from cloud import *
from config import *
import RPi.GPIO as GPIO
import Adafruit_PCA9685
import time
import math


class CloudLED(CloudActuator):
    def __init__(self, name, cloud, address, pulled_data = {}):
        CloudActuator.__init__(self, name, cloud, "led")
        self.thread = threading.Thread(target = self.ledThread)
        self.thread.daemon = True
        self.address = address
        self.device = None
        self.dummy = 0
        if self.initDevice():
            initialValue = cloud.getValue(pulled_data, self.name)
            if initialValue is None:
                initialValue = 1.0
                self.reportAvailability(True, {'status':initialValue})
            else:
                self.reportAvailability(True)
            
            self.state = initialValue
            self.changeValue(0, initialValue)
            
            self.thread.start()
        else:
            self.reportAvailability(False)
    
    def initDevice(self):
        if(self.device is None):
            try:
                with self.cloud.i2c_lock:
                    self.device = Adafruit_PCA9685.PCA9685(address=self.address)
                    self.device.set_pwm_freq(PWM_FREQ)
                if VERBOSE:
                    print 'LED Controller at address 0x%02X detected!' % self.address
                return True
            except Exception, e:
                return False
        
        return False
    
    def ledThread(self):
        startTime = time.time()
        while True:
            t = time.time() - startTime
            f = 0.3
            brightness = (math.sin(2*math.pi*f*t)+1)*0.5
            self.changeValue(0, brightness )
            time.sleep(0.05)
        
    def changeValue(self, channel, duty):
        resolution = 4095.0
        with self.cloud.i2c_lock:
            self.device.set_pwm(channel, 0, int((1.0-duty)*resolution))
        
        if(VERBOSE):
            print('%s chan %d was set to %s' % (self.name, channel, duty))
    
    def on_update(self, data):
        if VERBOSE:
            print('%s got update:' % self.name)
            print data
        
        state = data['data']['status']
        if((state is not None) and (state is not self.state)):
            self.state = state
            self.changeValue(0, state)
            
            
        