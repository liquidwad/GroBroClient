from RPLCD.i2c import CharLCD
from cloud import *
from config import *
import threading
import Queue
import time

class CloudLCD(CloudActuator):
	def __init__(self, name, cloud, addr, defaultString = ""):
		CloudActuator.__init__(self, name, cloud, "lcd")
		with self.cloud.i2c_lock:
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
			with self.cloud.i2c_lock:
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
		self.positions['ul'] = (0,1)
		self.positions['ur'] = (0,10)
		self.positions['ll'] = (1,1)
		self.positions['lr'] = (1,10)
	
		self.q = Queue.Queue()
		self.t = threading.Thread(target = self.workerThread)
		self.t.daemon = True
		self.t.start()
		self.data = {'ul':'', 'ur':'', 'll':'', 'lr':''}
		self.updateDisplay(data)
		self.data = data
		
	def updateDisplay(self,data):
		# We have 16 chars per row times 2 rows
		# Each sub-string is max 6 chars
		# The first char of each string holds the on/off status
		tags = [ 'ul', 'ur', 'll', 'lr']
		for tag in tags:
			if( data[tag] != self.data[tag]):
				self.q.put({'method':"updateLabel", 'data':data, 'tag':tag})
	
	def updateLabel(self, data, tag):
		w = 6
		with self.cloud.i2c_lock:
			self.setCursorPos(self.positions[tag])
			if( len(data[tag]) < len(self.data[tag])):
				self.writeToLCD("      ");
				self.setCursorPos(self.positions[tag])
			self.writeToLCD(data[tag][0:w].center(w))
	   
	def setRelayStatus(self, relay, status):
		with self.cloud.i2c_lock:
			if (relay is 0) or (relay is 2):
				self.setCursorPos((0,0))
			elif (relay is 1) or (relay is 3):
				self.setCursorPos((0,9))
			if (relay is 4) or (relay is 6):
				self.setCursorPos((1,0))
			elif (relay is 5) or (relay is 7):
				self.setCursorPos((1,9))
			
			self.writeToLCD('|' if status else '_')
	
	def setCursorPos(self, pos):
		while True:
			try:
				self.lcd.cursor_pos = pos
				break
			except:
				time.sleep(0.1)

	def writeToLCD(self, s):
		while True:
			try:
				self.lcd.write_string(s)
				break
			except:
				time.sleep(0.1)
	
	def workerThread(self):
		while True:
			item = self.q.get()
			if(item['method'] == "updateLabel"):
				self.updateLabel(item['data'], item['tag'])
			elif(item['method'] == "setRelayStatus"):
				self.setRelayStatus(item['relay'], item['status'])
			self.q.task_done()
		
	def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data
		if( 'data' in data):
			if data['channel_name'] == self.name:
				dat = data['data']
				if((dat is not None) and (dat is not self.data)):
					self.updateDisplay(dat)
					self.data = dat
			elif data['channel_name'] == "relay0":
				self.q.put({'method':"setRelayStatus", 'relay': 0, 'status': data['data']['status']})
			elif data['channel_name'] == "relay1":
				self.q.put({'method':"setRelayStatus", 'relay': 1, 'status': data['data']['status']})
			elif data['channel_name'] == "relay2":
				self.q.put({'method':"setRelayStatus", 'relay': 2, 'status': data['data']['status']})
			elif data['channel_name'] == "relay3":
				self.q.put({'method':"setRelayStatus", 'relay': 3, 'status': data['data']['status']})
			elif data['channel_name'] == "relay4":
				self.q.put({'method':"setRelayStatus", 'relay': 4, 'status': data['data']['status']})
			elif data['channel_name'] == "relay5":
				self.q.put({'method':"setRelayStatus", 'relay': 5, 'status': data['data']['status']})
			elif data['channel_name'] == "relay6":
				self.q.put({'method':"setRelayStatus", 'relay': 6, 'status': data['data']['status']})
			elif data['channel_name'] == "relay7":
				self.q.put({'method':"setRelayStatus", 'relay': 7, 'status': data['data']['status']})

class LeftRelayLCD(RelayLCD):
	def __init__(self, name, cloud, data = {}):
		RelayLCD.__init__(self, name, cloud, addr = LCD_LEFT_ADDR, relays = ["relay0", "relay1", "relay4", "relay5"], pulled_data = data)
		
class RightRelayLCD(RelayLCD):
	def __init__(self, name, cloud, data = {}):
		RelayLCD.__init__(self, name, cloud, addr = LCD_RIGHT_ADDR, relays = ["relay2", "relay3", "relay6", "relay7"], pulled_data = data)