#Simple TCP Server v0.2
#Jacob Quick - 07/19/2016
##VERSION NOTES: This is a simple, bare bones server script using multiple threads to handle
##incoming connections from multiple clients. The basic idea is that the handler class will accept
##an incoming connection, then pass the client socket object to the queue where the processor
##threads will handle the data. This way, multiple requests from different clients can be handled
##on a FIFO basis.

import queue
import threading
import time
import random
import sys
import socket
import commands

#Handler class will accept and route client socket objects (client) to the queue (q),
#listening on the server socket (server). Also, the Handler will log connections/disconnections
#in a specified text file.

class Handler(threading.Thread):

    def __init__(self, q, server, logfile):

        self.client = None
        self.clientInfo = None
        self.logfile = logfile
        self.server = server
        self.q = q
        threading.Thread.__init__(self)

    def run(self):

        while True:
            self.client, self.clientInfo = self.server.accept()
            self.q.put(self.client)
            self.log()

    def log(self):
        f = open(self.logfile, 'a')
        localtime = time.asctime(time.localtime(time.time()))
        f.write("{} -- Connection established to {}, port {}. Placed in process queue.".format(localtime, str(self.clientInfo[0]), str(self.clientInfo[1])))
        f.write("\n")
        f.close()
        
##processor class will take client socket objects out of the queue, read their data, process it,
##and then log the interaction.

class Processor(threading.Thread):

    def __init__(self, q, logfile, flag):
        self.client = None
        self.q = q
        self.logfile = logfile
        self.pName = "Processor-1"
        self.data = None
        threading.Thread.__init__(self)
        self.sdFlag = flag

    def run(self):
        flag = True
        while flag:
            if self.q.empty():
                print("Waiting for queue...")
                time.sleep(3)
            else:
                print("{} pulling from queue...".format(self.pName))
                self.client = self.q.get()
                self.data = self.client.recv(10).decode("UTF-8")
                res = self.process()
                self.q.task_done()
                flag = (self.log(res))
                self.client = None
                self.data = None

        print("Server Shutting Down.")
        
            

    def process(self):
        data = self.data.upper()
        if data == "ARDUINO":
            #commands.arduino(self.client)  ---- will call from future commands module
            return 1
        elif data == "SERVER":
            #commands.server(self.client)  ---- will call from future commands module
            return 2
        elif data == "SHUTDOWN":
            self.sdFlag.set()
            return 3
        else:
            print("Command Unrecognized")
            return 4

    def log(self, res):
        f = open(self.logfile, 'a')
        localtime = time.asctime(time.localtime(time.time()))
        if res == 1:
            f.write("{} received command {}, sent to arduino.\n".format(self.pName, self.data))
            f.close()
            return True
        elif res == 2:
            f.write("{} received command {}, ran server config.\n".format(self.pName, self.data))
            f.close()
            return True
        elif res == 3:
            f.write("{} received command {}, began system shutdown.\n".format(self.pName, self.data))
            f.close()
            return False
        else:
            f.write("{} received command {}, unrecognized command.\n".format(self.pName, self.data))
            f.close()
            return True
        
        
##Main Thread
##Assign LogFile names

serverLog = "ServerLog.txt"
procLog = "ProcessLog.txt"

##Create Shutdown Flag

sdFlag = threading.Event()

##Create thread list

activeThreads = []

##Create main queue (max size arbitrarily set at 10 to prevent overfilling in error)

mainq = queue.Queue(10)

##Initialize and set up a listener socket, a handler thread, and a processor thread
print("Server Starting...")
addr = socket.gethostbyname(socket.getfqdn())
port = 44444
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((addr, port))



processor = Processor(mainq, procLog, sdFlag)
processor.start()

activeThreads.append(processor)

print("Processor ready...")
s.listen(5)
print("Listener starting at {} on port {}".format(addr, port))
handler = Handler(mainq, s, serverLog)
handler.start()

activeThreads.append(handler)

while True:
    if sdFlag.is_set():
        f = open("ServerLog.txt", "a")
        lt = time.asctime(time.localtime(time.time()))
        f.write("==========SERVER SHUTDOWN: {}=========".format(lt))
        f.close()
        sys.exit()
        
        
