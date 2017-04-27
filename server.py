import sys
from time import time
from socket import *
import threading

serverPort = int(sys.argv[1])
BLOCK_DURATION = int(sys.argv[2])
TIMEOUT = int(sys.argv[3])



class ConnectionThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            connectionSocket, addr = serverSocket.accept()
            if addr[0] not in ip_blockdict:
                newthread = ClientThread(connectionSocket, addr)
                newthread.start()
                threads.append(newthread)
            else:
                connectionSocket.send("blockip".encode())


class ClientThread(threading.Thread):
    def __init__(self, sock, addr):
        threading.Thread.__init__(self)
        self.sock = sock
        self.login_require_flag = True
        self.login_remain_times = 2
        self.message = None
        self.addr = addr
        self.username = None
        self.exit = False
        self.blocked_user = []
        self.p2paddr = None

    def timeout_reset(self):
        timeout_dict[self] = time()

    def exit_enable(self):
        self.exit = True

    def init_after_login(self, word):
        self.login_require_flag = False
        self.username = word[1]
        login_record[self.username] = time()

    def show_presence(self):
        for key in login_dict:
            thread = login_dict[key]
            if isinstance(thread, threading.Thread):
                if key not in self.blocked_user:
                    reply = "online " + self.username
                    thread.sock.send(reply.encode())

    def send_stored_message(self):
        for reply in login_dict[self.username]:
            self.sock.send(reply.encode())
        login_dict[self.username] = self

    def login(self):
        while self.login_require_flag:
            self.message = self.sock.recv(1024).decode()
            username_flag = False
            self.timeout_reset()
            word = self.message.split()
            reply = "false"
            if self.message == "":
                self.exit_enable()
                break
            elif word[1] in username_blockdict:
                reply = "blockun"
            elif word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    if isinstance(login_dict[word[1]],threading.Thread):
                        reply = "occupied"
                    else:
                        reply = "welcome"
                        self.init_after_login(word)
                        self.login_remain_times+=1
                else:
                    reply = "falsep"
                    username_flag = True
            if self.login_remain_times == 0:
                reply = "block"
                ip_blockdict[self.addr[0]] = time()
                if username_flag:
                    username_blockdict[word[1]] = time()
                self.exit_enable()
            self.sock.send(reply.encode())
            self.login_remain_times -= 1

    def command_parse_and_send(self):
        message_list = self.message.split()

        if len(message_list) == 1:
            if self.message == "logout":
                self.sock.send("logout".encode())
                self.exit_enable()
            elif self.message == "whoelse":
                reply = "whoelse"
                for thread in threads:
                    if thread != self:
                        reply += " " + thread.username
                self.sock.send(reply.encode())
            else:
                self.sock.send("invilidcommand".encode())
        elif len(message_list) > 1:
            if message_list[0] == "p2p":
                self.p2paddr = (self.addr[0],int(message_list[1]))
            elif message_list[0] == "whoelsesince":
                try:
                    time_since = float(message_list[1])
                    reply = "whoelsesince"
                    for username in login_record:
                        if not username == self.username:
                            if time() - login_record[username] <= time_since:
                                reply += " " + username
                    self.sock.send(reply.encode())
                except ValueError:
                    self.sock.send("invalidtime".encode())

            elif message_list[0] == "broadcast":
                reply = "message "+self.username+" "+" ".join(message_list[1:])
                all_broadcast_flag = True
                for thread in threads:
                    if thread!=self:
                        if self.username not in thread.blocked_user:
                            thread.sock.send(reply.encode())
                        else:
                            all_broadcast_flag *= False
                if not all_broadcast_flag:
                    self.sock.send("partialbroadcast".encode())

            elif message_list[0] == "message":
                name_to_send = message_list[1]
                if name_to_send in login_dict:
                    sentence = " ".join(message_list[2:])
                    reply = "message " + self.username + " " + sentence
                    if isinstance(login_dict[name_to_send], threading.Thread):  # Target online case
                        thread = login_dict[name_to_send]
                        if self.username not in thread.blocked_user:
                            thread.sock.send(reply.encode())
                        else:
                            self.sock.send("beblocked".encode())
                    else:
                        login_dict[name_to_send].append(reply)
                        self.sock.send(("store " + name_to_send).encode())
                else:
                    self.sock.send("inviliduser".encode())

            elif message_list[0] == "block":
                user_to_block = message_list[1]
                if user_to_block in login_dict:
                    if user_to_block != self.username:
                        self.blocked_user.append(user_to_block)
                        self.sock.send("block {}".format(user_to_block).encode())
                    else:
                        self.sock.send("blockself".encode())
                else:
                    self.sock.send("inviliduser".encode())

            elif message_list[0] == "unblock":
                user_to_unblock = message_list[1]
                if user_to_unblock not in self.blocked_user:
                    if user_to_unblock == self.username:
                        self.sock.send("unblockself".encode())
                    elif user_to_unblock in login_dict:
                        self.sock.send("unblockerror {}".format(user_to_unblock).encode())
                    else:
                        self.sock.send("inviliduser".encode())
                else:
                    self.blocked_user.remove(user_to_unblock)
                    self.sock.send("unblock {}".format(user_to_unblock).encode())

            elif message_list[0] == "startprivate":
                p2p_username = message_list[1]
                if p2p_username in login_dict:
                    if isinstance(login_dict[p2p_username], threading.Thread):
                        thread = login_dict[p2p_username]
                        if p2p_username != self.username:
                            if self.username not in thread.blocked_user:
                                reply = "startprivate {} ('{}',{})".format(thread.username,thread.p2paddr[0],thread.p2paddr[1])
                                self.sock.send(reply.encode())
                            else:
                                self.sock.send("beblocked".encode())
                        else:
                            self.sock.send("privateself".encode())
                    else:
                        self.sock.send("privateoffline {}".format(p2p_username).encode())
                else:
                    self.sock.send("inviliduser".encode())
            else:
                self.sock.send("invilidcommand".encode())

    def thread_exit(self):
        login_dict[self.username] = []
        threads.remove(self)
        self.sock = None
        for thread in threads:
            if thread.username not in self.blocked_user:
                reply = "offline " + self.username
                thread.sock.send(reply.encode())

    def run(self):
        self.timeout_reset()
        self.login()
        if not self.login_require_flag:
            self.show_presence()
            self.send_stored_message()
            while not self.exit:
                self.message = self.sock.recv(1024).decode()
                self.timeout_reset()
                self.command_parse_and_send()
            if self.exit:
                self.thread_exit()

