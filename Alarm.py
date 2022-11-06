#!/usr/bin/env python3
from threading import Timer
import time
from datetime import datetime
from DatabaseHandler import DatabaseConnection
from Event import Event
from enum import auto,IntEnum
class Days(IntEnum):
    MONDAY = 1
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()
    DAYS_MAX = auto()
class Alarm():
    def __init__(self,dbConnection) -> None:
        self.dbConnection = dbConnection
        self.arm = False
        self.day = None
        self.alert_time = self.getAlertTime()
        self.isArmed = False
        self.onDayUpdate = Event()
        self.onArmDisarm = Event()
        self.dayChangeTimer = None
        self.alarmTimer = None
        self.startAlarmTimer = None
        self.isAlarmSet = False
        self.notToday = True
    def initAlarm(self):
        self.updateDay()        
        currentTime = self.getCurrentTime()
        dayEnd = "0000"
        delta = self.getTimeDeltainSecs(currentTime,dayEnd)
        self.dayChangeTimer = Timer(delta,self.initAlarm)
        self.dayChangeTimer.start()
        days = self.alert_time[0][2]
        if(days & (1 << (self.day ))):
            self.notToday = False
        else:
            self.notToday = True
        self.setAlarm()

    

    def AddSubscribersDayUpdate(self,objMethod):
        self.onDayUpdate += objMethod
    def AddSubscribersArmDisarmUpdate(self,objMethod):
        self.onArmDisarm += objMethod
		  
    def setAlarm(self):
        currentTime = self.getCurrentTime()
        self.getAlertTime()
        start = self.alert_time[0][0]
        end = self.alert_time[0][1]
        # delta_secs = self.getTimeDeltainSecs(currentTime,start)
        # print(delta_secs)
        if(self.notToday == False):
            if(self.isAlarmSet == False):
                if((self.isTimePast(currentTime,start) == True) and (self.isTimePast(currentTime,end)) == False):                    
                    delta = self.getTimeDeltainSecs(self.getCurrentTime(),end)
                    self.alarmTimer = Timer(delta,self.stopAlarm)
                    self.alarmTimer.start()
                elif((self.isTimePast(currentTime,start) == False)):
                    delta = self.getTimeDeltainSecs(self.getCurrentTime(),start)
                    self.startAlarmTimer = Timer(delta,self.setAlarm)
                    self.startAlarmTimer.start()            


    def stopAlarm(self):
        print("Alrm Stoped")
        self.isAlarmSet = False
        self.armAlarm(False)
        self.setAlarm()
    def startAlarm(self):
        self.getAlertTime()
        start = self.alert_time[0][0]
        end = self.alert_time[0][1]
        delta_secs = self.getTimeDeltainSecs(start,end)
        print(delta_secs)
        self.armAlarm(True)
        self.isAlarmSet = True
        self.alarmTimer = Timer(delta_secs,self.stopAlarm)
        self.alarmTimer.start()
    def isTimePast(self,start,end):
        t1_start = datetime.strptime(start, "%H%M")
        t2_end = datetime.strptime(end, "%H%M")
        if(t1_start >= t2_end):
            return True
        else:
            return False
    def armAlarm(self,val):        
            self.isArmed = val
            self.onArmDisarm(val)  
    
    def updateDay(self):
        self.day = self.getDay()
        self.onDayUpdate(self.day)

    def getAlertTime(self):
        alert_time = self.dbConnection.getAllAlertTime()
        return alert_time
    def getCurrentTime(self):
        return time.strftime("%H%M")
    def getDay(self):
        return datetime.today().weekday()
    def getTimeDeltainSecs(self,start,end):
        t1_start = datetime.strptime(start, "%H%M")
        t2_end = datetime.strptime(end, "%H%M")
        
        t3 = t2_end - t1_start
        secs = 0
        if(t1_start >= t2_end):
            secs = t3.total_seconds() + (24*60*60)
        else:
            secs = t3.total_seconds()
        return secs
    def cancelTimers(self):
        self.alarmTimer.cancel()
        self.dayChangeTimer.cancel()
        self.startAlarmTimer.cancel()
if __name__ == "__main__":
    db = DatabaseConnection("HomeSecurity.db")
    alarm = Alarm(db)
    alarm.initAlarm()
    
