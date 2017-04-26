import sys
import threading
from socket import *

serverName = "127.0.0.1"
serverPort = 12000



clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))


class ReceiverThread(threading.Thread):
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
                # self.sock.close()
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
            if self.reply == "partialbroadcast":
                print("Your message could not be delivered to some recipients")
            if self.reply == "beblocked":
                print("Your message could not be delivered as the recipient has blocked you")
        if len(reply_list)>1:
            if reply_list[0] == "online":
                print(reply_list[1]+" logged in")
            if reply_list[0] == "offline":
                print(reply_list[1]+" logged out")
            if reply_list[0] == "whoelse":
                print("Current online user:")
                for user in reply_list[1:]:
                    print(user)
            if reply_list[0] == "whoelsesince":
                for user in reply_list[2:]:
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


    def run(self):
        while not self.exit:
            self.reply = self.sock.recv(1024).decode()
            print(self.reply)
            self.message_parse()
        if self.exit:
            print("close")
            clientSocket.close()

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
        print(answer_login)
        if answer_login == "welcome":
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
            print("Invalid Username. Your account been blocked. Please try again later")
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


login()
thread_rec = ReceiverThread(clientSocket)
thread_rec.start()
exit_flag = []
while not exit_flag:
    message = input()
    if threading.active_count()>1:
        clientSocket.send(message.encode())