def check_timeout():
    threadtoClose = []
    for thread in timeout_dict.copy():
        time_now = time()
        if time_now - timeout_dict[thread] > TIMEOUT:
            if thread.sock is not None:
                thread.sock.send("timeout".encode())
                threadtoClose.append(thread)
    for thread in threadtoClose:
        del timeout_dict[thread]
        thread.exit = True


def update_usernameblockdict():
    usernametoRemove = []
    for username in username_blockdict:
        time_now = time()
        if time_now - username_blockdict[username] > BLOCK_DURATION:
            usernametoRemove.append(username)
    for username in usernametoRemove:
        del username_blockdict[username]

def update_ipblockdict():
    iptoRemove = []
    for ip in ip_blockdict:
        time_now = time()
        if time_now - ip_blockdict[ip] > BLOCK_DURATION:
            iptoRemove.append(ip)
    for ip in iptoRemove:
        del ip_blockdict[ip]



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

ip_blockdict = {}
username_blockdict = {}
threads = []
timeout_dict = {}
login_record = {}

con_thread = ConnectionThread()
con_thread.start()
prev_time = time()
while True:
    check_timeout()
    cur_time = time()
    if cur_time - prev_time > 1:
        update_ipblockdict()
        update_usernameblockdict()
        prev_time = cur_time
connectionSocket.close()
for t in threads:
    t.join()
