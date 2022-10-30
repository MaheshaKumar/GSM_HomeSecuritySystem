#!/usr/bin/env python3
import sys,time
from unittest import result
import serial,threading
import sys,os

from Gsm import QUEUE_SIZE
sys.path.append(os.getcwd())
from EnumTest import *
import re, queue

from setuptools import Command
CR_CHAR = 0x0D
LF_CHAR = 0x0A
TX_DELAY = 2
class Event(object):

	def __init__(self):
		self.__eventhandlers = []

	def __iadd__(self, handler):
		self.__eventhandlers.append(handler)
		return self

	def __isub__(self, handler):
		self.__eventhandlers.remove(handler)
		return self

	def __call__(self, *args, **keywargs):
		for eventhandler in self.__eventhandlers:
			eventhandler(*args, **keywargs)

class SerialComm:
    
    def __init__(self, name,_baudrate,_byteSize,_parity,_stopbit):
        self.serialInst = serial.Serial(port = name, baudrate = _baudrate,parity = _parity, stopbits = _stopbit, bytesize = _byteSize)
        self.serialInst.timeout = None
        self.OnSerialReceive = Event()
        self.txQueue = queue.Queue(QUEUE_SIZE)
    def AddSubscribers(self,objMethod):
        self.OnSerialReceive += objMethod
		
    def RemoveSubscribers(self,objMethod):
        self.OnSerialReceive -= objMethod
    
    def sendSerial(self,data):
        dataBytes = data.encode()
        self.txQueue.put_nowait(dataBytes)
    def sendSerialBytes(self,data):
        self.txQueue.put_nowait(data)
    def open(self):
        self.serialInst.open()
        receiveThread = threading.Thread(target=self.serialReceiveThread)
        sendThread = threading.Thread(target=self.serialSendThread)
        receiveThread.setDaemon(True)
        sendThread.setDaemon(True)
        receiveThread.start()
        sendThread.start()
    def close(self):
        self.serialInst.close()
    def resetOutputBuffer(self):
        self.serialInst.reset_output_buffer()
    def serialReceiveThread(self):
        while True:
            data = b''           
            bytesWaiting = self.serialInst.inWaiting()
            if bytesWaiting != 0:           
                data = self.serialInst.readline()
                print("Receiving")                
                self.OnSerialReceive(data)
                self.serialInst.flush()
    def serialSendThread(self):
        while True:
            data = self.txQueue.get()
            self.serialInst.write(data)
            time.sleep(TX_DELAY)
                     
def send(serialDev):
    while True:
        print("Sending")
        # #serialDev.sendSerial("AT+CMGL=\"ALL\",0")
        # print(atTransmit.SEND_MESSAGE.value)
        # serialDev.sendSerial(atTransmit.SEND_MESSAGE.value)
        time.sleep(5)
def printSerialData(data):
    print(data)
    try:
        result = re.search(atReceiveRegex.MESSAGES.value,data.decode())
        print(result.groups())
    except:
        print("")
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
    try:

        port = "COM8"
        baudrate = 115200
        parity = serial.PARITY_NONE
        stopbit = serial.STOPBITS_ONE
        datasize = serial.EIGHTBITS

        serialTest= SerialComm(port,baudrate,datasize,parity,stopbit)
        serialTest.AddSubscribers(printSerialData)

        sendThread = threading.Thread(target=send,args=(serialTest,))
        serialTest.close()

        #serialTest.open()
        time.sleep(3)
        serialTest.sendSerial("ATE0\r\n")
        time.sleep(3)
        serialTest.sendSerial("AT+CSCLK=0\r\n")
        time.sleep(3)
        SendSms(serialTest)
        sendThread.start()
        sendThread.join()
        #serialTest.serialReceive()
    except KeyboardInterrupt as e:
        sys.exit()
