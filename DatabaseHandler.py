#!/usr/bin/env python3
import sqlite3
from sqlite3 import Error
from enum import IntEnum,auto
class AlertTimeEnum(IntEnum):
    START = 0
    END = auto()
    DAYS = auto()
class DatabaseConnection:
    def __init__(self,dbFilePath):
        self.dbPath = dbFilePath                
        self.conn = self.create_connection(self.dbPath)
        self.createTables()
    def create_connection(self,db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file,check_same_thread=False)
            return conn
        except Error as e:
            print(e)              
    def createTables(self):
        sql_create_phone_numer_table = 'CREATE TABLE IF NOT EXISTS PhoneNumber (number text PRIMARY KEY,name text NOT NULL);'
        
        sql_create_alert_time_table  = 'CREATE TABLE IF NOT EXISTS AlertTime (start_time text NOT NULL PRIMARY KEY,end_time text NOT NULL,days int);'
        if self.conn != None:        
            self.conn.execute(sql_create_phone_numer_table)
            self.conn.execute(sql_create_alert_time_table)
    def insertPhoneNumberTable(self,name,number):
        sql = ''' INSERT INTO PhoneNumber(number,name)
              VALUES(?,?) '''
        row = (number,name)
        if self.conn != None:        
            self.conn.execute(sql,row)
            self.conn.commit()
    def updatePhoneNumberTable(self,name,number):
        sql = ''' UPDATE PhoneNumber SET name = ? WHERE number = ? '''
        row = (name,number)
        if self.conn != None:        
            self.conn.execute(sql,row)
            self.conn.commit()
    def delFromPhoneNumberTable(self,number):
        sql = ''' DELETE FROM PhoneNumber WHERE number = ? '''
        row = (number,)
        if self.conn != None:        
            self.conn.execute(sql,row)
            self.conn.commit()
    def delAllPhoneNumberFromTable(self):
        sql = ''' DELETE FROM PhoneNumber'''        
        if self.conn != None:        
            self.conn.execute(sql)
            self.conn.commit()
    def insertAlertTimeTable(self,start,end,days):
        ret = False
        sql = ''' INSERT INTO AlertTime(start_time,end_time,days)
              VALUES(?,?,?) '''
        row = (start,end,str(days))
        if self.conn != None:        
            self.conn.execute(sql,row)
            self.conn.commit()
            ret = True
        return ret
            
    # def updateAlertTimeTable(self,start,end,days):
    #     sql = ''' UPDATE AlertTime SET start_time = ?, end_time = ?, days = ? WHERE start_time = ? AND end_time = ?'''
    #     row = (start,end,str(days),,)
    #     if self.conn != None:        
    #         self.conn.execute(sql,row)
    #         self.conn.commit()
    def deleteAlertTimeTable(self,start,end):
        sql = ''' DELETE FROM AlertTime WHERE start_time = ? AND end_time = ?'''
        row = (start,end)
        if self.conn != None:        
            self.conn.execute(sql,row)
            self.conn.commit()
    def getAllAlertTime(self):
        sql = '''SELECT * FROM AlertTime '''
        
        if self.conn != None: 
            cur = self.conn.cursor()       
            cur.execute(sql)
            rows = cur.fetchall()
            return rows
    def delAllAlertFromTable(self):
        sql = ''' DELETE FROM AlertTime'''        
        if self.conn != None:        
            self.conn.execute(sql)
            self.conn.commit()
    def getUserDetails(self):
        sql = '''SELECT * FROM PhoneNumber '''
        
        if self.conn != None: 
            cur = self.conn.cursor()       
            cur.execute(sql)
            rows = cur.fetchall()
            return rows

    def dbClose(self):
        self.conn.close()
    

if __name__ == '__main__':
    db = DatabaseConnection("HomeSecurity.db")
    #db.create_connection("HomeSecurity.db")
    db.createTables()
    try:
        rows = db.getAllAlertTime()
        for i in rows:
            print("Start {0}, end {1}, days {2}".format(i[AlertTimeEnum.START],i[AlertTimeEnum.END],i[AlertTimeEnum.DAYS]))
    except Exception as e:
        print(str(e))
    #db.delAllPhoneNumberFromTable()
    #db.insertAlertTimeTable(1305,1405,7)
    db.dbClose()