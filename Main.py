#!/usr/bin/env python3
from mimetypes import init
from sqlite3 import Timestamp
from threading import Thread
from SerialComm import SerialComm
import serial
from Gsm import GSM, atReceive
import time,threading,datetime
import re
from AtEnums import timeAT
from UserActions import *
from DatabaseHandler import DatabaseConnection
from AtEnums import messageNotiAT
from GPIO import *
from UDP import UdpServer
serverIp = "192.168.4.110"
serverPort = 12000
DB_PATH = "HomeSecurity.db"
SERIAL_PORT = "/dev/ttyUSB0"
BUZZER_PIN = 17
class Application:
    def __init__(self):
        self.isTimeSet = False
        self.gsmHandler = None
        self.gsmSerial= None
        self.buzzer = GPIO_Handler(BUZZER_PIN,GPIO_Direction.OUTPUT.value,GPIO_State.LOW.value)
        self.udpServer= UdpServer(serverIp,serverPort)
        self.doorSensor= None
        self.isMessage = False
        self.number = ""
        self.dbConnection = DatabaseConnection(DB_PATH)  
        self.getNumberFromDb()      
        self.initGsm()
        self.UserAct = UserActions(self.dbConnection,self.buzzer,self.gsmHandler,self.udpServer)
        self.TestThreadRSSI()
    def initGsm(self):
        port = SERIAL_PORT
        baudrate = 115200
        parity = serial.PARITY_NONE
        stopbit = serial.STOPBITS_ONE
        datasize = serial.EIGHTBITS

        self.gsmSerial= SerialComm(port,baudrate,datasize,parity,stopbit)
        self.gsmHandler = GSM(self.gsmSerial)
        self.gsmHandler.AddSubscribers(self.GsmOnReceive)

        
    def GsmOnReceive(self,gsmEvent,reGroup):          
        self.UserAct.parseAtCommand(gsmEvent,reGroup)
                   
    def getRssi(self):
        while True:
            # print("getRssi")
            # self.gsmHandler.getTime()
            time.sleep(5)
    def TestThreadRSSI(self):
        test = threading.Thread(target=self.getRssi)
        test.start()
    def processGsmMessage(self,data):
        print(data)
        self.UserAct.processUserMessage(data)
    def getNumberFromDb(self):
        dets = self.dbConnection.getUserDetails()
        if(len(dets) > 0):
            self.number = dets[0][0]
    def setTime(self,groups):
        TimeStamp = groups[messageNotiAT.TIME.value]
        TimeStamp = TimeStamp[:-3]
        date_object = datetime.strptime(TimeStamp, '%y/%m/%d,%H:%M:%S')
        a_timedelta = date_object - datetime(1900, 1, 1)
        seconds = a_timedelta.total_seconds()
        #time.clock_settime(time.CLOCK_REALTIME,seconds)

if __name__ == "__main__":
    app = Application()