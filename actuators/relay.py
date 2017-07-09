from cloud import *
from config import *
import RPi.GPIO as GPIO

#Plug order
# 15 23 25 7
# 14 18 24 8

relay_gpio = [15,23,25,7,14,18,24,8]

class CloudRelay(CloudActuator):
    def __init__(self, name, cloud, relayNumber, initialState = False):
		CloudActuator.__init__(self, name, cloud)
		global relay_gpio
		self.relayNumber = relayNumber
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
		GPIO.setup(relay_gpio[relayNumber], GPIO.OUT)
		self.state = initialState
		self.reportAvailability(True)
		self.changeValue(initialState)
		   
    def changeValue(self, newValue):
        self.gpioState = GPIO.LOW if newValue else GPIO.HIGH
        GPIO.output(relay_gpio[self.relayNumber], self.state) 
        if(VERBOSE):
            print('%s was turned %s' % (self.name, 'on' if newValue else 'off'))
    
    def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		if((data.value is not None) and (data.value is not self.state)):
		    self.changeValue(data.value)
		    
		