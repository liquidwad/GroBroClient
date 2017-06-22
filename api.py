from socketIO_client import SocketIO, LoggingNamespace

def on_recieve_response(*args):
    print('on_recieve_response', args)

def on_update_response(*args):
	print('on_update_response', args)

with SocketIO('https://grobroserver-liquidwad.c9users.io', 8080, LoggingNamespace) as socketIO:
    socketIO.emit('register_device', {'key': 'RwsoNt3LkgPa2fUCS4KF'})
    socketIO.on('recieve', on_recieve_response)
    socketIO.on('update', on_update_response)
    socketIO.emit('pull', {})
    socketIO.emit('push', {u'channel_name': u'Ventilator', u'data': {u'override': True, u'status': u'on'}})
    socketIO.wait(seconds=10)