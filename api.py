from socketIO_client import SocketIO, LoggingNamespace
import shelve

__CACHE__FILE__ = "grobro.cache"

class Cache:
	@staticmethod
	def get_cache():
		s = shelve.open(__CACHE__FILE__, writeback=True)
		s.close()

	@staticmethod
	def put_cache(channels):
		s = shelve.open(__CACHE__FILE__, writeback=True)

		try:
			for channel in channels:
				channel_name = channel['channel_name'].encode('ascii','ignore')
				s[channel_name] = channel['data']
		finally:
			s.close()

	@staticmethod
	def update_cache(channel):
		s = shelve.open(__CACHE__FILE__, writeback=True)

		try:
			channel_name = channel['channel_name'].encode('ascii','ignore')
			s[channel_name] = channel['data']
			print channel_name, "added to shelve"
		finally:
			s.close()

class GroBroAPI:
	def __init__(self, host, port=8080):
		self.host = host
		self.port = port
		self.connected = False
		self.callbacks = {}

	def register_callback(self, *args):
		name, callback = args
		self.callbacks[name] = callback

	def call_callback(self, name, data=None):
		if name in self.callbacks:
			if data == None:
				self.callbacks[name]()
			else:
				self.callbacks[name](data)

	def __on_connect(self):
	    self.call_callback('connect')
	    self.connected = True

	def __on_disconnect(self):
	    self.call_callback('disconnect')
	    self.connected = False

	def __on_reconnect(self):
	    self.call_callback('reconnect')
	    self.connected = True

	def __on_pull_response(self, args):
	    self.call_callback('pull', args)

	    #put all channels into cache
	    Cache.put_cache(args)

	def __on_update_response(self, args):
		self.call_callback('update', args)

		#put recieved channel into cache
		Cache.put_cache(data)

	def push(self, data):
		self.socketIO.emit('push', data)

		#put pushed channel into cache
		Cache.update_cache(data)

	def pull(self):
		self.socketIO.emit('pull', {}, self.__on_pull_response)

		#if not connect return caches channels
		if not self.connected:
			self.call_callback('pull', Cache.get_cache())

	def register_device(self, key):
		self.socketIO.emit('register_device', {'key': key })

	def connect(self, callbacks=None):
		self.socketIO = SocketIO(self.host, self.port, LoggingNamespace)

		#register events
		self.socketIO.on('connect', self.__on_connect)
		self.socketIO.on('disconnect', self.__on_disconnect)
		self.socketIO.on('reconnect', self.__on_reconnect)
		self.socketIO.on('update', self.__on_update_response)

	def wait(self, seconds):
		self.socketIO.wait(seconds=seconds)

api = GroBroAPI('https://grobroserver-liquidwad.c9users.io')

def connected():
	print "connected"

def disconnected():
	print "disconnected"

def reconnected():
	print "reconnected"
	api.register_device('RwsoNt3LkgPa2fUCS4KF')

def update(data):
	print data

def pull(data):
	print data
	Cache.put_cache(data)


Cache.get_cache()
api.register_callback('connect', connected)
api.register_callback('disconnect', disconnected)
api.register_callback('reconnect', reconnected)
api.register_callback('update', update)
api.register_callback('pull', pull)
api.connect()
api.register_device('RwsoNt3LkgPa2fUCS4KF')
api.pull()
#api.push({u'channel_name': u'Ventilator', u'data': {u'override': True, u'status': u'on'}})
#api.push({u'channel_name': u'Icebox', u'data': {u'override': True, u'status': u'on'}})
api.push({u'channel_name': u'Dog', u'data': {u'override': True, u'status': u'on'}})
api.wait(30)