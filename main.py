from gpiozero import PWMLED
from time import sleep

import statusLED
import gpiozero

def pressed():
    print("We did it")
def released():
    print ("we undid it")


             
led = statusLED.statusLight(18)
button = gpiozero.DigitalInputDevice(4)

change = 0.01




while True:
    if button.is_active:
        led.flash()  
    
    
    sleep(.025) 

