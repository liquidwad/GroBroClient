from cloud import CloudSensor
from Adafruit_BME280 import *
from config import *
import time

bme280 = None

class BME280Sensor(CloudSensor):
	def __init__(self, name, cloud, measureInterval, range_min, range_max, channel_subtype = "BME280"):
		self.address = 0x76
		CloudSensor.__init__(self, name, cloud, measureInterval, range_min, range_max, channel_subtype)

	def initDevice(self):
		global bme280
		if(bme280 is None):
			try:
				with self.cloud.i2c_lock:
					bme280 = BME280(mode=BME280_OSAMPLE_8)
				if VERBOSE:
					print "BME280 sensor Detected!"
			except Exception, e:
				bme280 = None
		
		self.device = bme280
		self.reportAvailability(bme280 is not None)
		
	def measure(self, timeout = BME280_TIMEOUT):
		if(self.device is None):
			return None
		measurement = None
		startTime = time.time()
		while ((time.time() - startTime) < timeout) and (self.device is not None):
			try:
				meas = self.deviceMeasure();
				if( self.measureCheck(meas) ):
					measurement = self.postMeasure(meas)
					break;
			except Exception, e:
				if VERBOSE:
					print "BME280 measure fail: "
					print e
			time.sleep(0.2)

		return measurement

	def deviceMeasure(self):
		return 0

	def measureCheck(self, measurement):
		return (measurement is not None) and (measurement < self.range_max) and (measurement > self.range_min)

	def postMeasure(self, measurement):
		return measurement

class HumiditySensor(BME280Sensor):
	def __init__(self, name, cloud, measureInterval = 5):
		BME280Sensor.__init__(self,name, cloud, measureInterval, 0, 100, "humidity")

	def deviceMeasure(self):
		with self.cloud.i2c_lock:
			result = self.device.read_humidity()
		return result

class TemperatureSensor(BME280Sensor):
	def __init__(self, name, cloud, measureInterval = 5):
		BME280Sensor.__init__(self, name, cloud, measureInterval, -40, 100, "temperature")

	def deviceMeasure(self):
		with self.cloud.i2c_lock:
			result = self.device.read_temperature()
		return result

	def postMeasure(self, measurement):
		return measurement