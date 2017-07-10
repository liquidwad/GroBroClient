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
	def __init__(self, name, cloud, addr, relays, pulled_data = {}):
		CloudLCD.__init__(self, name, cloud, addr)
		#subscribe to updates from the associated relays
		cloud.subscribe(self, relays[0])
		cloud.subscribe(self, relays[1])
		cloud.subscribe(self, relays[2])
		cloud.subscribe(self, relays[3])
		data = cloud.getData(pulled_data, self.name)
		if data is None:
			data = {'ul': relays[0], 'ur':relays[1], 'll':relays[2], 'lr':relays[3]}
			self.reportAvailability(True, data)
		else:
			self.reportAvailability(True)
			
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
			0b00000, 
			0b00000, 
			0b00000, 
			0b00000, 
			0b00000, 
			0b00000, 
			0b00000, 
			0b00000)
			
		self.positions = {}
		self.positions['ul'] = (0,0)
		self.positions['ur'] = (0,9)
		self.positions['ll'] = (1,0)
		self.positions['lr'] = (1,9)
	
		self.data = {'ul':'', 'ur':'', 'll':'', 'lr':''}
		self.updateDisplay(data)
		self.data = data
		
	def updateDisplay(self,data):
		# We have 16 chars per row times 2 rows
		# Each sub-string is max 6 chars
		# The first char of each string holds the on/off status
		self.updateLabel(data, 'ul')
		self.updateLabel(data, 'ur')
		self.updateLabel(data, 'll')
		self.updateLabel(data, 'lr')
	
	def updateLabel(self, data, tag):
		w = 6
		if( data[tag] != self.data[tag]):
			self.lcd.cursor_pos = self.positions[tag]
			if( len(data[tag]) < len(self.data[tag])):
				self.lcd.write_string("      ");
				self.lcd.cursor_pos = self.positions[tag]
			self.lcd.write_string(" " + data[tag][0:w].center(w))
		
	   
	def setRelayStatus(self, relay, status):
		if (relay is 0) or (relay is 2):
			self.lcd.cursor_pos = (0,0)
		elif (relay is 1) or (relay is 3):
			self.lcd.cursor_pos = (0,9)
		if (relay is 4) or (relay is 6):
			self.lcd.cursor_pos = (1,0)
		elif (relay is 5) or (relay is 7):
			self.lcd.cursor_pos = (1,9)
		
		self.lcd.write_string('|' if status else '_')
		#self.lcd.create_char(0, self.onChar if status else self.offChar)
		#self.lcd.write_string('\x00')
		
	def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		
		if data['channel_name'] == self.name:
			dat = data['data']
			if((dat is not None) and (dat is not self.data)):
				self.updateDisplay(dat)
				self.data = dat
		elif data['channel_name'] == "relay0":
			self.setRelayStatus(0, data['data']['status'])
		elif data['channel_name'] == "relay1":
			self.setRelayStatus(1, data['data']['status'])
		elif data['channel_name'] == "relay2":
			self.setRelayStatus(2, data['data']['status'])
		elif data['channel_name'] == "relay3":
			self.setRelayStatus(3, data['data']['status'])
		elif data['channel_name'] == "relay4":
			self.setRelayStatus(4, data['data']['status'])
		elif data['channel_name'] == "relay5":
			self.setRelayStatus(5, data['data']['status'])
		elif data['channel_name'] == "relay6":
			self.setRelayStatus(6, data['data']['status'])
		elif data['channel_name'] == "relay7":
			self.setRelayStatus(7, data['data']['status'])

class LeftRelayLCD(RelayLCD):
	def __init__(self, name, cloud, data = {}):
		RelayLCD.__init__(self, name, cloud, addr = LCD_LEFT_ADDR, relays = ["relay0", "relay1", "relay4", "relay5"], data = data)
		
class RightRelayLCD(RelayLCD):
	def __init__(self, name, cloud, data = {}):
		RelayLCD.__init__(self, name, cloud, addr = LCD_RIGHT_ADDR, relays = ["relay2", "relay3", "relay6", "relay7"], data = data)