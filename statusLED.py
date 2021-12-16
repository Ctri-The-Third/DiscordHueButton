

from types import MethodType
from gpiozero import PWMLED, DigitalInputDevice
import math 
from threading import Thread
from datetime import datetime, timedelta 
import time

class buttonWithLED:
    def __init__(self,LEDpin,BTNpin,notificationEmoji,notificationShade):
        self.notificationEmoji = notificationEmoji
        self.notificationShade = notificationShade
        self._LED = PWMLED(LEDpin)
        self._button = DigitalInputDevice(BTNpin)
        self._pulsedirection = 1
        self._pulsespeed = 0.01
        self._pulseValue = 0

        self._timeLastPresed = datetime.now()
        self._button.when_activated = self._onPress
        self._button.when_deactivated = self._onRelease
        self._stateFlag = "pulsing"
        
        self.onShortPress = None
        self.onLongPress = None
        self.is_active = False

        self._timePressed = 0
        self._flashEndTime = datetime.now()
        self._flashRate = 0.5
        self._continueLoop = True 
        self._loopThread = Thread(target=self._loop)
        self._loopThread.start()

    def flash(self,rate = 0.5,duration = 2 ):
        #sets instruciton to flash for half a second
        self._flashEndTime = datetime.now() + timedelta(seconds = duration)
        self._flashRate = rate 
        self._stateFlag = "flashing"
        pass 


    def setPulseSpeed(self, speed:int) -> None:
        """Set a rate of change betwee 0 and 1. The brightness value changes by this amount every 0.01 seconds - so 0.01 means one full cycle every 2 seconds"""
        self._pulsespeed = speed


    def terminate(self):
        self._continueLoop = False

    def _loop(self):
        while self._continueLoop:
            if datetime.now() < self._flashEndTime and self._stateFlag == "flashing":
                newValue = self._newFlashValue()
            elif datetime.now() >= self._flashEndTime and self._stateFlag == "flashing":
                self._stateFlag = "pulsing"
                self.setPulseSpeed(0.01)
            else: 
                newValue = self._newPulseValue()
                newValue = self._bounce(newValue)
            newValue = self._limitNewValue(newValue)
            
            
            self._LED.value = self._pulseValue = newValue
            time.sleep(0.01)
            
    def swtich_off(self):
        return 
    def switch_on(self):
        return 
    def _bounce(self,newValue):
        if newValue >= 1:
            self._pulsedirection = -1
            return 1
        elif newValue <= 0:
            
            self._pulsedirection = 1 
            return 0
        else:
            return newValue
    def _limitNewValue(self,newValue):
        if newValue > 1:
            return 1
        elif newValue < 0:
            self._pulsedirection = 1 
            return 0
        else:
            return newValue
    
    def _newPulseValue(self):
        return self._pulseValue + ( self._pulsedirection * self._pulsespeed)
        
    def _newFlashValue(self):
        flashRate = self._flashRate * 2 #e.g. every 0.5 seconds we change, so a full rotation is 1 second
        currentTime = time.time_ns() / 1000 / 1000 / 1000  #get time in seconds
        remainder = currentTime % flashRate  #determine how far through the cycle we are 
        #print("current time in seconds:{} full cycle: {} progress through cycle: {}".format(currentTime,flashRate,currentTime%flashRate))

        if remainder - self._flashRate < 0: #if in the first half, light off 
            return 0 
        elif remainder - self._flashRate >= 0: #if in the second, light on 
            return 1 
        #flash rate is 0.2.
        #at 0.1 we want off, at 0.0 we want off  0.1 / 0.2 = 0.5 
        #at 0.2 we want on at 0.3 we want on 
        #at 0.4 we want off 
        return 1 

    def _onPress(self):
        self._timeLastPresed = datetime.now()
        self.is_active = True
        timeString = self._timeLastPresed.strftime("%y-%m-%d %H:%M:%S.%f")
        pass 
    def _onRelease(self):
        targetTime =  self._timeLastPresed + timedelta(milliseconds= 500)
        diff = math.floor( (targetTime - datetime.now()).total_seconds() * 1000)
        print(diff)
        if diff > 0:
            if isinstance( self.onShortPress , MethodType):
                self.onShortPress(self)
            pass 
        elif targetTime <= datetime.now():
            if isinstance( self.onLongPress , MethodType):
                self.onLongPress(self)
            pass 
        else:
            print("?")
        self.is_active = False

    
