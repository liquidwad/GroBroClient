import io
import fcntl
from cloud import CloudSensor
from config import *
import time

# Based on 'notSMB' for an easier way to access the i2c bus using just one
# function. The main difference between this and notSMB is that the bus
# here will be dedicated to 1 device address
class IIC:
   def __init__(self, device, bus):

	  self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
	  self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

	  # set device address

	  fcntl.ioctl(self.fr, 0x0703, device)
	  fcntl.ioctl(self.fw, 0x0703, device)

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
	   time.sleep(0.1)
	   if nout != 0:
		   rv = self.read(nout)
	   return rv    

class K30: #CO2 Sensor
	def __init__(self, address, bus):
		self.address = address
		self.bus = bus

	def read_CO2(self):
		co2Val = None
		bus = IIC(self.address, self.bus)
		resp = bus.i2c([0x22,0x00,0x08,0x2A],4)
	    co2Val = (resp[1]*256) + resp[2]
		bus.close()

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