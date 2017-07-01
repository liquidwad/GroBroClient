from api import GroBroAPI
from config import *
import threading
import time

class CloudManager:
	def __init__(self, host, key):
		self.key = key
		cloudAPI = GroBroAPI(host)
		cloudAPI.register_callback('connect', self.on_connected)
		cloudAPI.register_callback('disconnect', self.on_disconnected)
		cloudAPI.register_callback('reconnect', self.on_reconnected)
		cloudAPI.register_callback('update', self.on_update)
		cloudAPI.register_callback('pull', self.on_pull)
		self.cloudAPI = cloudAPI
		self.connected = False
		self.subscribers = {}

	def wait(self, sec):
		self.cloudAPI.wait(sec)
	def connect(self):
		self.cloudAPI.connect()
		return True

	def pullUpdates(self):
		self.cloudAPI.pull()

	def subscribe(self, subscriber, channel):
		try:
			self.subscribers[channel].append(subscriber)
		except KeyError, e:
			self.subscribers[channel] = []
			self.subscribers[channel].append(subscriber)

	def publish(self, channel, cloud_type, available, data):
		self.cloudAPI.push({'channel_name': channel, 'type': cloud_type, 'available': available, 'data': data})

	def on_connected(self):
		print "connected"
		self.cloudAPI.register_device(self.key)
		self.connected = True

	def on_disconnected(self):
		print "disconnected"

	def on_reconnected(self):
		print "reconnected"
		self.cloudAPI.register_device(self.key)

	def on_update(self, data):
		try:
			subscribers = self.subscribers[data.channel_name]
			for subscriber in subscribers:
				subscriber.onUpdate(data)
		except Exception, e:
			pass

	def on_pull(self, data):
		if VERBOSE is True:
			print "Pulled: ", data


class CloudDevice:
	def __init__(self, name, cloud):
		self.name = name
		self.cloud = cloud
		#self.cloud.subscribe(self, name)

	def onUpdate(self, data):
		if VERBOSE:
			print('%s got update:' % self.name)
			print data

	def publish(self, channel, cloud_type, available, data):
		self.cloud.publish(channel, cloud_type, available, data)


class CloudActuator(CloudDevice):
	def __init__(self, name, cloud, type):
		CloudDevice.__init__(self, name, cloud)
		self.type = type
		self.cloud.subscribe(self, name)

class CloudSensor(CloudDevice):
	def __init__(self, name, cloud, measureInterval):
		CloudDevice.__init__(self, name, cloud)
		self.thread = threading.Thread(target = self.measureThread)
		self.stopped = True
		self.measureInterval = measureInterval
		self.device = None

	def reportAvailability(self, available):
		#for this to work we have to change the method of pushing
		self.publish(self.name, 'sensor', available, None)


	def measureThread(self):
		while self.stopped is False:
			startTime = time.time()
			value = self.measure()
			self.publish(self.name,'sensor', True, { 'value': value })
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
