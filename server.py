from time import time
from socket import *
import threading

TIMEOUT = 100
BLOCK_DURATION = 10


class ConnectionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            connectionSocket, addr = serverSocket.accept()
            newthread = ClientThread(connectionSocket)
            newthread.start()
            threads.append(newthread)
            sockets.append(connectionSocket)


class ClientThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        # self.init_time = init_time
        self.login_require_flag = True
        self.login_remain_times = 2
        self.message = ""

    def timeout_reset(self):
        timeout_dict[self.sock] = time()

    def login(self):
        while self.login_require_flag:
            self.message = self.sock.recv(1024).decode()
            self.timeout_reset()
            word = self.message.split()
            print(word)
            reply = "wrong"
            if self.message == "":
                print("connection lost")
                break
            if self.login_remain_times == 0:
                reply = "block"
                # server_blocklist.append([addr[0], time()])
                print(server_blocklist)
            print(word[1], credentials.keys())
            if word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    reply = "welcome"
                    self.login_require_flag = False
            self.sock.send(reply.encode())
            self.login_remain_times -= 1

    def run(self):
        self.timeout_reset()
        self.login()
        while True:
            self.message = self.sock.recv(1024).decode()
            self.timeout_reset()
            self.sock.send(self.message.encode())


def check_timeout():
    socktoclose = []
    for sock in timeout_dict:
        time_now = time()
        if time_now - timeout_dict[sock] > TIMEOUT:
            sock.send("timeout".encode())
            socktoclose.append(sock)
    for sock in socktoclose:
        del timeout_dict[sock]
        sock.close()



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
server_blocklist = []
threads = []
sockets = []
timeout_dict = {}
con_thread = ConnectionThread()
con_thread.start()
while True:
    # print(sockets)
    check_timeout()
    # print(threads)
    # print(addr)
connectionSocket.close()
for t in threads:
    t.join()
