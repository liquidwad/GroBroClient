from cloud import *
from config import *
import RPi.GPIO as GPIO

#Plug order
# 14 18 24 8
# 15 23 25 7

relay_gpio = [16,18,24,8,20,23,25,7]

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
		self.changeValue(initialValue)
		   
    def changeValue(self, newValue):
		if( newValue == "False" or newValue == "false" or newValue == "Off" or newValue == 0):
			self.gpioState =  GPIO.HIGH
		elif( newValue == "True" or newValue == "true" or newValue == "On" or newValue == 1):
			self.gpioState =  GPIO.LOW
		GPIO.output(relay_gpio[self.relayNumber], self.gpioState) 
		if(VERBOSE):
			print('%s was set to %s' % (self.name, newValue))
    
    def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		state = data['data']['status']
		if((state is not None) and (state is not self.state)):
			self.state = state
			self.changeValue(state)
		    
		    
		