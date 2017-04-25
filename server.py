from time import time
from socket import *
import threading

class ClientThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        # self.init_time = init_time
        self.login_require_flag = True
        self.login_remain_times = 2
        self.message = ""

    def login(self):
        while self.login_require_flag:
            self.message = connectionSocket.recv(1024).decode()
            word = self.message.split()
            print(word)
            reply = "wrong"
            if self.message == "":
                print("connection lost")
                break
            if self.login_remain_times == 0:
                reply = "block"
                server_blocklist.append([addr[0], time()])
                print(server_blocklist)
            print(word[1], credentials.keys())
            if word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    reply = "welcome"
                    self.login_require_flag = False
            connectionSocket.send(reply.encode())
            self.login_remain_times -= 1

    def run(self):
        # connectionSocket, addr = self.sock.accept()
        self.login()
        while True:
            self.message=self.sock.recv(1024).decode()
            self.sock.send(self.message.encode())



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
server_blocklist =[]
threads=[]



while True:
    connectionSocket, addr = serverSocket.accept()
    newthread = ClientThread(connectionSocket)
    newthread.start()
    threads.append(newthread)
    # print(addr)
connectionSocket.close()
for t in threads:
    t.join()

