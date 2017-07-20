from cloud import CloudSensor
from config import *
import time
import Adafruit_GPIO.I2C as I2C

class K30: #CO2 Sensor
	def __init__(self, address, bus):
		self.address = address
		self.bus = bus
		# Create I2C device.
		self._device = I2C.Device(address, bus)

	def read_CO2(self):
		co2Val = None
		self._device.writeRaw8(0x22)
		self._device.writeRaw8(0x00)
		self._device.writeRaw8(0x08)
		self._device.writeRaw8(0x2A)
		
		resp = []
		resp[0] = self._device.readRaw8()
		resp[1] = self._device.readRaw8()
		resp[2] = self._device.readRaw8()
		resp[3] = self._device.readRaw8()
		
		co2Val = (resp[1]*256) + resp[2]

		return co2Val
		
k30 = None

class CO2Sensor(CloudSensor):
	def __init__(self, name, cloud, measureInterval):
		self.address = 0x68
		CloudSensor.__init__(self, name, cloud, measureInterval, 0, 5000, "CO2")

	def initDevice(self):
		global k30
		if(k30 is None):
			try:
				k30 = K30(self.address, 1)
				if VERBOSE:
					print "K30 sensor Detected!"
			except Exception, e:
				k30 = None
		
		self.device = k30
		self.reportAvailability(k30 is not None)
		
	def measure(self, timeout = K30_TIMEOUT):
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