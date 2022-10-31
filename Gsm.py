#!/usr/bin/env python3
from operator import truediv
import threading, queue,sys,os,Event,time
sys.path.append(os.getcwd())
import re
from enum import Enum, auto
import serial
import SerialComm
from Event import Event

QUEUE_SIZE = 15

class atReceive(Enum):
    
    RSSI_LEVEL = 0
    RECEIVE_MESSAGE = auto()
    TIME = auto()
    SMS_NOTIFICATION = auto()
    OK = auto()
    MESSAGES = auto()
class atReceiveRegex(Enum):   
    RSSI_LEVEL = r'^\+CSQ\:\W(\d+)'
    RECEIVE_MESSAGE = r'^\+CMGL\:\W(\d+),(\"[a-zA-Z0-9_ ]*\"),"\+(\d+)\".\"\",(\"(\d+)\/(\d+)\/(\d+),(\d+):(\d+):(\d+)\+(\d+)\")'
    TIME =  r'^\+CCLK\:\W\"(\d+)\/(\d+)\/(\d+),(\d+):(\d+):(\d+)\+(\d+)\"'
    SMS_NOTIFICATION = r'^\+CMT\:\W\"\+(\d+)","",("(\d+)\/(\d+)\/(\d+),(\d+):(\d+):(\d+)\+(\d+)")'          
    OK = r'^OK'  
    MESSAGES = r'[a-zA-Z0-9_: ]*'

class GSM:
    def __init__(self, serialComm):
        self.serial = serialComm
        self.rxThread = None
        self.txThread = None
        self.rxQueue = queue.Queue(QUEUE_SIZE)
        self.TxQueue = queue.Queue(QUEUE_SIZE)
        self.registerListerner()
        self.eventHandler = Event()
        self.rxThread = threading.Thread(target=self.serialRxThread)
        self.rxThread.setDaemon(True)
        self.rxThread.start()
        self.serial.close()
        self.serial.open()
        self.setBaud(115200)
        self.setEchoOff()
        self.setSleepOff()
        
    def AddSubscribers(self,objMethod):
        self.eventHandler += objMethod
    def registerListerner(self):
        self.serial.AddSubscribers(self.serialOnReceive)
    def serialOnReceive(self,data):
        print("GSM::serialOnReceive:{0}".format(data))
        self.rxQueue.put_nowait(data)
    def processRx(self, data):
        count = 0
        try:
            if(data.decode() == '\r\n'):
                return
            else:
                for i in atReceiveRegex:                       
                    result = re.search(i.value,data.decode())
                    print(result)
                    # print("processRx {1}: {0} GsmEvent {2}",result.groups(),i.name,count)
                    if(result != None):
                        self.eventHandler(count,result)                    
                        break
                    count = count + 1
        except Exception as e:
            print(str(e))
            count = 0
                
            
                
    def SendSms(self,number, message):
        if(number == ""):
            return False
        self.setTextMode()
        print("Text Mode Enabled…")
        atCommand = 'AT+CMGS="+{0}"\r'.format(number)
        print(atCommand)
        self.serial.sendSerialBytes(atCommand.encode())
        print("sending message….")
        self.serial.resetOutputBuffer()
        time.sleep(2)
        message = message +'\n'
        self.serial.sendSerialBytes(str.encode(message+chr(26)))
        print("message sent…")
    def setEchoOff(self):
        self.serial.sendSerial("ATE0\r\n")
    def setSleepOff(self):
        self.serial.sendSerial("AT+CSCLK=0\r\n")
    def getRSSI(self):
        self.serial.sendSerial("AT+CSQ\r\n")
    def getAllMessages(self):
        self.serial.sendSerial('AT+CMGL="ALL",0\r\n')
    def getTime(self):
        self.serial.sendSerial('AT+CCLK?\r\n')
    def setTime(self,time):
        atCommand = 'AT+CCLK="{0}"\r\n'.format(time)
        self.serial.sendSerial(atCommand)
    def setTextMode(self):
        self.serial.sendSerial("AT+CMGF=1\r\n")
    def setBaud(self,baudrate):
        atCommand = 'AT+IPR={0}\r\n'.format(str(baudrate))
        self.serial.sendSerial(atCommand)
    def serialRxThread(self):
        while True:
            data = self.rxQueue.get()
            self.processRx(data)
    def deleteAllMessages(self):
        self.serial.sendSerial('AT+CMGDA="DEL ALL"\r\n')


if __name__ == "__main__":
    port = "COM11"
    baudrate = 115200
    parity = serial.PARITY_NONE
    stopbit = serial.STOPBITS_ONE
    datasize = serial.EIGHTBITS

    serialTest = SerialComm.SerialComm(port,baudrate,datasize,parity,stopbit)
    gsm = GSM(serialTest)
    count =0
    gsm.deleteAllMessages()
    gsm.SendSms("60134230613", "Testing")
    while True:        
        
        time.sleep(10)