from config import *
from cloud import *
from BME280 import *
from relay import *
import threading
import time
import signal
import sys

cloud = None

class CloudStartupThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	
	def run(self):
		global cloud
		cloud = CloudManager(API_HOST, DEVICE_KEY)
		cloud.connect()
		cloud.wait(10)

class CloudManagerThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	
	def run(self):
		global cloud

		sensors = []
		actuators = []
		
		while cloud == None or not cloud.connected:
			time.sleep(1)

		# TODO: Initialize all actuators here and add them as cloud subscribers before starting the cloud connection
		print "Pulling..."
		cloud.pull_updates()

		while not cloud.pulled_data:
			pass

		#Now we have the latest data and we initialize actuators
		last_data = cloud.pulled_data
		
		print "Initializing actuators..."
		#If this is the first time we ever run, the server will have an empty pull
		
		if DEVICE_MODEL is 'WW8':
			for i in range(0,7):
				# During initialization, each actuator will report to the cloud that it is present
				if last_data is None:
					# Default initialValue will be False
					actuators.append(CloudRelay("relay" + str(i), cloud, i))
				else:
					# Obtain this relay's initial state from the pulled data
					initialValue = cloud.getValue(last_data, "relay"+ str(i))
					if initialValue is None:
						initialValue = False
					actuators.append(CloudRelay("relay" + str(i), cloud, i, initialValue))
		
		cloud.reset_pull_data()
		
		print "Initializing sensors..."
		# During initialization, each sensor object will report to the cloud whether or not it is available 
		temp_sensor = TemperatureSensor("temperature", cloud, measureInterval = TEMP_INTERVAL)
		humidity_sensor = HumiditySensor("humidity", cloud, TEMP_INTERVAL)
		sensors.extend([temp_sensor, humidity_sensor])

		print "Starting measurements..."

		for sensor in sensors:
			sensor.start()
		
		while True:
			time.sleep(100)
		
def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
		
if __name__ == "__main__":
	cloud_thread = CloudStartupThread()
	cloud_thread.daemon = True
	cloud_thread.start()

	cloud_mananger_thread = CloudManagerThread()
	cloud_mananger_thread.daemon = True
	cloud_mananger_thread.start()
	
	while True:
		pass