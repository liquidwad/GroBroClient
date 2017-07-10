from cloud import *
from config import *
import RPi.GPIO as GPIO

#Plug order
# 15 23 25 7
# 14 18 24 8

relay_gpio = [15,23,25,7,14,18,24,8]

class CloudRelay(CloudActuator):
    def __init__(self, name, cloud, relayNumber, pulled_data = {}):
		CloudActuator.__init__(self, name, cloud, "relay")
		global relay_gpio
		self.relayNumber = relayNumber
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
		GPIO.setup(relay_gpio[relayNumber], GPIO.OUT)
		
		initialValue = cloud.getValue(pulled_data, self.name)
		if initialValue is None:
			initialValue = False
			self.reportAvailability(True, {'status':initialValue})
		else:
			self.reportAvailability(True)
		
		self.state = initialValue
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
		
		state = data['data']['status']
		if((state is not None) and (state is not self.state)):
			self.state = state
			self.changeValue(state)
		    
		    
		