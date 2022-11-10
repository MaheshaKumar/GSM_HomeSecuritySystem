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
import os
serverIp = "192.168.4.110"
serverPort = 12000
DB_PATH = r"/home/ubuntu/HomeSecurityServer/GSM_HomeSecuritySystem/HomeSecurity.db"
SERIAL_PORT = "/dev/ttyUSB0"
BUZZER_PIN = 17
class Application:
    def __init__(self):
        """
        Application init for start of application
        Arguments:
            self: an Application datatype            
        Returns:
            None
        """
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

    def initGsm(self):
        """
        initialize Gsm module by starting up serial communication
        Arguments:
            self: an Application datatype            
        Returns:
            None
        """
        port = SERIAL_PORT
        baudrate = 115200
        parity = serial.PARITY_NONE
        stopbit = serial.STOPBITS_ONE
        datasize = serial.EIGHTBITS

        self.gsmSerial= SerialComm(port,baudrate,datasize,parity,stopbit)
        self.gsmHandler = GSM(self.gsmSerial)
        self.gsmHandler.AddSubscribers(self.GsmOnReceive)
        
    def GsmOnReceive(self,gsmEvent,reGroup): 
        """
        Callback function that will be called whenever the GSM receives messages
        Arguments:
            self: an Application datatype
            gsmEvent: an atReceive enum for specify the event type
            reGroup: an regex list to output the matches of the data received 
            from the Gsm Module
        Returns:
            None
        """         
        self.UserAct.parseAtCommand(gsmEvent,reGroup)
                               
    def getNumberFromDb(self):
        """
        get user number from the database
        Arguments:
            self: an Application datatype            
        Returns:
            None
        """
        dets = self.dbConnection.getUserDetails()
        if(len(dets) > 0):
            self.number = dets[0][0]    

if __name__ == "__main__":
    app = Application()