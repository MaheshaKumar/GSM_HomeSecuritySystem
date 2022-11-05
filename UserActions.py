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
        self.UdpMessageQueue.put(data)
    def parseUdpMessage(self):
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
        dets = self.db.getUserDetails()
        if(len(dets) > 0):
            self.number = dets[0][0]
    def setIsMessage(self,val):
        self.isMessage = val
    def parseAtCommand(self,gsmEvent,reGroup):
        if(gsmEvent == atReceive.SMS_NOTIFICATION.value):
            print(reGroup.groups())            
            self.rxNumber = reGroup.groups()[messageNotiAT.NUMBER.value]
            # if(self.number == ""):
            #     message = "Number not registered. Update phone number to continue.\nPhone:<Name>:<Number>\nEx:Phone:Kumar:60123456789\n"
            #     self.gsmHandler.SendSms(number,message)
            #     self.isMessage = True
            # elif(self.number == number):
            self.isMessage = True
        if((gsmEvent == atReceive.MESSAGES.value) and (self.isMessage == True)):
            print(reGroup)
            self.processUserMessage(reGroup.group(),self.rxNumber)
            self.isMessage = False
    def processUserMessage(self,data,rxNumber):
        if(self.number == rxNumber):
            if( "HELP" in data.upper()):
                self.sendHelpMessage()
            elif("Alert Time".upper() in data.upper()):
                self.handleUpdateAlertTime(data)
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
        
        
    def getAlertTime(self):
        message = "Alert Times:\n"
        rows = self.db.getAllAlertTime()
        count = 0
        for i in rows:
            count = count + 1
            message = message + "{0}.Start ={1},End = {2}:".format(count,i[AlertTimeEnum.START],i[AlertTimeEnum.END])
            for j in range(Days.MONDAY,Days.DAYS_MAX):
                if(i[AlertTimeEnum.DAYS] & (1 << j)):
                    message = message + "{0},".format(str(j+1))
            message = message +'\n'
            
        self.gsmHandler.SendSms(self.number,message)
    def sendHelpMessage(self):
        message = 'MENU\n1. Update Phone Number\n2. Sound Alarm\n3. Door Status\n4. Off Alarm\n5. Arm Alarm\n6. Disarm Alarm'
        self.gsmHandler.SendSms(self.number,message)
    def sendUpdatePhoneNumHelp(self):
        message = "Phone:<Name>:<Number>\nEx:Phone:Kumar:60123456789\n"
        self.gsmHandler.SendSms(self.number,message)
    def setAlertTimeMainHelp(self):
        message = "1.Set Alert Time\n2.Remove Alert Time\n3.Get Alert Time"
        self.gsmHandler.SendSms(self.number,message)
    def setAlertTimeHelp(self):
        message = '<start_hours>:<end_hours>:<days>\nEx:1000:0600:1,2,3,4,5,6,7\n1-Mon,2-Tue,3,Wed,4-Thurs,5-Fri,6-Sat,7-Sun'
        self.gsmHandler.SendSms(self.number,message)
    def removeAlertTimeHelp(self):
        message = "Choose Alert Time to remove:"
        rows = self.db.getAllAlertTime()
        count = 0
        for i in rows:
            count = count + 1
            message = message + "{0}.Start ={1},End = {2}:".format(count,i[AlertTimeEnum.START],i[AlertTimeEnum.END])
            for j in range(Days.MONDAY,Days.DAYS_MAX):
                if(i[AlertTimeEnum.DAYS] & (1 << j)):
                    message = message + "{0},".format(str(j+1))
            message = message +'\n'
        self.gsmHandler.SendSms(self.number,message)
    def soundAlarmAck(self):
        self.buzzer.setGpioState(GPIO_State.HIGH.value)
        message = "Alarm Triggered"
        self.gsmHandler.SendSms(self.number,message)
    def stopAlarmAck(self):
        self.triggered = False
        self.buzzer.setGpioState(GPIO_State.LOW.value)
        message = "Alarm Stopped"
        self.gsmHandler.SendSms(self.number,message)
    def alarmArmDiarmAck(self,arm):
        if(arm):
            self.isArm = True
            message = "Alarm Armed"
        else:
            self.isArm = False
            message = "Alarm disarmed"
        self.gsmHandler.SendSms(self.number,message)
    def doorStatusAck(self):
        if(self.doorIsOpen == True):
            message = "Door Open"
        else:
            message = "Door Closed"
        self.gsmHandler.SendSms(self.number,message)
    def intrusionDetectedMessage(self):
        self.buzzer.setGpioState(GPIO_State.HIGH.value)
        message = "Intrusion Detected. Alarm Triggered. Send Off Alarm to stop the alarm. Close the door to stop alarm from triggering again"
        self.gsmHandler.SendSms(self.number,message)

    def verifyUpdatePhoneNum(self,data):
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
    def verifyUpdateAlertTime(self,data):
        ret = False
        print(type(data))
        userData = data.split(':')
        if(len(userData) == 3):
            start_time = userData[0]
            end_time = userData[1]
            days = userData[2].split(',')
            daysBit = 0
            try:
                start_timeInt = int(start_time)
                end_timeInt = int(end_time)
                for i in days:
                    day = int(i) - 1                    
                    if day < Days.DAYS_MAX.value:
                        daysBit = daysBit | (1 << (day))
                self.db.delAllAlertFromTable()
                ret = self.db.insertAlertTimeTable(start_time,end_time,daysBit)
            except:
                return ret
        return ret
    def handleUpdateAlertTime(self,data):
        if("Update Alert Time".upper() in data.upper()):
            self.setAlertTimeMainHelp()
        elif("Set Alert Time".upper() in data.upper()):
            self.setAlertTimeHelp()
        elif("Remove Alert Time".upper() in data.upper()):
            self.removeAlertTimeHelp()
        elif("Get Alert Time".upper() in data.upper()):
            self.getAlertTime()      
        else:
            self.gsmHandler.SendSms(self.number,"Invalid input")
    
    def handleUpdateUpdatePhoneNumber(self,data):
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
