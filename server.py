from time import time
from socket import *
import threading

TIMEOUT = 10
BLOCK_DURATION = 15


class ConnectionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)


    def run(self):
        while True:
            connectionSocket, addr = serverSocket.accept()
            if addr[0] not in server_blockdict:
                newthread = ClientThread(connectionSocket, addr)
                newthread.start()
                threads.append(newthread)
                sockets.append(connectionSocket)
            else:
                connectionSocket.send("block".encode())


class ClientThread(threading.Thread):
    def __init__(self, sock, addr):
        threading.Thread.__init__(self)
        self.sock = sock
        # self.init_time = init_time
        self.login_require_flag = True
        self.login_remain_times = 2
        self.message = None
        self.addr = addr
        self.username = None
        self.reply = []
        self.exit = False

    def timeout_reset(self):
        timeout_dict[self] = time()

    def login(self):
        while self.login_require_flag:
            self.message = self.sock.recv(1024).decode()
            if self.sock in timeout_dict:
                self.timeout_reset()
            word = self.message.split()
            print(word)
            reply = "wrong"
            if self.login_remain_times == 0:
                reply = "block"
                server_blockdict[self.addr[0]]=time()
                print(server_blockdict)
            if self.message == "":
                print("connection lost")
                break
            print(word[1], credentials.keys())
            if word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    reply = "welcome"
                    self.login_require_flag = False
                    self.username = word[1]
            self.sock.send(reply.encode())
            self.login_remain_times -= 1

    def run(self):
        self.timeout_reset()
        self.login()
        while not self.exit:
            self.message = self.sock.recv(1024).decode()
            if self.message!="":
                self.timeout_reset()
            self.sock.send(self.message.encode())


def check_timeout():
    threadtoClose = []
    # print(timeout_dict)
    for thread in timeout_dict:
        time_now = time()
        if time_now - timeout_dict[thread] > TIMEOUT:
            thread.sock.send("timeout".encode())
            threadtoClose.append(thread)
    # print(threadtoClose)
    for thread in threadtoClose:
        del timeout_dict[thread]
        thread.exit = True


def update_serverblockdict():
    iptoRemove = []
    for ip in server_blockdict:
        time_now = time()
        if time_now - server_blockdict[ip] > BLOCK_DURATION:
            iptoRemove.append(ip)
    for ip in iptoRemove:
        del server_blockdict[ip]



serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
credentials = {}
with open("credentials.txt") as file:
    for line in file:
        word = line.split()
        credentials[word[0]] = word[1]
serverSocket.listen(5)
print("The server is ready to receive")

server_blockdict = {}
threads = []
sockets = []
timeout_dict = {}


con_thread = ConnectionThread()
con_thread.start()
prev_time= time()
while True:
    # print(sockets)
    check_timeout()
    cur_time = time()
    if cur_time-prev_time>1:
        update_serverblockdict()
        prev_time = cur_time
    # print(threading.enumerate())
connectionSocket.close()
for t in threads:
    t.join()
