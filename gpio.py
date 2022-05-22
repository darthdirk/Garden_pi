import time

class Gpio:
"""
doc string
"""


    def __init__(self, timeout:int, threshold:int):
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
