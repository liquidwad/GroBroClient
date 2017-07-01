
from cloud import CloudSensor
from Adafruit_BME280 import *
from config import *
import time

bme280 = None

class BME280Sensor(CloudSensor):
    def __init__(self, name, cloud, measureInterval):
        CloudSensor.__init__(self, name, cloud, measureInterval)
        if(bme280 == None):
            try:
                bme280 = BME280(mode=BME280_OSAMPLE_8)
            except Exception, e:
                bme280 = None
        self.device = bme280
        CloudSensor.reportAvailability(self.device!=None)

    def measure(self, timeout):
        if(self.device is None):
            return None
        measurement = None
        startTime = time.time()
        while (time.time() - startTime) < timeout:
            try:
                meas = self.device.read_humidity()
                if( measureCheck(meas) )
                    measurement = postMeasure(meas)
                    break;
            except Exception, e:
                if VERBOSE == True:
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
        BME280Sensor.__init__(name, cloud, measureInterval)

    def deviceMeasure(self):
        hum = self.device.read_humidity()

    def measureCheck(self, measurement):
         return (measurement is not None) and (measurement < 100) and (measurement > 20)

class TemperatureSensor(BME280Sensor):
    def __init__(self, name, cloud, measureInterval = 5, celcius = False):
        BME280Sensor.__init__(name, cloud, measureInterval)
        self.celcius = celcius

    def deviceMeasure(self):
        hum = self.device.read_temperature()

    def measureCheck(self, measurement):
         return (measurement is not None) and (measurement < 60) and (measurement > 0)

    def postMeasure(sef, measurement):
        if(!self.celcius):
            # convert from celcius to fahrenheit
            measurement = temp*1.8 + 32

        return measurement