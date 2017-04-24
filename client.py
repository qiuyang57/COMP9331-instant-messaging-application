import sys
import threading
from socket import *

serverName = "127.0.0.1"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
while True:
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
        break
    if answer_login == "block":
        print("Too many tries! You have been blocked for a while.")
        clientSocket.close()
        sys.exit()
    print("Wrong username or password! Please retry.")

class ReceiverThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            reply = clientSocket.recv(1024)
            print(reply)



thread_rec = ReceiverThread()
while True:
    message = input()
    clientSocket.send(message.encode())
    thread_rec.run()



