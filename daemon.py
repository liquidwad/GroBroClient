from config import *
from cloud import *
from BME280 import *
import threading
import time

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
		
		while cloud == None or not cloud.connected:
			time.sleep(1)
		
		print "Initializing sensors..."
		# During initialization, each sensor object will report to the cloud whether or not it is available 
		temp_sensor = TemperatureSensor("temperature", cloud, measureInterval = TEMP_INTERVAL)
		humidity_sensor = HumiditySensor("humidity", cloud, TEMP_INTERVAL)
		sensors.extend([temp_sensor, humidity_sensor])

		# TODO: Initialize all actuators here and add them as cloud subscribers before starting the cloud connection
		print "Pulling..."
		cloud.pull_updates()

		while not cloud.pulled_data:
			pass

		#Now we have the latest data and we initialize actuators
		last_data = cloud.pulled_data
		cloud.reset_pull_data()

		print "Starting measurements..."

		for sensor in sensors:
			sensor.start()

		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			pass
		
if __name__ == "__main__":
	cloud_thread = CloudStartupThread()
	cloud_thread.daemon = True
	cloud_thread.start()

	cloud_mananger_thread = CloudManagerThread()
	cloud_mananger_thread.daemon = True
	cloud_mananger_thread.start()

	cloud_mananger_thread.join()
	cloud_thread.join()