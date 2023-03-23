import datetime
import logging
import threading


import gpi.Gardenpi.db_store as db_store

logger = logging.getLogger(__name__)

_SECONDS_PER_MINUTE = 60
# Number of seconds to idle between checks for whether a poller needs to poll or
# a poller needs to stop (note that this is NOT the total time a poller sleeps
# between polls).
_IDLE_SECONDS = 0.5

class piDataBus(object):
"""
Databus objects
"""
    def __init__(self, schedule_function, record_buff):
        """
        creates a new Sensor databus instance
        :param self:
        :param Schedule_Function: databus waiting function
        :param record_buff: buffer for data records
        :return:
        """
        self._schedule_function = schedule_function
        self._record_buff = record_buff

    def inc_temperature_databus(self, temperature_sensor):
        return _sensorData(
            _tempatureData(self._schedule_function(),
                           self.record_buff, temperature_sensor))


    def inc_humidity_databus(self, humidity_sensor):
        return _sensorData(
            _humidityData(self._schedule_function(),
                           self.record_buff, humidity_sensor))
    def soil_water_databus():
        pass
    def camera_databus():
        pass
