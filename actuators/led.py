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
        self.profiles = []
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
        while True:
            n = 0
            try:
                n = len(self.profiles[0])
            except Exception, e:
                n = 0
                
            if( n > 0 ):
                t= time.localtime()
                tNow = time.mktime(t)
                tStart = time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, t.tm_wday, t.tm_yday, t.tm_isdst))
                tSec = tNow - tStart # number of seconds elapsed since start of day
                
                # Convert current time to profile lookup indices for interpolation
                t_frac = tSec/86400.0 # fraction of day that has elapsed, given 86400 seconds per day
                i_f = n*t_frac #floating point index
                i_l = math.floor(i_f) #left interp index
                i_r = (i_l + 1) % n #right interp index with wraparound
                w = i_f - i_l # interpolation weight
                
                # interpolate brightness value by blending left and right samples using weight
                b = self.profiles[0][i_l]*w + self.profiles[0][i_r]*(1.0-w)
                # cap the brightness value to the limits
                brightness = math.min(1.0,math.max(0.0,b))
                
                # set the brightness value 
                self.changeValue(0, brightness )
                
            time.sleep(1)
            
        
    def changeValue(self, channel, duty):
        resolution = 4095.0
        with self.cloud.i2c_lock:
            self.device.set_pwm(channel, 0, int((1.0-duty)*resolution))
        
        if(VERBOSE):
            print('%s chan %d was set to %s' % (self.name, channel, duty))
    
    def applyProfile(self, channel, samples):
        self.profiles[channel] = samples
        if VERBOSE:
            print('Assigned profile to channel %d' % (channel))
            print(samples)
        
    def on_update(self, data):
        if VERBOSE:
            print('%s got update:' % self.name)
            print data
        
        state = data['data']['state']
        if((state is not None) and (state is not self.state)):
            self.state = state
            self.changeValue(0, state)
        
        if( (data is not None) and ('profiles' in data) and ('ch0' in data['profiles'])):
            self.applyProfile(0, data['profiles']['ch0'])
            
            
            
        