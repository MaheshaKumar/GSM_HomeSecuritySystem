#!/usr/bin/env python3
import socket
import threading
import time

class UdpServer():
    def __init__(self,ip,port) -> None:
        self.ip = ip
        self.port = port
        self.socket = None
        self.addr = None
    def startServer(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(True)
        self.socket.bind((self.ip, self.port))
        recvThread = threading.Thread(target=self.startRecvThread)
        recvThread.start()
    def startRecvThread(self):
        while True:
            data, self.addr = self.socket.recvfrom(1024)
            print("Server: "+data.decode() + self.addr[0])
            self.sendMessage("Received")

    def sendMessage(self,data):
        self.socket.sendto(data.encode(),self.addr)
class UdpClient():
    def __init__(self,Txip,port) -> None:
        self.Txip = Txip
        self.port = port
        self.addr = None
        self.socket = None
        self.rxStart = False
    def startClient(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(True)
        self.addr = (self.Txip, self.port)
        
    def sendMessage(self,message):
        self.socket.sendto(message.encode(),self.addr)
        if(self.rxStart == False):
            recvThread = threading.Thread(target=self.startRecvThread)
            recvThread.start()
            self.rxStart = True
    def startRecvThread(self):
        while True:
            data ,self.addr = self.socket.recvfrom(1024)
            print("Client: "+data.decode())

if __name__ == "__main__":
    serverIp = "127.0.0.1"
    serverPort = 12000
    serverSock = UdpServer(serverIp,serverPort)
    clientSock = UdpClient(serverIp,serverPort)
    serverSock.startServer()
    clientSock.startClient()
    count = 0
    while True:        
        count = count + 1
        message = "Sending " + str(count)
        clientSock.sendMessage(message)
        time.sleep(2)