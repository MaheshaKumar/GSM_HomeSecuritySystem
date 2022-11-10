#!/usr/bin/env python3
import threading, queue
import re,os
from enum import Enum, auto

QUEUE_MAX_SIZE = 15

class atReceive(Enum):
    OK = 0
    RSSI_LEVEL = auto()
    RECEIVE_MESSAGE = auto()    
    TIME = auto()
    SMS_NOTIFICATION = auto()
    MESSAGES = auto()

class atReceiveRegex(Enum):
    OK = r'^OK'
    RSSI_LEVEL = r'^\+CSQ\:\W(\d+)'
    RECEIVE_MESSAGE = r'^\+CMGL\:\W(\d+),(\"[a-zA-Z0-9_ ]*\"),"\+(\d+)\".\"\",(\"(\d+)\/(\d+)\/(\d+),(\d+):(\d+):(\d+)\+(\d+)\")'
    TIME =  r'^\+CCLK\:\W\"(\d+)\/(\d+)\/(\d+),(\d+):(\d+):(\d+)\+(\d+)\"'
    SMS_NOTIFICATION = r'^\+CMTI\:\W\"SM\",(\d+)'
    MESSAGES = r'[a-zA-Z0-9_ ]*'
def SendSms(serial):
    print("Text Mode Enabled…")
    time.sleep(3)
    serial.sendSerialBytes(b'AT+CMGS="+60134230613"\r')
    msg = "test message from SIM900A…"
    print("sending message….")
    time.sleep(3)
    serial.resetOutputBuffer()
    time.sleep(1)
    serial.sendSerialBytes(str.encode(msg+chr(26)))
    time.sleep(3)
    print("message sent…")
if __name__ == "__main__":
    
    print(os.path.abspath(os.getcwd())+"/HomeSecurity.db")