from cloud import CloudSensor
from Adafruit_BME280 import *
from config import *
import time

bme280 = None

class BME280Sensor(CloudSensor):
    def __init__(self, name, cloud, measureInterval, channel_subtype = "BME280"):
        self.address = 0x77
        CloudSensor.__init__(self, name, cloud, measureInterval, channel_subtype)

    def initDevice(self):
        global bme280
        if(bme280 is None):
            try:
                bme280 = BME280(mode=BME280_OSAMPLE_8)
                if VERBOSE:
                    print self.name + " sensor Detected!"
            except Exception, e:
                bme280 = None
        
        self.device = bme280
        self.reportAvailability(bme280 is not None)
        
    def measure(self, timeout = BME280_TIMEOUT):
        if(self.device is None):
            return None
        measurement = None
        startTime = time.time()
        while (time.time() - startTime) < timeout:
            try:
                meas = self.deviceMeasure();
                if( self.measureCheck(meas) ):
                    measurement = self.postMeasure(meas)
                    break;
            except Exception, e:
                if VERBOSE == True:
                    print "BME280 measure fail: "
                    print e
            time.sleep(0.2)

        return measurement

    def deviceMeasure(self):
        return 0

    def measureCheck(self, measurement):
        return True

    def postMeasure(self, measurement):
        return measurement

class HumiditySensor(BME280Sensor):
    def __init__(self, name, cloud, measureInterval = 5):
        BME280Sensor.__init__(self,name, cloud, measureInterval, "humidity")

    def deviceMeasure(self):
        return self.device.read_humidity()

    def measureCheck(self, measurement):
         return (measurement is not None) and (measurement < 100) and (measurement > 20)

class TemperatureSensor(BME280Sensor):
    def __init__(self, name, cloud, measureInterval = 5, celcius = False):
        BME280Sensor.__init__(self, name, cloud, measureInterval, "temperature")
        self.celcius = celcius

    def deviceMeasure(self):
        return self.device.read_temperature()

    def measureCheck(self, measurement):
         return (measurement is not None) and (measurement < 60) and (measurement > 0)

    def postMeasure(self, measurement):
        if not self.celcius:
            # convert from celcius to fahrenheit
            measurement = measurement*1.8 + 32

        return measurement