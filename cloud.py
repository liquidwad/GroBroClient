from api import GroBroAPI
from config import *
import threading
import time

class CloudManager:
	def __init__(self, host, key):
		self.key = key
		cloudAPI = GroBroAPI(host)
		cloudAPI.register_callback('connect', connected)
		cloudAPI.register_callback('disconnect', disconnected)
		cloudAPI.register_callback('reconnect', reconnected)
		cloudAPI.register_callback('update', update)
		cloudAPI.register_callback('pull', pull)
		self.cloudAPI = cloudAPI
		self.connected = False

	def connect(self, timeout):
		self.cloudAPI.connect()
		timeStart = time.time()
		timePassed = 0
		# Just block until the connection is successful
		while((self.connected == False) and (timePassed < timeout)):
			time.sleep(0.1)
			timePassed = time.time() - timeStart
		
		if self.connected:
			self.cloudAPI.register_device(self.key)

		return self.connected

	def pullUpdates(self):
		self.cloudAPI.pull()

	def subscribe(self, subscriber, channel):
		self.subscribers[channel].append(subscriber)

	def publish(self, channel, data):
		#api.push({u'channel_name': u'Ventilator', u'data': {u'override': True, u'status': u'on'}}
		api.push({u'channel_name': channel, u'data': data})

	def connected(self):
		print "connected"
		self.connected = True

	def disconnected(self):
		print "disconnected"

	def reconnected(self):
		print "reconnected"
		self.cloudAPI.register_device(self.key)

	def update(self, data):
		try:
			subscribers = self.subscribers[data.channel_name]
			for subscriber in subscribers:
				subscriber.onUpdate(data)
		except Exception, e:
			pass

	def pull(self, data):
		if(VERBOSE is True):
			print "Pulled: " + data


class CloudDevice:
	def __init__(self, name, cloud):
		self.name = name
		self.cloud = cloud
		self.cloud.subscribe(self, name)

	def onUpdate(self, data):
		if(VERBOSE == True):
			print('%s got update:' % self.name)
			print data

	def publish(self,data):
		self.cloud.publish(self.name, data)


class CloudActuator(CloudDevice):
	def __init__(self, name, cloud, type):
		CloudDevice.__init__(self, name, cloud)
		self.type = type

class CloudSensor(CloudDevice):
	def __init__(self, name, cloud, measureInterval):
		CloudDevice.__init__(self, name, cloud)
		self.thread = threading.Thread(target = measureThread)
		self.stopped = True
		self.measureInterval = measureInterval
		self.device = None

	def reportAvailability(self, available):
		publish(u'available': available)


	def measureThread(self):
		while(!self.stopped):
			startTime = time.time()
			value = measure()
			publish({u'value' : value})
			deltaTime = time.time() - startTime
			remainingTime = self.measureInterval - deltaTime
			if(remainingTime > 0):
				wait(remainingTime)

	def measure(self):
		return none

	def start(self):
		if(self.device is not None):
			self.stopped = False
			self.thread.start()
		else:
			print "Cannot start " + self.name + " sensor thread: No device detected"

	def stop(self):
		self.stopped = True
