from cloud import CloudSensor
import SI1145.SI1145 as SI1145
from config import *
import time

si1145 = None

class SI1145Sensor(CloudSensor):
	def __init__(self, name, cloud, measureInterval, range_min, range_max, channel_subtype = "SI1145"):
		self.address = 0x60
		CloudSensor.__init__(self, name, cloud, measureInterval, range_min, range_max, channel_subtype)

	def initDevice(self):
		global si1145
		with self.cloud.i2c_lock:
			if(si1145 is None):
				try:
					si1145 = SI1145.SI1145()
					if VERBOSE:
						print "SI1145 sensor Detected!"
				except Exception, e:
					si1145 = None
			
			self.device = si1145
		self.reportAvailability(si1145 is not None)
		
	def measure(self, timeout = SI1145_TIMEOUT):
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
					print "SI1145 measure fail: "
					print e
			time.sleep(0.2)

		return measurement

	def deviceMeasure(self):
		return 0

	def measureCheck(self, measurement):
		 return (measurement is not None) and (measurement >= self.range_min) and (measurement <= self.range_max)

	def postMeasure(self, measurement):
		return measurement

class UVSensor(SI1145Sensor):
	def __init__(self, name, cloud, measureInterval = 5):
		SI1145Sensor.__init__(self,name, cloud, measureInterval,  0, 12, "UV")

	def deviceMeasure(self):
		with self.cloud.i2c_lock:
			result = self.device.readUV() / 100
		return result


class IRSensor(SI1145Sensor):
	def __init__(self, name, cloud, measureInterval = 5):
		SI1145Sensor.__init__(self,name, cloud, measureInterval, 0, 65536, "IR")

	def deviceMeasure(self):
		with self.cloud.i2c_lock:
			result = self.device.readIR()
		return result

		 
class LumenSensor(SI1145Sensor):
	def __init__(self, name, cloud, measureInterval = 5):
		SI1145Sensor.__init__(self,name, cloud, measureInterval, 0, 65536, "Lumen")

	def deviceMeasure(self):
		with self.cloud.i2c_lock:
			result = self.device.readVisible()
		return result