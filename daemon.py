from config import *
from cloud import *
from sensors.BME280 import *
from sensors.light import *
from sensors.K30 import *
from actuators.relay import *
from actuators.lcd import *
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
	
	def wait(self, seconds):
		global cloud
		cloud.wait(seconds)
	
	def run(self):
		global cloud

		sensors = []
		actuators = []
		
		while cloud == None or not cloud.connected:
			time.sleep(1)

		# TODO: Initialize all actuators here and add them as cloud subscribers before starting the cloud connection
		print "Pulling..."
		cloud.pull_updates(False)

		# TODO: fix this because it will block forever if pulled data is empty
		while cloud.data_pulled is False:
			time.sleep(0.1)

		#Now we have the latest data and we initialize actuators
		last_data = cloud.pulled_data
		
		print "Initializing actuators..."
		#If this is the first time we ever run, the server will have an empty pull
		
		if DEVICE_MODEL is 'WW8':
			# Initialize LCD's
			actuators.append(LeftRelayLCD("lcd0", cloud, last_data))
			actuators.append(RightRelayLCD("lcd1", cloud, last_data))
			
			# Initialize relays
			for i in range(0,8):
				actuators.append(CloudRelay("relay" + str(i), cloud, i, last_data))
		
		print "Initializing sensors..."
		# During initialization, each sensor object will report to the cloud whether or not it is available 
		sensors.append(TemperatureSensor("temperature", cloud, measureInterval = TEMP_INTERVAL))
		sensors.append(HumiditySensor("humidity", cloud, measureInterval = HUMIDITY_INTERVAL))
		sensors.append(CO2Sensor("CO2", cloud, measureInterval = CO2_INTERVAL))
		sensors.append(UVSensor("UV", cloud, measureInterval = UV_INTERVAL))
		sensors.append(IRSensor("IR", cloud, measureInterval = IR_INTERVAL))
		sensors.append(LumenSensor("lumens", cloud, measureInterval = LUMEN_INTERVAL))

		print "Starting measurements..."
		
		#stagger sensor start so they don't all measure at the same time
		for sensor in sensors:
			sensor.start()
			time.sleep(0.5)
		
		while True:
			cloud.wait(999999)
		
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
		time.sleep(0.1)