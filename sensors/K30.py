import io
import fcntl
from cloud import CloudSensor
from config import *
import time
import Adafruit_GPIO.I2C as I2C

I2C_SLAVE=0x0703
I2CBUS = 1

class IIC:
   def __init__(self, device, bus):

	  self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
	  self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

	  # set device address

	  fcntl.ioctl(self.fr, I2C_SLAVE, device)
	  fcntl.ioctl(self.fw, I2C_SLAVE, device)

   def write(self, data):
	  if type(data) is list:
		 data = bytes(data)
	  self.fw.write(data)

   def read(self, count):
	  s = ''
	  l = []
	  s = self.fr.read(count)
	  if len(s) != 0:
		 for n in s:
			l.append(ord(n))
	  return l
	

   def close(self):
	  self.fw.close()
	  self.fr.close()
	  
   def i2c(self,listin,nout):
	   self.write(bytearray(listin))
	   if nout != 0:
		   rv = self.read(nout)
	   return rv  
	   
	   
class K30: #CO2 Sensor
	def __init__(self, address, bus):
		self.address = address
		self.bus = bus
		# Create I2C device.
		self._device = I2C.Device(address, bus)
		
	def open_bus(self):
		pass
		#self._device = IIC(self.address, self.bus)
	
	def close_bus(self):
		pass
		#self._device.close()
		
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
		
		#resp = self._device.i2c([0x22,0x00,0x08,0x2A],4)
		#co2Val = (resp[1]*256) + resp[2]


		return co2Val
		
k30 = None

class CO2Sensor(CloudSensor):
	def __init__(self, name, cloud, measureInterval):
		self.address = 0x68
		CloudSensor.__init__(self, name, cloud, measureInterval, 0, 5000, "CO2")

	def detect(self):
		return True
		try:
			temp = K30(self.address, 1)
			temp.open_bus()
			temp.close_bus()
			return True
		except:
			return False
			
			
	def initDevice(self):
		global k30
		if(k30 is None):
			try:
				k30 = K30(self.address, 1)
				k30.open_bus()
				
				if VERBOSE:
					print "K30 sensor Detected!"
			except Exception, e:
				k30 = None
		
		k30.close_bus()
		self.device = k30
		self.reportAvailability(k30 is not None)
		
	def measure(self, timeout = K30_TIMEOUT):
		if(self.device is None):
			return None
		measurement = None
		startTime = time.time()
		while ((time.time() - startTime) < timeout) and (self.device is not None):
			try:
				meas = self.deviceMeasure()
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
		self.device.open_bus()
		co2 = self.device.read_CO2()
		self.device.close_bus()
		return co2

	def measureCheck(self, measurement):
		return (measurement is not None) and (measurement < self.range_max) and (measurement > self.range_min)

	def postMeasure(self, measurement):
		return measurement

if __name__ == "__main__":
	k30 = K30(0x68, 1)
	while True:
		try:
			k30.open_bus()
			co2Val = k30.read_CO2()
			k30.close_bus()
			print co2Val
		except Exception, e:
			print e
		time.sleep(1)