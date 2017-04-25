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
    if answer_login == "timeout":
        print("Times out! Exit the program.")
        sys.exit()
    if answer_login == "block":
        print("Too many tries! You have been blocked for a while.")
        clientSocket.close()
        sys.exit()
    print("Wrong username or password! Please retry.")

def rec(sock):
    while True:
        reply = sock.recv(1024).decode()
        print(reply)
        if reply == "timeout":
            print("exit")
            sys.exit()
        print(reply)

thread_rec = threading.Thread(target=rec,args=(clientSocket,))
thread_rec.start()
while True:
    message = input()
    clientSocket.send(message.encode())




