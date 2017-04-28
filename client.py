import sys
import threading
from socket import *

serverName = sys.argv[1]
serverPort = int(sys.argv[2])



clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
p2pConnectionSocket = socket(AF_INET, SOCK_STREAM)
p2pConnectionSocket.bind(('',0))
p2pPort = p2pConnectionSocket.getsockname()[1]

class ServerReceiverThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.reply = None
        self.exit = False

    def message_parse(self):
        reply_list = self.reply.split()
        if len(reply_list)==1:
            if self.reply == "timeout":
                print("Times out! Exit the program.")
                exit_flag.append(1)
                self.exit = True

            if self.reply == "logout":
                exit_flag.append(1)
                self.exit = True
            if self.reply == "invalidtime":
                print("Error. Invalid time")
            if self.reply == "inviliduser":
                print("Error. Invalid user")
            if self.reply == "blockself":
                print("Error. Cannot block self")
            if self.reply == "unblockself":
                print("Error. Cannot unblock self")
            if self.reply == "partialbroadcast":
                print("Your message could not be delivered to some recipients")
            if self.reply == "beblocked":
                print("Your message could not be delivered as the recipient has blocked you")
            if self.reply == "privateself":
                print("Error. Cannot private self")
            if self.reply == "invilidcommand":
                print("Error. Invilid command")
        if len(reply_list)>1:
            if reply_list[0] == "online":
                print(reply_list[1]+" logged in")
            if reply_list[0] == "offline":
                print(reply_list[1]+" logged out")
            if reply_list[0] == "whoelse":
                for user in reply_list[1:]:
                    print(user)
            if reply_list[0] == "whoelsesince":
                for user in reply_list[1:]:
                    print(user)
            if reply_list[0] == "message":
                print("{}: {}".format(reply_list[1], " ".join(reply_list[2:])))
            if reply_list[0] == "store":
                print("{} is offline now. Your message has been stored".format(reply_list[1]))
            if reply_list[0] == "block":
                print(reply_list[1]+" is blocked")
            if reply_list[0] == "unblock":
                print(reply_list[1]+" is unblocked")
            if reply_list[0] == "unblockerror":
                print("Error. {} was not blocked".format(reply_list[1]))
            if reply_list[0] == "privateoffline":
                print("Error. {} is currently offline. Cannot start private".format(reply_list[1]))
            if reply_list[0] == "startprivate":
                print(self.reply)
                p2p_sendto_username = reply_list[1]
                p2p_sendto_addr = eval(reply_list[2])
                p2p_rec_thread = P2PReceiverThread(p2p_sendto_username,p2p_sendto_addr,None)
                p2p_rec_thread.start()
                print("Start private messaging with {}".format(p2p_sendto_username))
                p2p_rec_threads.append(p2p_rec_thread)
                p2p_connected_user[p2p_sendto_username] = p2p_rec_thread

    def run(self):
        while not self.exit:
            self.reply = self.sock.recv(1024).decode()
            self.message_parse()
        if self.exit:
            clientSocket.close()


class P2PReceiverThread(threading.Thread):
    def __init__(self, username, addr, sock):
        threading.Thread.__init__(self)
        self.username = username
        self.addr = addr
        self.exit = False
        if username is not None:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(self.addr)
            self.sock.send(("p2pname "+myName).encode())
        else:
            self.sock = sock

    def run(self):
        while not self.exit:
            reply = self.sock.recv(1024).decode()
            reply_list = reply.split()
            if len(reply_list):
                if reply_list[0]=="p2pname":
                    self.username = reply_list[1]
                    p2p_connected_user[self.username] = self
                elif reply_list[0]=="private":
                    print("{}(private): {}".format(self.username," ".join(reply_list[1:])))
                elif reply_list[0]=="stopprivate":
                    print("{} canceled private message with you".format(self.username))
                    self.exit = True
        p2p_rec_threads.remove(self)
        del p2p_connected_user[self.username]
        self.sock.close()


class P2PConnectionThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock
        self.sock.listen(10)
        self.exit = False

    def run(self):
        while not self.exit:
            connectionSocket, addr = self.sock.accept()
            newthread = P2PReceiverThread(None, addr, connectionSocket)
            newthread.start()
            p2p_rec_threads.append(newthread)


def login():
    login_flag = True
    username_flag = True
    while login_flag:
        while username_flag:
            username = input("username:")
            if username != "":
                break
            print("Empty username. Please try again.")
        while True:
            password = input("password:")
            if password != "":
                break
            print("Empty password. Please try again.")

        clientSocket.send(('login ' + username + ' ' + password).encode())
        answer_login = clientSocket.recv(1024).decode()
        if answer_login == "welcome":
            clientSocket.send("p2p {}".format(p2pPort).encode())
            print("Welcome to the greatest messaging application ever!")
            login_flag = False
        if answer_login == "timeout":
            print("Times out! Exit the program.")
            clientSocket.close()
            sys.exit()
        if answer_login == "block":
            print("Invalid Username and Password. Your IP been blocked. Please try again later")
            clientSocket.close()
            sys.exit()
        if answer_login == "blockun":
            print("Your username is blocked due to multiple login failures. Please try again later")
            clientSocket.close()
            sys.exit()
        if answer_login == "blockip":
            print("Your IP is blocked due to multiple login failures. Please try again later")
            clientSocket.close()
            sys.exit()
        if answer_login == "falsep":
            username_flag = False
            print("Invalid Password. Please try again")
        if answer_login == "false":
            print("Invalid Username and Password. Please try again")
        if answer_login == "occupied":
            print("This username has already logged in! Please retry.")
    return username
p2p_rec_threads = []
p2p_connected_user = {}
myName = login()
thread_server_rec = ServerReceiverThread(clientSocket)
thread_p2p_connection = P2PConnectionThread(p2pConnectionSocket)
thread_p2p_connection.daemon = True
thread_server_rec.start()
thread_p2p_connection.start()
exit_flag = []
while not exit_flag:
    message = input()
    message_list = message.split()
    if len(message_list):
        if message_list[0] == "private":
            private_username = message_list[1]
            if private_username in p2p_connected_user:
                p2p_connected_user[private_username].sock.send("private {}".format(" ".join(message_list[2:])).encode())
            else:
                print("Error. Private messaging to {} not enabled".format(private_username))
        elif message_list[0] == "stopprivate":
            stopprivate_username = message_list[1]
            if stopprivate_username in p2p_connected_user:
                thread=p2p_connected_user[stopprivate_username]
                thread.sock.send("stopprivate".encode())
                thread.exit = True
                print("Private messaging to {} stopped".format(stopprivate_username))
            else:
                print("Error. Not exist an active p2p messaging session with {}".format(stopprivate_username))
        elif message_list[0]== "startprivate":
            if message_list[1] in p2p_connected_user:
                print("Error. Private connection already exits")
            else:
                clientSocket.send(message.encode())
        else:
            if isinstance(thread_server_rec, threading.Thread):
                clientSocket.send(message.encode())
for thread in p2p_rec_threads:
        thread.sock.send("stopprivate".encode())
        thread.exit = True





