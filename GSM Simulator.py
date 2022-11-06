#!/usr/bin/env python3
from SerialComm import SerialComm
import serial,re
from Gsm import atReceiveRegex
def printSerialData(data):
    print(data)
    # try:
    #     result = re.search(atReceiveRegex.MESSAGES.value,data.decode())
    #     print(result.groups())
    # except:
    #     print("")

port = "COM13"
baudrate = 115200
parity = serial.PARITY_NONE
stopbit = serial.STOPBITS_ONE
datasize = serial.EIGHTBITS

serialTest= SerialComm(port,baudrate,datasize,parity,stopbit)
serialTest.AddSubscribers(printSerialData)
serialTest.close()
serialTest.open()

while True:
    action = input("Enter message:")
    serialTest.sendSerial('+CMT: "+601154216256","","18/07/26,13:40:45+22"\r\n')
    serialTest.sendSerial("{0}\r\n".format(action))