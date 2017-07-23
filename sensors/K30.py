from cloud import CloudSensor
from config import *
import time
import serial


class K30:  # CO2 Sensor
	def __init__(self):
		self.ser = serial.Serial("/dev/ttyAMA0", baudrate=9600, timeout=.5)

	def read_CO2(self):
		self.ser.flushInput()
		self.ser.write("\xFE\x44\x00\x08\x02\x9F\x25")
		time.sleep(.5)
		resp = self.ser.read(7)
		high = ord(resp[3])
		low = ord(resp[4])
		co2 = (high * 256) + low
		return co2

	def close(self):
		self.ser.close()
	
	def available(self):
		return self.ser.isOpen()


k30 = None


class CO2Sensor(CloudSensor):
	def __init__(self, name, cloud, measureInterval):
		CloudSensor.__init__(self, name, cloud, measureInterval, 0, 5000, "CO2")

	def detect(self):
		global k30
		if k30 is None:
			try:
				temp = K30()
				temp.close()
				return True
			except:
				return False
		else:
			return k30.available()

	def initDevice(self):
		global k30
		if(k30 is None):
			try:
				k30 = K30()
				if VERBOSE:
					print "K30 sensor Detected!"
			except Exception, e:
				k30 = None

		self.device = k30
		self.reportAvailability(k30 is not None)

	def measure(self, timeout=K30_TIMEOUT):
		if(self.device is None):
			return None
		measurement = None
		startTime = time.time()
		while ((time.time() - startTime) < timeout) and (self.device is not None):
			try:
				meas = self.deviceMeasure()
				if(self.measureCheck(meas)):
					measurement = self.postMeasure(meas)
					break
			except Exception, e:
				if VERBOSE:
					print "K30 measure fail: "
					print e
			time.sleep(0.2)

		return measurement

	def deviceMeasure(self):
		return self.device.read_CO2()

	def measureCheck(self, measurement):
		return (measurement is not None) and (measurement < self.range_max) and (measurement > self.range_min)

	def postMeasure(self, measurement):
		return measurement
