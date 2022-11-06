#!/usr/bin/env python3
import RPi.GPIO as GPIO  
from time import sleep
from enum import auto,IntEnum
class GPIO_State(IntEnum):
    LOW = 0
    HIGH = 1
class GPIO_Direction(IntEnum):
    INPUT = GPIO.IN
    OUTPUT = GPIO.OUT
class GPIO_Handler():
    def __init__(self,pin,direction,initialState) -> None:
        self.pin = pin
        self.direction = direction
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, direction, initial=initialState)
    def setGpioState(self,val):
        GPIO.output(self.pin, val)
if __name__ == "__main__":
    LED = GPIO_Handler(17,GPIO_Direction.OUTPUT.value,GPIO_State.LOW.value)
    while True:
        LED.setGpioState(1)
        sleep(2)
        LED.setGpioState(0)
        sleep(1)

