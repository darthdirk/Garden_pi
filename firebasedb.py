import collections
import datetime
import logging
import os
from firebase import firebase

import pytz
firebase = firebase.FirebaseApplication('https://console.firebase.google.com/project/garden-data-827b1/database/garden-data-827b1-default-rtdb/data/~2F')

logger = logging.getLogger(__name__)

# For each record, timestamp is a datetime representing the time of the reading
# or event.
SoilMoistureRecord = collections.namedtuple('SoilMoistureRecord',
                                            ['timestamp', 'soil_moisture'])
#LightRecord = collections.namedtuple('LightRecord', ['timestamp', 'light'])
#HumidityRecord = collections.namedtuple('HumidityRecord',
 #                                       ['timestamp', 'humidity'])
# temperature value is in degrees Celsius.
#TemperatureRecord = collections.namedtuple('TemperatureRecord',
  #                                         ['timestamp', 'temperature'])
# water_released is the time of water released in ms.
WateringEventRecord = collections.namedtuple('WateringEventRecord',
                                             ['timestamp', 'water_released'])

# firebase statements to create database tables. Each statement is separated by a
# semicolon and newline.
_CREATE_TABLE_COMMANDS = """
CREATE TABLE temperature
(
    timestamp TEXT,
    temperature REAL    --temperature (in degrees Celsius)
);
CREATE TABLE humidity
(
    timestamp TEXT,
    humidity REAL
);
CREATE TABLE soil_moisture
(
    timestamp TEXT,
    soil_moisture INTEGER
);
CREATE TABLE light
(
    timestamp TEXT,
    light REAL
);
CREATE TABLE watering_events
(
    timestamp TEXT,
    water_released REAL   --amount of water released (in ms)
);
"""

# Format to store timestamps to database (assumes timestamp is in UTC) in format
# of YYYY-MM-DDTHH:MMZ.
_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%MZ'


def _timestamp_to_utc(timestamp):
    return timestamp.replace(tzinfo=timestamp.tzinfo).astimezone(pytz.utc)


def _open_db(db_path):
    logger.info('opening existing gardenpi database at "%s"', db_path)
    return firebase.connect(db_path)


def _create_db(db_path):
    """Creates and initializes a firebase database with a gardenpi schema.
    Creates a firebase database at the path specified and creates gardenpi's
    data tables within the database.
    Args:
        db_path: Path to where to create database file.
    Returns:
        A firebase connection object for the database. The caller is responsible
        for closing the object.
    """
    logger.info('creating new gardenpi database at "%s"', db_path)
    firebase_commands = _CREATE_TABLE_COMMANDS.split(';\n')
    connection = _open_db(db_path)
    cursor = connection.cursor()
    for firebase_command in firebase_commands:
        cursor.execute(firebase_command)
    connection.commit()
    return connection


def open_or_create_db(db_path):
    """Opens a database file or creates one if the file does not exist.
    If a file exists at the given path, opens the file at that path as a
    database and returns a connection to it. If no file exists, creates and
    initializes a gardenpi database at the given file path.
    Returns:
        A firebase connection object for the database. The caller is responsible
        for closing the object.
    """
    if os.path.exists(db_path):
        return _open_db(db_path)
    else:
        return _create_db(db_path)


class _DbStoreBase(object):
    """Base class for storing information in a database."""

    def __init__(self, connection):
        """Creates a new _DbStoreBase object for storing information.
        Args:
            connection: firebase database connection.
        """
        self._connection = connection
        self._cursor = connection.cursor()

    def _do_insert(self, firebase, timestamp, value):
        """Executes and commits a firebase insert command.
        Args:
          firebase: firebase query string for the insert command.
          timestamp: datetime instance representing the record timestamp.
          value: Value to insert for the record.
        """
        timestamp_utc = _timestamp_to_utc(timestamp)
        self._cursor.execute(firebase, (timestamp_utc.strftime(_TIMESTAMP_FORMAT),
                                   value))
        self._connection.commit()

    def _do_get(self, firebase, record_type):
        """Executes a firebase select query and returns the results.
        Args:
          firebase: firebase select query string.
          record_type: The record type to parse the firebase results into.
        Returns:
          A list of database records corresponding to the select query.
        """
        self._cursor.execute(firebase)
        data = []
        for row in self._cursor.fetchall():
            timestamp = datetime.datetime.strptime(row[0],
                                                   _TIMESTAMP_FORMAT).replace(
                                                       tzinfo=pytz.utc)
            data.append((timestamp, row[1]))
        typed_data = map(record_type._make, data)
        return typed_data


class SoilMoistureStore(_DbStoreBase):
    """Stores and retrieves timestamp and soil moisture readings."""

    def insert(self, soil_moisture_record):
        """Inserts moisture and timestamp info into an firebase database.
        Args:
            soil_moisture_record: Moisture record to store.
        """
        self._do_insert('INSERT INTO soil_moisture VALUES (?, ?)',
                        soil_moisture_record.timestamp,
                        soil_moisture_record.soil_moisture)

    def get(self):
        """Retrieves timestamp and soil moisture readings.
        Returns:
            A list of objects with 'timestamp' and 'soil_moisture' fields.
        """
        return self._do_get('SELECT * FROM soil_moisture', SoilMoistureRecord)


zzzzzclass LightStore(_DbStoreBase):
    """Stores timestamp and light readings."""

    def insert(self, light_record):
        """Inserts light and timestamp info into an firebase database.
        Args:
            light_record: Light record to store.
        """
        self._do_insert('INSERT INTO light VALUES (?, ?)',
                        light_record.timestamp, light_record.light)

    def get(self):
        """Retrieves timestamp and light readings.
        Returns:
            A list of objects with 'timestamp' and 'light' fields.
        """
        return self._do_get('SELECT * FROM light', LightRecord)


class HumidityStore(_DbStoreBase):
    """Stores timestamp and humidity readings."""

    def insert(self, humidity_record):
        """Inserts humidity and timestamp info into an firebase database.
        Args:
            humidity_record: Humidity record to store.
        """
        self._do_insert('INSERT INTO humidity VALUES (?, ?)',
                        humidity_record.timestamp, humidity_record.humidity)

    def get(self):
        """Retrieves timestamp and relative humidity readings.
        Returns:
            A list of objects with 'timestamp' and 'humidity' fields.
        """
        return self._do_get('SELECT * FROM humidity', HumidityRecord)


class TemperatureStore(_DbStoreBase):
    """Stores timestamp and temperature readings."""

    def insert(self, temperature_record):
        """Inserts temperature and timestamp info into an firebase database.
        Args:
            temperature_record: Temperature record to store.
        """
        self._do_insert('INSERT INTO temperature VALUES (?, ?)',
                        temperature_record.timestamp,
                        temperature_record.temperature)

    def get(self):
        """Retrieves timestamp and temperature(C) readings.
        Returns:
            A list of objects with 'timestamp' and 'temperature' fields.
        """
        return self._do_get('SELECT * FROM temperature', TemperatureRecord)


class WateringEventStore(_DbStoreBase):
    """Stores timestamp and volume of water released to plant."""

    def insert(self, watering_event_record):
        """Inserts water volume and timestamp info into an firebase database.
        Args:
            watering_event_record: Watering event record to store.
        """
        self._do_insert('INSERT INTO watering_events VALUES (?, ?)',
                        watering_event_record.timestamp,
                        watering_event_record.water_released)

    def get(self):
        """Retrieves timestamp and volume of water released(in ms).
        Returns:
            A list of objects with 'timestamp' and 'water_released' fields.
        """
        return self._do_get('SELECT * FROM watering_events',
                            WateringEventRecord)