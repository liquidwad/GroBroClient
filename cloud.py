from api import *
from config import *
import threading
import time

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
		if not hasattr(data, 'data'):
			dat = Cache.get_cache()[data['channel_name']]
		
		subscribers = {}
		if hasattr(self.subscribers, data['channel_name']):
			subscribers = self.subscribers[data['channel_name']]
		for subscriber in subscribers:
			if((publisher is None) or (subscriber is not publisher)):
				subscriber.on_update(data)

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
	def __init__(self, name, cloud, measureInterval, channel_subtype = "undefined"):
		CloudDevice.__init__(self, name, cloud, "sensor", channel_subtype)
		self.thread = threading.Thread(target = self.measureThread)
		self.stopped = True
		self.measureInterval = measureInterval
		self.device = None
		self.available = False

	def measureThread(self):
		while self.stopped is False:
			startTime = time.time()
			value = self.measure()
			if value is not None:
				self.cloud.publish( {'channel_name': self.name, 'data': { 'status': value } } )
				if(VERBOSE):
					print('%s: %d' % (self.name, value))
			elif(VERBOSE):
				print self.name + "sensor measurement returned none"
				
					
			deltaTime = time.time() - startTime
			remainingTime = self.measureInterval - deltaTime
			if(remainingTime > 0):
				time.sleep(remainingTime)

	def measure(self):
		return none

	def start(self):
		if self.device is not None:
			self.stopped = False
			self.thread.start()
		else:
			print "Cannot start " + self.name + " sensor thread: No device detected"

	def stop(self):
		self.stopped = True
