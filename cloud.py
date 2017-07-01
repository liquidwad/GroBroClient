from api import GroBroAPI
import threading

class CloudManager:
	def __init__(self, host, key):
		self.key = key
		cloudAPI = GroBroAPI(host)
		cloudAPI.register_callback('connect', connected)
		cloudAPI.register_callback('disconnect', disconnected)
		cloudAPI.register_callback('reconnect', reconnected)
		cloudAPI.register_callback('update', update)
		cloudAPI.register_callback('pull', pull)
		cloudAPI.connect()
		cloudAPI.register_device('RwsoNt3LkgPa2fUCS4KF')
		self.cloudAPI = cloudAPI

	def subscribe(self, subscriber, channel):
		self.subscribers[channel].append(subscriber)

	def publish(self, channel, data):
		#api.push({u'channel_name': u'Ventilator', u'data': {u'override': True, u'status': u'on'}}
		api.push({u'channel_name': channel, u'data': data})
		api.wait(30)

	def connected(self):
		print "connected"

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
		print data


class CloudDevice:
	def __init__(self, name, cloud):
		self.name = name
		self.cloud = cloud
		self.cloud.subscribe(self, name)

	def onUpdate(self, data):
		#TODO: remove these prints after testing
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

	def measureThread(self):
		while(!self.stopped):
			value = measure()
			publish({u'value' : value})
			wait(self.measureInterval)

	def measure(self):
		return none

	def start(self):
		self.stopped = False
		self.thread.start()

	def stop(self):
		self.stopped = True
		


if __name__ == "__main__":
	cloud = CloudManager('https://grobroserver-liquidwad.c9users.io', 'RwsoNt3LkgPa2fUCS4KF')