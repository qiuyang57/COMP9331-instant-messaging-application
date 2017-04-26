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

    def run(self):
        while not self.exit:
            self.reply = self.sock.recv(1024).decode()
            print(self.reply)
            if self.reply == "timeout":
                print("Times out! Exit the program.")
                # self.sock.close()
                exit_flag.append(1)
                self.exit = True
            if self.reply == "logout":
                exit_flag.append(1)
                self.exit = True



def login():
    login_flag = True
    while login_flag:
        while True:
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
            print("Too many tries! You have been blocked for a while.")
            clientSocket.close()
            sys.exit()
        if answer_login == "wrong":
            print("Wrong username or password! Please retry.")
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
clientSocket.close()


