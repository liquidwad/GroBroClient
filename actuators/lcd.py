from RPLCD.i2c import CharLCD
from cloud import *
from config import *

class CloudLCD(CloudActuator):
    def __init__(self, name, cloud, addr, defaultString = ""):
        CloudActuator.__init__(self, name, cloud)
        self.lcd = CharLCD(address = addr, port = 1, cols = 16, rows = 2, dotsize = 8, charmap = 'A02')
        self.write(defaultString)
        self.reportAvailability(True)
	
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
		    self.write(data.value)
		    
if __name__ == "__main__":
    testLCD = CharLCD(address = LCD_LEFT_ADDR, port = 1, cols = 16, rows = 2, dotsize = 8, charmap = 'A02')
    testLCD.write_string("Test")