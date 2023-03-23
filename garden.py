import argparce
import clock
import datetime
import logging
import time

# from ssl import CHANNEL_BINDING_TYPES
from typing_extensions import self

import RPi.GPIO as GPIO
import os
from time import sleep
from firebase import firebase
from gpio import Gpio
import solenoid
import solenoid_history
import sleep_windows
import soil_moisture_sensor

firebase = firebase.FirebaseApplication(
    'https://console.firebase.google.com/project/garden-data-827b1/database/garden-data-827b1-default-rtdb/data/~2F')

logger = logging.getLogger(__name__)


def configure_logging(verbose):
    """Configure the root logger for log output."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-15s %(levelname)-4s %(message)s',
        '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    if verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)


# Pin setup and Def
chan_list = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24]
GPIO.setup(2, GPIO.OUT)
GPIO.setup(3, GPIO.OUT)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(14, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(27, GPIO.IN)
GPIO.setup(22, GPIO.IN)
GPIO.setup(23, GPIO.IN)
GPIO.setup(24, GPIO.IN)

# Initial state of output pins
GPIO.output(2, GPIO.LOW)
GPIO.output(3, GPIO.LOW)
GPIO.output(4, GPIO.LOW)
GPIO.output(14, GPIO.LOW)
GPIO.output(15, GPIO.LOW)
GPIO.output(17, GPIO.LOW)
GPIO.output(18, GPIO.LOW)


def measure_temperature():
    temperature = os.popen("vcgencmd measure_temp").readline()  # Retrieves temperature of the raspberry pi motherboard 
    return (temperature.replace("temp=", ""))


def make_soil_moisture_sensor(adc, raspberry_pi_io, wiring_config):
    return soil_moisture_sensor.SoilMoistureSensor(
        adc, raspberry_pi_io, wiring_config.adc_channels.soil_moisture_sensor,
        wiring_config.gpio_pins.soil_moisture)


def make_solenoid_manager(moisture_threshold, sleep_windows, raspberry_pi_io,
                          wiring_config, solenoid_amount, db_connection, solenoid_interval):
    """Creates a solenoid manager instance.
    Args:
        moisture_threshold: The minimum moisture level below which the solenoid
            turns on.
        sleep_windows: Sleep windows during which solenoid will not turn on.
        raspberry_pi_io: pi_io instance for the gardenpi.
        wiring_config: Wiring configuration for the gardenpi.
        solenoid_amount: Amount (in mL) to solenoid on each run of the solenoid.
        db_connection: Database connection to use to retrieve solenoid history.
        solenoid_interval: Maximum amount of time between solenoid runs.
    Returns:
        A solenoidManager instance with the given settings.
    """
    water_solenoid = solenoid.solenoid(raspberry_pi_io,
                                       clock.Clock(), wiring_config.gpio_pins.solenoid)
    solenoid_scheduler = solenoid.solenoidScheduler(clock.LocalClock(), sleep_windows)
    solenoid_timer = clock.Timer(clock.Clock(), solenoid_interval)
    last_solenoid_time = solenoid_history.last_solenoid_time(
        db_store.WateringEventStore(db_connection))
    if last_solenoid_time:
        logger.info('last watering was at %s', last_solenoid_time)
        time_remaining = max(
            datetime.timedelta(seconds=0),
            (last_solenoid_time + solenoid_interval) - clock.Clock().now())
    else:
        logger.info('no previous watering found')
        time_remaining = datetime.timedelta(seconds=0)
    logger.info('time until until next watering: %s', time_remaining)
    solenoid_timer.set_remaining(time_remaining)
    return solenoid.solenoidManager(water_solenoid, solenoid_scheduler, moisture_threshold,
                                    solenoid_amount, solenoid_timer)


def make_sensor_databus(databus_interval, photo_interval, record_queue,
                        temperature_sensor, humidity_sensor,
                        soil_moisture_sensor, light_sensor, camera_manager,
                        solenoid_manager):
    """Creates a databus for each gardenpi sensor.
    Args:
        databus_interval: The frequency at which to databus non-camera sensors.
        photo_interval: The frequency at which to capture photos.
        record_queue: Queue on which to put sensor reading records.
        temperature_sensor: Sensor for measuring temperature.
        humidity_sensor: Sensor for measuring humidity.
        soil_moisture_sensor: Sensor for measuring soil moisture.
        light_sensor: Sensor for measuring light levels.
        camera_manager: Interface for capturing photos.
        solenoid_manager: Interface for turning water solenoid on and off.
    Returns:
        A list of sensor databus.
    """
    logger.info('creating sensor databus (databus interval=%ds")',
                databus_interval.total_seconds())
    utc_clock = clock.Clock()

    make_scheduler_func = lambda: databus.Scheduler(utc_clock, databus_interval)
    photo_make_scheduler_func = lambda: databus.Scheduler(utc_clock, photo_interval)
    databus_factory = databus.SensordatabusFactory(make_scheduler_func,
                                                record_queue)
    camera_databus_factory = databus.SensordatabusFactory(
        photo_make_scheduler_func, record_queue=None)

    return [
        databus_factory.create_temperature_databus(temperature_sensor),
        databus_factory.create_humidity_databus(humidity_sensor),
        databus_factory.create_soil_watering_databus(
            soil_moisture_sensor,
            solenoid_manager),
        databus_factory.create_light_databus(light_sensor),
        camera_databus_factory.create_camera_databus(camera_manager)
    ]  # yapf: disable


def create_record_processor(db_connection, record_queue):
    """Creates a record processor for storing records in a database.
    Args:
        db_connection: Database connection to use to store records.
        record_queue: Record queue from which to process records.
    """
    return record_processor.RecordProcessor(
        record_queue,
        db_store.SoilMoistureStore(db_connection),
        db_store.LightStore(db_connection),
        db_store.HumidityStore(db_connection),
        db_store.TemperatureStore(db_connection),
        db_store.WateringEventStore(db_connection))


def main(args):
    configure_logging(args.verbose)
    logger.info('starting gardenpi')
    wiring_config = read_wiring_config(args.config_file)
    record_queue = Queue.Queue()
    raspberry_pi_io = pi_io.IO(GPIO)
    adc = make_adc(wiring_config)
    local_soil_moisture_sensor = make_soil_moisture_sensor(
        adc, raspberry_pi_io, wiring_config)
    local_temperature_sensor, local_humidity_sensor = make_dht11_sensors(
        wiring_config)
    local_light_sensor = make_light_sensor(adc, wiring_config)
    camera_manager = make_camera_manager(args.camera_rotation, args.image_path,
                                         local_light_sensor)

    with contextlib.closing(
            db_store.open_or_create_db(args.db_file)) as db_connection:
        record_processor = create_record_processor(db_connection, record_queue)
        solenoid_manager = make_solenoid_manager(
            args.moisture_threshold,
            sleep_windows.parse(args.sleep_window),
            raspberry_pi_io,
            wiring_config,
            args.solenoid_amount,
            db_connection,
            datetime.timedelta(hours=args.solenoid_interval))
        databus = make_sensor_databus(
            datetime.timedelta(minutes=args.databus_interval),
            datetime.timedelta(minutes=args.photo_interval),
            record_queue,
            local_temperature_sensor,
            local_humidity_sensor,
            local_soil_moisture_sensor,
            local_light_sensor,
            camera_manager,
            solenoid_manager)
        try:
            for current_databus in databus:
                current_databus.start_databusing_async()
            while True:
                if not record_processor.try_process_next_record():
                    time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info('Caught keyboard interrupt. Exiting.')
        finally:
            for current_databus in databus:
                current_databus.close()
            raspberry_pi_io.close()


# infinite loop
while True:
    if GPIO.input(27, GPIO.HIGH):
        GPIO.output(2, GPIO.HIGH)
        time.sleep(.50)
    elif GPIO.input(22, GPIO.HIGH):
        GPIO.output(3, GPIO.HIGH)
        time.sleep(.50)
    elif GPIO.input(23, GPIO.HIGH):
        GPIO.output(4, GPIO.HIGH)
        time.sleep(.50)
    elif GPIO.input(24, GPIO.HIGH):
        GPIO.output(14, GPIO.HIGH)
        time.sleep(.50)
    else:
        GPIO.output(2, GPIO.LOW)
        GPIO.output(3, GPIO.LOW)
        GPIO.output(4, GPIO.LOW)
        GPIO.output(14, GPIO.LOW)
        GPIO.cleanup

#  firebase.post("/raspberry-pi-2/health-monitor/cpu-temp", cpuTp)
#  firebase.post("/raspberry-pi-2/sensors/ultrasonic", distance)
#  firebase.post("/raspberry-pi-2/health-monitor/cpu-core0-usage", cpuCore[0])
# firebase.post("/raspberry-pi-2/health-monitor/cpu-core1-usage", cpuCore[1])
# firebase.post("/raspberry-pi-2/health-monitor/cpu-core2-usage", cpuCore[2])
# firebase.post("/raspberry-pi-2/health-monitor/cpu-core3-usage", cpuCore[3])         

# GPIO.add_event_detect(GPIO.BOTH, bouncetime=300)  # let us know when the pin goes HIGH or LOW
# GPIO.add_event_callback(CHANNEL_BINDING_TYPES, callback)  # assign function to GPIO PIN, Run function on change

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='gardenpi',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-t',
        '--photo_interval',
        type=float,
        help='Number of minutes between each camera photo',
        default=(4 * 60))
    parser.add_argument(
        '-w',
        '--solenoid_interval',
        type=float,
        help='Max number of hours between plant waterings',
        default=(7 * 24))
    parser.add_argument(
        '-c',
        '--config_file',
        help='Wiring config file',
        default='gardenpi/wiring_config.ini')
    parser.add_argument(
        '-s',
        '--sleep_window',
        action='append',
        type=str,
        default=[],
        help=('Time window during which gardenpi will not activate its '
              'solenoid. Window should be in the form of a time range in 24-hour '
              'format, such as "03:15-03:45 (in the local time zone)"'))
    parser.add_argument(
        '-i',
        '--image_path',
        type=str,
        help='Path to folder where images will be stored',
        default='images/')
    parser.add_argument(
        '-d',
        '--db_file',
        help='Location to store gardenpi database file',
        default='gardenpi/gardenpi.db')
    parser.add_argument(
        '-m',
        '--moisture_threshold',
        type=int,
        help=('Moisture threshold to start solenoid. The solenoid will turn on if the '
              'moisture level drops below this level'),
        default=0)
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Use verbose logging')
    main(parser.parse_args())