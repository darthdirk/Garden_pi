import time
import RPi.GPIO as GPIO


class Gpio:
    """
    doc string
    """


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


def __init__(self, timeout: int, threshold: int):
    """
    GPIO initialization
    :param timeout:
    :param threshold:
    """
    self.threshold: int = threshold
    self.timeout: int = timeout
    self.voltage: int = 0
    self.voltage_is_high: bool = False


def update_voltage(self, voltage: int):
    """
    doc string
    """
    self.voltage = voltage
    self.__check_voltage()


@staticmethod
def __check_voltage(self):
    """
    doc string
    """
    if self.voltage >= self.threshold:
        self.voltage_is_high = True
        self.__set_timeout()
        self.__check_voltage()
    else:
        self.voltage_is_high = False


@staticmethod
def __set_timeout(self):
    """
    doc string
    """
    time.sleep(self.timeout * 1000 + 100)
