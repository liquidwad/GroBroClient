from config import *
from cloud import *
from BME280 import *


if __name__ == "__main__":
	cloud = CloudManager(API_HOST, DEVICE_KEY)
	print "Connecting..."
	sensors = []
	if cloud.connect():
		print "Initializing sensors..."
		# During initialization, each sensor object will report to the cloud whether or not it is available 
		sensors.append(TemperatureSensor("temperature", cloud, measureInterval = TEMP_INTERVAL))
		sensors.append(HumiditySensor("humidity", cloud, TEMP_INTERVAL))
		# TODO: Initialize all actuators here and add them as cloud subscribers before starting the cloud connection
		print "Pulling..."
		cloud.pullUpdates()
		print "Starting measurements..."
		for sensor in sensors:
			sensor.start()
	else:
		print "Failed to connect to cloud."
		#TODO: implement recovery actio
	
	try:
		while(True):
			cloud.wait(1)
	except KeyboardInterrupt:
		pass
	finally:
		for sensor in sensors:
			sensor.stop()