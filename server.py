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
        self.exit = False

    def timeout_reset(self):
        timeout_dict[self] = time()

    def exit_enable(self):
        self.exit = True

    def init_after_login(self, word):
        self.login_require_flag = False
        self.username = word[1]
        login_record[self.username] = time()
        for key in login_dict:
            thread = login_dict[key]
            if isinstance(thread, threading.Thread):
                print(self.username)
                reply = "online " + self.username
                thread.sock.send(reply.encode())
        # print(login_dict[self.username])
            else:
                for reply in login_dict[self.username]:
                    self.sock.send(reply.encode())
        login_dict[self.username] = self

    def login(self):
        while self.login_require_flag:
            self.message = self.sock.recv(1024).decode()
            if self in timeout_dict:
                self.timeout_reset()
            word = self.message.split()
            print(word)
            reply = "wrong"
            if self.login_remain_times == 0:
                reply = "block"
                server_blockdict[self.addr[0]] = time()
                print(server_blockdict)
                self.exit_enable()
            if self.message == "":
                print("connection lost")
                self.exit_enable()
                break
            # print(word[1], credentials.keys())
            if word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    if login_dict[word[1]]:
                        reply = "occupied"
                    else:
                        reply = "welcome"
                        self.init_after_login(word)
            self.sock.send(reply.encode())
            self.login_remain_times -= 1

    def command_parse_and_send(self):
        message_list = self.message.split()
        if len(message_list) == 1:
            if self.message == "logout":
                self.sock.send("logout".encode())
                self.exit_enable()
            if self.message == "whoelse":
                reply = "whoelse"
                for thread in threads:
                    if thread != self:
                        reply += " " + thread.username
                self.sock.send(reply.encode())

        if len(message_list) > 1:
            if message_list[0] == "whoelsesince":
                try:
                    time_since = float(message_list[1])
                    reply = "whoelsesince "+message_list[1]
                    for username in login_record:
                        if not username == self.username:
                            if time() - login_record[username] <= time_since:
                                reply += " " + username
                    self.sock.send(reply.encode())
                except ValueError:
                    self.sock.send("invalidtime".encode())
            if message_list[0] == "broadcast":
                reply = " ".join(message_list)
                for thread in threads:
                    if thread != self:
                        thread.sock.send(reply.encode())
            if message_list[0] == "message":
                name_to_send = message_list[1]
                if name_to_send in login_dict:
                    sentence = " ".join(message_list[2:])
                    reply = "message " + self.username + " " + sentence
                    if isinstance(login_dict[name_to_send], threading.Thread): # Target online case
                        thread = login_dict[name_to_send]
                        thread.sock.send(reply.encode())
                    else:
                        login_dict[name_to_send].append(reply)
                        self.sock.send(("store "+name_to_send).encode())
                else:
                    self.sock.send("inviliduser".encode())

    def thread_exit(self):
        login_dict[self.username] = []
        threads.remove(self)
        self.sock = None
        for thread in threads:
            reply = "offline " + self.username
            thread.sock.send(reply.encode())

    def run(self):
        self.timeout_reset()
        self.login()
        while not self.exit:
            self.message = self.sock.recv(1024).decode()
            print(self.message)
            self.timeout_reset()
            self.command_parse_and_send()
        if (not self.login_require_flag) and self.exit:
            self.thread_exit()

def check_timeout():
    threadtoClose = []
    # print(timeout_dict)
    for thread in timeout_dict.copy():
        time_now = time()
        if time_now - timeout_dict[thread] > TIMEOUT:
            if thread.sock is not None:
                thread.sock.send("timeout".encode())
                threadtoClose.append(thread)
    # print(threadtoClose)
    for thread in threadtoClose:
        del timeout_dict[thread]
        thread.exit = True



def update_serverblockdict():
    iptoRemove = []
    for ip in server_blockdict.copy():
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
login_dict = {username: [] for username in credentials}
serverSocket.listen(5)
print("The server is ready to receive")

server_blockdict = {}
threads = []
sockets = []
timeout_dict = {}
login_record = {}

con_thread = ConnectionThread()
con_thread.start()
prev_time = time()
while True:
    # print(sockets)
    check_timeout()
    cur_time = time()
    if cur_time - prev_time > 1:
        update_serverblockdict()
        prev_time = cur_time
    # print(threading.enumerate())
connectionSocket.close()
for t in threads:
    t.join()
