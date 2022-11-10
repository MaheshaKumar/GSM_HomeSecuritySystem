#!/usr/bin/env python3
from concurrent.futures import thread
from enum import Enum, IntEnum, auto
from itertools import count
from operator import truediv
import re
from Gsm import GSM,atReceive
from DatabaseHandler import DatabaseConnection,AlertTimeEnum
from AtEnums import messageNotiAT
from GPIO import GPIO_Handler,GPIO_State
from queue import Empty, Full, Queue
import threading

class UserActionEnum(IntEnum):
    HELP = 0
    PHONE_NUMBER = auto()
    ALERT_TIME = auto()
    SOUND_ALARM = auto()
    DOOR_STATUS = auto()
    OFF_ALARM = auto()
    ARM_DISARM = auto()

class Days(IntEnum):
    MONDAY = 0
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()
    DAYS_MAX = auto()
class DoorSensor(IntEnum):
    HEADER = 0
    DATA = auto()
    FOOTER = auto()
    
class UserActions:
    def __init__(self,dbConnection,buzzer,gsmHandler,udpServer):
        """
        UserActions init to handle user messages
        Arguments:
            self: an UserActions datatype  
            dbConnection: Database instance
            buzzer: Buzzer instance
            gsmHandler: GSM instance
            udpServer: UDP Server instance
        Returns:
            None
        """
        self.noAckCount = 0
        self.UdpMessageQueue = Queue(15)
        self.db = dbConnection
        self.buzzer = buzzer
        self.gsmHandler = gsmHandler
        self.number = None
        self.getNumberFromDb()  
        self.isMessage = False
        self.isArm = False
        self.isDoorSensorAvailable = True
        self.doorIsOpen = False
        self.triggered = False
        self.udpServer = udpServer
        self.udpServer.AddSubscribers(self.onUpdReceive)
        self.udpThread = threading.Thread(target = self.parseUdpMessage )
        self.udpThread.start()
        self.udpServer.startServer()
        self.rxNumber = ""
    def onUpdReceive(self,data):
        """
        Callback function that receives UDP data & put in a queue for processing
        Arguments:
            self: an UserActions datatype      
            data: bytes data from UDP Server      
        Returns:
            None
        """
        self.UdpMessageQueue.put(data)
    def parseUdpMessage(self):
        """
        Function to get UDP data from queue and process it
        Arguments:
            self: an UserActions datatype      
        Returns:
            None
        """
        while True:
            try:
                data = self.UdpMessageQueue.get(timeout=1.8)
                if((data[DoorSensor.HEADER.value] == 0xFF) and (data[DoorSensor.FOOTER.value] == 0xFA) ):
                    if(data[DoorSensor.DATA.value] == 0x00):
                        print("Door Close")
                        self.doorIsOpen = False
                        if(self.isDoorSensorAvailable == False):
                            self.buzzer.setGpioState(GPIO_State.LOW.value)
                            self.isDoorSensorAvailable == True
                    else:
                        print("Door Open")
                        self.doorIsOpen = True
                        if((self.isDoorSensorAvailable == False) and (self.triggered == True)):
                            self.buzzer.setGpioState(GPIO_State.LOW.value)
                            self.isDoorSensorAvailable == True
                        if((self.isArm == True) and (self.triggered == False)):
                            self.intrusionDetectedMessage()
                            self.triggered = True
                self.noAckCount = 0
            except Empty:
                self.noAckCount = self.noAckCount + 1
            except Full:
                size = self.UdpMessageQueue.qsize()
                for i in range(size):
                    self.UdpMessageQueue.get(timeout=0.2)
            except Exception as e:
                print(str(e))
            if(self.noAckCount == 3):
                self.isDoorSensorAvailable = False
                self.buzzer.setGpioState(GPIO_State.HIGH.value)
                message = "Number not registered. Update phone number to continue.\nPhone:<Name>:<Number>\nEx:Phone:Kumar:60123456789\n"
                if(self.number != "" ):
                    message = "Door Sensor Not Available. Alarm Triggered"
                    self.gsmHandler.SendSms(self.number,message)
            

    def getNumberFromDb(self):
        """
        Function to get UDP data from queue and process it
        Arguments:
            self: an UserActions datatype      
        Returns:
            None
        """
        dets = self.db.getUserDetails()
        if(len(dets) > 0):
            self.number = dets[0][0]
    def setIsMessage(self,val):
        """
        Function to set flag if SMS in incoming
        Arguments:
            self: an UserActions datatype   
            val: boolean, true if message is incoming   
        Returns:
            None
        """
        self.isMessage = val
    def parseAtCommand(self,gsmEvent,reGroup):
        """
        Function to process event & data from GSM module
        Arguments:
            self: an UserActions datatype   
            gsmEvent: event enum from GSM module
            reGroup: Regex group with data   
        Returns:
            None
        """
        if(gsmEvent == atReceive.SMS_NOTIFICATION.value):
            print(reGroup.groups())            
            self.rxNumber = reGroup.groups()[messageNotiAT.NUMBER.value]           
            self.isMessage = True
        if((gsmEvent == atReceive.MESSAGES.value) and (self.isMessage == True)):
            print(reGroup)
            self.processUserMessage(reGroup.group(),self.rxNumber)
            self.isMessage = False
    
    def processUserMessage(self,data,rxNumber):
        """
        Function to handle each type of user message
        Arguments:
            self: an UserActions datatype   
            data: message string received from user
            rxNumber: user phone number   
        Returns:
            None
        """
        if(self.number == rxNumber):
            if( "HELP" in data.upper()):
                self.sendHelpMessage()            
            elif("Phone".upper() in data.upper()):
                self.handleUpdateUpdatePhoneNumber(data)
            elif("Sound Alarm".upper() in data.upper()):
                self.soundAlarmAck()
            elif("Off Alarm".upper() in data.upper()):
                self.stopAlarmAck()
            elif("Door Status".upper() in data.upper()):
                self.doorStatusAck()                
            elif("DisArm Alarm".upper() in data.upper()):
                self.alarmArmDiarmAck(False)
            elif("Arm Alarm".upper() in data.upper()):
                self.alarmArmDiarmAck(True)
            else:
                self.gsmHandler.SendSms(self.number,"Invalid input")
        elif((self.number == None) and ("Phone".upper() in data.upper())):
            self.handleUpdateUpdatePhoneNumber(data)
        elif (self.number == None):
            message = "Number not registered. Update phone number to continue.\nPhone:<Name>:<Number>\nEx:Phone:Kumar:60123456789\n"
            self.gsmHandler.SendSms(rxNumber,message)                
    
    def sendHelpMessage(self):
        """
        Function to send Help menu to user
        Arguments:
            self: an UserActions datatype                 
        Returns:
            None
        """
        message = 'MENU\n1. Update Phone Number\n2. Sound Alarm\n3. Door Status\n4. Off Alarm\n5. Arm Alarm\n6. Disarm Alarm'
        self.gsmHandler.SendSms(self.number,message)
    def sendUpdatePhoneNumHelp(self):
        """
        Function to send Update phone number example to user
        Arguments:
            self: an UserActions datatype                 
        Returns:
            None
        """
        message = "Phone:<Name>:<Number>\nEx:Phone:Kumar:60123456789\n"
        self.gsmHandler.SendSms(self.number,message)        
    def soundAlarmAck(self):
        """
        Function to trigger alarm and send ack
        Arguments:
            self: an UserActions datatype                 
        Returns:
            None
        """
        self.buzzer.setGpioState(GPIO_State.HIGH.value)
        message = "Alarm Triggered"
        self.gsmHandler.SendSms(self.number,message)
    def stopAlarmAck(self):
        """
        Function to strop alarm and send ack
        Arguments:
            self: an UserActions datatype                 
        Returns:
            None
        """
        self.triggered = False
        self.buzzer.setGpioState(GPIO_State.LOW.value)
        message = "Alarm Stopped"
        self.gsmHandler.SendSms(self.number,message)
    def alarmArmDiarmAck(self,arm):
        """
        Function to arm alarm and send ack
        Arguments:
            self: an UserActions datatype  
            arm: boolean, arm if true
        Returns:
            None
        """
        if(arm):
            self.isArm = True
            message = "Alarm Armed"
        else:
            self.isArm = False
            message = "Alarm disarmed"
        self.gsmHandler.SendSms(self.number,message)
    def doorStatusAck(self):
        """
        Function to get door status and send to user
        Arguments:
            self: an UserActions datatype              
        Returns:
            None
        """
        if(self.doorIsOpen == True):
            message = "Door Open"
        else:
            message = "Door Closed"
        self.gsmHandler.SendSms(self.number,message)
    def intrusionDetectedMessage(self):
        """
        Function to send instrusion alert to user
        Arguments:
            self: an UserActions datatype              
        Returns:
            None
        """
        self.buzzer.setGpioState(GPIO_State.HIGH.value)
        message = "Intrusion Detected. Alarm Triggered. Send Off Alarm to stop the alarm. Close the door to stop alarm from triggering again"
        self.gsmHandler.SendSms(self.number,message)
    def verifyUpdatePhoneNum(self,data):
        """
        Function to verify user phone number during registration
        Arguments:
            self: an UserActions datatype
            data: user update phone number command              
        Returns:
            None
        """
        ret = False
        userData = data.split(':')
        if(len(userData) == 3):
            name = userData[1]
            number = userData[2]
            try:
                self.db.delAllPhoneNumberFromTable()               
                self.db.insertPhoneNumberTable(name,number)
                ret = True
            except Exception as e:
                print(str(e))
                return ret            
        return ret        
    
    def handleUpdateUpdatePhoneNumber(self,data):
        """
        Function to handle user request to update phone number
        Arguments:
            self: an UserActions datatype
            data: user update phone number command              
        Returns:
            None
        """
        if("Update Phone Number".upper() in data.upper()):
            self.sendUpdatePhoneNumHelp()
        else:
            if(self.verifyUpdatePhoneNum(data) == False):
                self.gsmHandler.SendSms(self.number,"Unable to update phone number\n")
            else:
                self.getNumberFromDb()
                self.gsmHandler.SendSms(self.number,"Phone Number Successfully updated\n")
            
        
if __name__ == "__main__":
    dbConnection = DatabaseConnection("HomeSecurity.db")
    app = UserActions(dbConnection,None,None)
    app.verifyUpdatePhoneNum("Phone:Kumar:60123456789")
