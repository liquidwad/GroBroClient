from api import GroBroAPI
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

	def wait(self, sec):
		self.cloud_api.wait(sec)

	def connect(self):
		print "Connecting"
		self.cloud_api.connect()

	def pull_updates(self):
		self.cloud_api.pull()

	def subscribe(self, subscriber, channel):
		try:
			self.subscribers[channel].append(subscriber)
		except KeyError, e:
			self.subscribers[channel] = []
			self.subscribers[channel].append(subscriber)

	def publish(self, data):
		self.cloud_api.push(data)

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
		try:
			subscribers = self.subscribers[data.channel_name]
			for subscriber in subscribers:
				subscriber.on_update(data)
		except Exception, e:
			pass

	def on_pull(self, data):
		if VERBOSE is True:
			print "Pulled: ", data
		
		for chan in data:
			self.on_update(chan)
			
		self.pulled_data = data
		
	
	def reset_pull_data(self):
		self.pulled_data = None
		
	def getValue(self, data, channel):
		for chan in data:
			if chan.channel_name is channel:
				return chan.data.value
		
		return None
		


class CloudDevice:
	def __init__(self, name, cloud):
		self.name = name
		self.cloud = cloud

	def on_update(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data

class CloudActuator(CloudDevice):
	def __init__(self, name, cloud):
		CloudDevice.__init__(self, name, cloud)
		self.subscribe(this, name)
	
	def reportAvailability(self, available):
		self.available = available
		self.cloud.publish({'channel_name': self.name, 'available': self.available })

		if(VERBOSE and available):
			print self.name + " actuator was initialized"
	
	def changeValue(self, newValue):
		pass


		

class CloudSensor(CloudDevice):
	def __init__(self, name, cloud, measureInterval):
		CloudDevice.__init__(self, name, cloud)
		self.thread = threading.Thread(target = self.measureThread)
		self.stopped = True
		self.measureInterval = measureInterval
		self.device = None
		self.type = "Sensor"
		self.available = False

	def reportAvailability(self, available):
		self.available = available
		self.cloud.publish({'channel_name': self.name, 'available': self.available })

		if(VERBOSE and available):
			print self.name + " sensor was detected"

	def measureThread(self):
		while self.stopped is False:
			startTime = time.time()
			value = self.measure()
			if value is not None:
				self.cloud.publish( {'channel_name': self.name, 'data': { 'override': self.override, 'status': value } } )
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
