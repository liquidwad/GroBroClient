from api import *
from config import *
import threading
import time
import smbus

bus = smbus.SMBus(1)

class CloudManager:
	def __init__(self, host, key):
		self.key = key
		self.cloud_api = GroBroAPI(host)
		self.cloud_api.register_callback('connect', self.on_connected)
		self.cloud_api.register_callback('disconnect', self.on_disconnected)
		self.cloud_api.register_callback('reconnect', self.on_reconnected)
		self.cloud_api.register_callback('update', self.on_update)
		self.cloud_api.register_callback('pull', self.on_pull)
		self.connected = False
		self.subscribers = {}
		self.pulled_data = None
		self.data_pulled = False
		self.notifyOnPull = True
		self.i2c_lock = threading.Lock()

	def wait(self, sec):
		self.cloud_api.wait(sec)

	def connect(self):
		print "Connecting"
		self.cloud_api.connect()

	def pull_updates(self, notify = True):
		self.notifyOnPull = notify
		self.cloud_api.pull()

	def subscribe(self, subscriber, channel):
		try:
			self.subscribers[channel].append(subscriber)
		except KeyError, e:
			self.subscribers[channel] = []
			self.subscribers[channel].append(subscriber)
		if VERBOSE:
			print subscriber.name + " subscribed to channel " + channel

	def publish(self, data, publisher = None):
		#First notify all subscribers of this change, since server does not reflect published values back to us
		self.notifySubscribers(data, publisher)
		
		# If cloud is available, push the data to it
		while self.connected is False:
			self.wait(0.1)
		self.cloud_api.push(data)
		
	def notifySubscribers(self, data, publisher = None):
		dat = data
		if not 'data' in data:
			dat = None
			cache = Cache.get_cache()
			if data['channel_name'] in cache:
				dat = cache[data['channel_name']]
		
		subscribers = {}
		if (dat is not None) and (dat['channel_name'] in self.subscribers):
			subscribers = self.subscribers[dat['channel_name']]
		for subscriber in subscribers:
			if((publisher is None) or (subscriber is not publisher)):
				subscriber.on_update(dat)

	def on_connected(self):
		print "Connected"
		self.cloud_api.register_device(self.key)
		self.connected = True

	def on_disconnected(self):
		print "Disconnected"
		self.connected = False

	def on_reconnected(self):
		print "Reconnected"
		self.cloud_api.register_device(self.key)
		self.connected = True
				
	def on_update(self, data):
		if VERBOSE:
			print "Got update:"
			print data
			
		self.notifySubscribers(data)

	def getSubscribers(self, channel):
		string = ""
		try:
			subscribers = self.subscribers[channel]
			for subscriber in subscribers:
				string = string + subscriber.name + ","
		except Exception, e:
			pass
		
		return string
		
	def on_pull(self, data):
		if VERBOSE:
			print "Pulled: ", data
			
		if(self.notifyOnPull):
			for chan in data:
				self.on_update(chan)
			
		self.pulled_data = data
		self.data_pulled = True
		
	
	def reset_pull_data(self):
		self.pulled_data = None
		self.data_pulled = False
		
	# TODO: optimize search
	def getValue(self, data, channel):
		if data is None:
			return None
			
		for chan in data:
			if chan['channel_name'] == channel:
				state = chan['data']['status']
				if state is not None:
					return state
				else:
					return None
		return None
		
	def getData(self, pulled_data, channel):
		if pulled_data is None:
			return None
		
		for chan in pulled_data:
			if chan['channel_name'] == channel:
				data = chan['data']
				return data
			
		return None
		


class CloudDevice:
	def __init__(self, name, cloud, channel_type = "device", channel_subtype = "undefined"):
		self.name = name
		self.cloud = cloud
		self.channel_type = channel_type
		self.channel_subtype = channel_subtype
		
	def reportAvailability(self, available, data = None):
		self.available = available
		if data is None:
			self.cloud.publish({
				'channel_name': self.name, 
				'channel_type': self.channel_type, 
				'channel_subtype': self.channel_subtype, 
				'available': self.available
			}, self)
		else:
			self.cloud.publish({
			'channel_name': self.name, 
			'channel_type': self.channel_type, 
			'channel_subtype': self.channel_subtype, 
			'available': self.available,
			'data': data
		}, self)
			

		if(VERBOSE and available):
			print self.name + " " + self.channel_type + " " + self.channel_subtype + " was initialized"
	
	def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data

class CloudActuator(CloudDevice):
	def __init__(self, name, cloud, channel_subtype = "undefined"):
		CloudDevice.__init__(self, name, cloud, "actuator", channel_subtype)
		cloud.subscribe(self, name)
	
	def changeValue(self, newValue):
		pass


class CloudSensor(CloudDevice):
	def __init__(self, name, cloud, measureInterval, range_min, range_max, channel_subtype = "undefined"):
		CloudDevice.__init__(self, name, cloud, "sensor", channel_subtype)
		self.thread = threading.Thread(target = self.measureThread)
		self.stopped = True
		self.measureInterval = measureInterval
		self.device = None
		self.range_min = range_min
		self.range_max = range_max
		self.checkAndReportDevice()

	def reportAvailability(self, available, data = None):
		self.available = available
		if data is None:
			self.cloud.publish({
				'channel_name': self.name, 
				'channel_type': self.channel_type, 
				'channel_subtype': self.channel_subtype, 
				'available': self.available,
				'range': {'min': self.range_min, 'max': self.range_max }
			}, self)
		else:
			self.cloud.publish({
				'channel_name': self.name, 
				'channel_type': self.channel_type, 
				'channel_subtype': self.channel_subtype, 
				'available': self.available,
				'range': {'min': self.range_min, 'max': self.range_max },
				'data': data
			}, self)
			

		if(VERBOSE and available):
			print self.name + " sensor was initialized"
			
	def checkAndReportDevice(self):
		pass
	
	def initDevice(self):
		pass
	
	def detect(self):
		global bus
		try:
			bus.read_byte(self.address)
			return True
		except:
			return False
			
	def checkAndReportDevice(self):
		detected = self.detect()
		if (detected is False) and (self.device is not None):
			if VERBOSE:
				print self.name + " sensor device disconnected"
			self.device = None
			self.reportAvailability(False)
		elif (detected is True) and (self.device is None):
			if VERBOSE:
				print self.name + "sensor connected"
			self.initDevice()
			
	def measureThread(self):
		while self.stopped is False:
			startTime = time.time()
			self.checkAndReportDevice()
			if(self.device is not None):
				value = self.measure()
				self.cloud.publish( {'channel_name': self.name, 'data': { 'status': value } } )
				if(VERBOSE):
					print('%s: %d' % (self.name, value))
					
			deltaTime = time.time() - startTime
			remainingTime = self.measureInterval - deltaTime
			if(remainingTime > 0):
				time.sleep(remainingTime)

	def measure(self):
		return none

	def start(self):
		self.stopped = False
		self.thread.start()
		if VERBOSE:
			print "Started measurement thread for " + self.name

	def stop(self):
		self.stopped = True
		if VERBOSE:
			print "Stopped measurement thread for " + self.name
