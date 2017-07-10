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
	def __init__(self, name, cloud, addr, relays, data = {}):
		self.ul = False
		self.ur = False
		self.ll = False
		self.lr = False
		CloudLCD.__init__(self, name, cloud, addr, self.getDisplayString(data))
		#subscribe to updates from the associated relays
		cloud.subscribe(self, relays[0])
		cloud.subscribe(self, relays[1])
		cloud.subscribe(self, relays[2])
		cloud.subscribe(self, relays[3])
		self.reportAvailability(True, data)
		self.data = data
		self.offChar = (
			0b11111, 
			0b10001, 
			0b10001, 
			0b10001, 
			0b10001, 
			0b10001, 
			0b10001, 
			0b11111)
		
		self.onChar = (
			0b11111, 
			0b11111, 
			0b11111, 
			0b11111, 
			0b11111, 
			0b11111, 
			0b11111, 
			0b11111)
			
		self.lcd.create_char(0, self.offChar)
		self.lcd.create_char(1, self.onChar)
	
	def getDisplayString(self,data):
		# We have 16 chars per row times 2 rows
		# Each sub-string is max 6 chars
		# The first char of each string holds the on/off status

		w = 6
		return (("\x01" if self.ul else "\x00") + data['ul'][0:w].center(w) + "  " +
		("\x01" if self.ur else "\x00") + data['ur'][0:w].center(w) + "\n\r" + 
		("\x01" if self.ll else "\x00") + data['ll'][0:w].center(w) + "  " + 
		("\x01" if self.lr else "\x00") + data['lr'][0:w].center(w)) 
	   
	def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		if data['channel_name'] == self.name:
			dat = data['data']
			if((dat is not None) and (dat is not self.data)):
				self.data = dat
				self.write(self.getDisplayString(dat))
		elif data['channel_name'] == "relay0":
			self.ul = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay1":
			self.ur = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay2":
			self.ul = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay3":
			self.ur = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay4":
			self.ll = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay5":
			self.lr = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay6":
			self.ll = data['data']['status']
			self.write(self.getDisplayString(self.data))
		elif data['channel_name'] == "relay7":
			self.lr = data['data']['status']
			self.write(self.getDisplayString(self.data))
