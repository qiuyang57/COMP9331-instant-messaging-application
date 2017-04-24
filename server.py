from time import time
from socket import *
import threading

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
login_require_flag = True
login_remain_times = 2
server_blocklist =[]


connectionSocket, addr = serverSocket.accept()
# print(addr)
while login_require_flag:
    message = connectionSocket.recv(1024).decode()
    word = message.split()
    print(word)
    reply = "wrong"
    if message == "":
        print("connection lost")
        break
    if login_remain_times == 0:
        reply = "block"
        server_blocklist.append([addr[0],time()])
        print(server_blocklist)
    print(word[1], credentials.keys())
    if word[1] in credentials.keys():
        if credentials[word[1]] == word[2]:
            reply = "welcome"
            login_require_flag = False
    connectionSocket.send(reply.encode())
    login_remain_times -= 1

while True:
    message = connectionSocket.recv(1024)
    connectionSocket.send(message)
connectionSocket.close()
