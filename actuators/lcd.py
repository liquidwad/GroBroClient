from RPLCD.i2c import CharLCD
from cloud import *
from config import *

class CloudLCD(CloudActuator):
    def __init__(self, name, cloud, addr, defaultString = ""):
        CloudActuator.__init__(self, name, cloud, "lcd")
        self.lcd = CharLCD(address = addr, port = 1, cols = 16, rows = 2, dotsize = 8, charmap = 'A02')
        self.write(defaultString)
	
    def write(self, string):
        self.clear()
        self.lcd.write_string(string)
    
    def clear(self):
        self.lcd.clear()
        
    def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		if((data.value is not None) and (data.value is not self.state)):
		    self.state = data.value
		    self.write(data.value)
		    
class RelayLCD(CloudLCD):
    def __init__(self, name, cloud, addr, data = {}):
        CloudLCD.__init__(self, name, cloud, getDisplayString(data))
        self.reportAvailability(True, data)
        self.data = data
	
    def getDisplayString(data):
        # We have 16 chars per row times 2 rows
        # Each sub-string is max 7 chars
        w = 7
        return data.ul[0:w-1].center(w) + "  " + data.ur[0:w-1].center(w) + "  " + "\n" + data.ll[0:w-1].center(w) + "  " + data.lr[0:w - 1].center(w) 
       
    def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		if((data is not None) and (data is not self.data)):
		    self.data = data
		    self.write(getDisplayString(data))
