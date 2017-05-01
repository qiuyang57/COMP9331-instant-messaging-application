import sys
from time import time
from socket import *
import threading

serverPort = int(sys.argv[1])
BLOCK_DURATION = int(sys.argv[2])
TIMEOUT = int(sys.argv[3])


# The ConnectionThread runs for accepting the connection from clients
# Create a new thread per new client
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

# Each ClientThread runs for receiving requests from one single client
# and parsing the request and send the label and message to the correct user
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

    # reset the time record in timeout dict
    def timeout_reset(self):
        timeout_dict[self] = time()

    # enable the exit from loop
    def exit_enable(self):
        self.exit = True

    # update some data after login
    def init_after_login(self, word):
        self.login_require_flag = False
        self.username = word[1]
        login_record[self.username] = time()

    # send presence message to all unblocked user
    def show_presence(self):
        for key in login_dict:
            thread = login_dict[key]
            if isinstance(thread, threading.Thread):
                if key not in self.blocked_user:
                    reply = "online " + self.username
                    thread.sock.send(reply.encode())

    # send the offline stored message
    def send_stored_message(self):
        for reply in login_dict[self.username]:
            self.sock.send(reply.encode())
        login_dict[self.username] = self

    # deal with client login request
    def login(self):
        while self.login_require_flag:
            self.message = self.sock.recv(1024).decode()
            username_flag = False
            self.timeout_reset()
            word = self.message.split()
            reply = "false"                      # wrong username and password
            if self.message == "":
                self.exit_enable()
                break
            elif word[1] in username_blockdict:
                reply = "blockun"       # username is blocked
            elif word[1] in credentials.keys():
                if credentials[word[1]] == word[2]:
                    if isinstance(login_dict[word[1]],threading.Thread):
                        reply = "occupied"      # this username has already logged in
                    else:
                        reply = "welcome"       # user authentication succeeded
                        self.init_after_login(word)
                        self.login_remain_times+=1
                else:
                    reply = "falsep"            # username is right but password is wrong
                    username_flag = True
            if self.login_remain_times == 0:
                reply = "block"                 # you have been blocked by server
                ip_blockdict[self.addr[0]] = time()
                if username_flag:
                    username_blockdict[word[1]] = time()
                self.exit_enable()
            self.sock.send(reply.encode())
            self.login_remain_times -= 1

    # parsing the request and send the message with labels to right user
    def command_parse_and_send(self):
        message_list = self.message.split()

        if len(message_list) == 1:
            if self.message == "logout":            # user request: "logout"
                self.sock.send("logout".encode())   # server response: "logout"
                self.exit_enable()
            elif self.message == "whoelse":         # user request: "whoelse"
                reply = "whoelse"                   # server response: "whoelse user1 user2 ..." or "invilidcommand"
                for thread in threads:
                    if thread != self:
                        reply += " " + thread.username
                self.sock.send(reply.encode())
            else:
                self.sock.send("invilidcommand".encode())
        elif len(message_list) > 1:
            # user request for updating their ip address used for p2p connection
            if message_list[0] == "p2p":                        # no response
                self.p2paddr = (self.addr[0],int(message_list[1]))
            elif message_list[0] == "whoelsesince":         # request: "whoelsesince time"
                try:                                        # response: "whoelsesince user1 user2 ..." or "invilidtime"
                    time_since = float(message_list[1])
                    reply = "whoelsesince"
                    for username in login_record:
                        if not username == self.username:
                            if time() - login_record[username] <= time_since:
                                reply += " " + username
                    self.sock.send(reply.encode())
                except ValueError:
                    self.sock.send("invalidtime".encode())

            elif message_list[0] == "broadcast":        # request: "broadcast message"
                reply = "message "+self.username+" "+" ".join(message_list[1:])
                all_broadcast_flag = True                                           # response to all other user:
                for thread in threads:                                              # "message sender message"
                    if thread!=self:
                        if self.username not in thread.blocked_user:
                            thread.sock.send(reply.encode())
                        else:
                            all_broadcast_flag *= False
                if not all_broadcast_flag:                       # if blocked by some user
                    self.sock.send("partialbroadcast".encode())     # response to user: "partialbroadcast"

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

    # release and reset some resource before thread exits
    def thread_exit(self):
        login_dict[self.username] = []
        threads.remove(self)
        self.sock = None
        for thread in threads:
            if thread.username not in self.blocked_user:
                reply = "offline " + self.username
                thread.sock.send(reply.encode())

    def run(self):
        self.timeout_reset()                # init timeout for current user
        self.login()                        # current user login
        if not self.login_require_flag:
            self.show_presence()            # show presence for current user
            self.send_stored_message()      # show stored offline message
            while not self.exit:            # thread main loop with exit condition
                self.message = self.sock.recv(1024).decode()
                self.timeout_reset()        # reset the timeout after receive the message from socket
                self.command_parse_and_send()   # parse and execution
            if self.exit:
                self.thread_exit()          # release thread resource


def check_timeout():                        # check timeout, set exit flag when timeout
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


def update_usernameblockdict():             # update username block dictionary when time longer than BLOCK_DURATION
    usernametoRemove = []
    for username in username_blockdict:
        time_now = time()
        if time_now - username_blockdict[username] > BLOCK_DURATION:
            usernametoRemove.append(username)
    for username in usernametoRemove:
        del username_blockdict[username]


def update_ipblockdict():                   # update ip block dictionary when time longer than BLOCK_DURATION
    iptoRemove = []
    for ip in ip_blockdict:
        time_now = time()
        if time_now - ip_blockdict[ip] > BLOCK_DURATION:
            iptoRemove.append(ip)
    for ip in iptoRemove:
        del ip_blockdict[ip]


# open credentials file and save the data in dict
credentials = {}
with open("credentials.txt") as file:
    for line in file:
        word = line.split()
        credentials[word[0]] = word[1]
login_dict = {username: [] for username in credentials}

# socket init and bind
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(10)
print("The server is ready to receive")

ip_blockdict = {}
username_blockdict = {}
threads = []
timeout_dict = {}
login_record = {}

# thread for user connection
con_thread = ConnectionThread()
con_thread.start()
prev_time = time()

# main loop in main thread
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
