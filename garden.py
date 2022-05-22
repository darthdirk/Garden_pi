import logging
import time

#from ssl import CHANNEL_BINDING_TYPES
from typing_extensions import Self
import RPi.GPIO as GPIO

from gpio import Gpio_volt


log_format = '%(levelname)s | %(asctime)-15s | %(message)s'
logging.basicConfig(format=log_format, level=logging.DEBUG)


#Pin setup and Def
chan_list = [2,3,4,14,15,17,18,27,22,23,24]
GPIO.setup(2,GPIO.OUT)
GPIO.setup(3, GPIO.OUT)
GPIO.setup(4,GPIO.OUT)
GPIO.setup(14,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(18,GPIO.OUT)
GPIO.setup(27,GPIO.IN)
GPIO.setup(22,GPIO.IN)
GPIO.setup(23,GPIO.IN)
GPIO.setup(24,GPIO.IN)

# Initial state of output pins
GPIO.output(2,GPIO.LOW)
GPIO.output(3,GPIO.LOW)
GPIO.output(4,GPIO.LOW)
GPIO.output(14,GPIO.LOW)
GPIO.output(15,GPIO.LOW)
GPIO.output(17,GPIO.LOW)
GPIO.output(18,GPIO.LOW)


#GPIO.add_event_detect(GPIO.BOTH, bouncetime=300)  # let us know when the pin goes HIGH or LOW
#GPIO.add_event_callback(CHANNEL_BINDING_TYPES, callback)  # assign function to GPIO PIN, Run function on change
 
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
          
 
