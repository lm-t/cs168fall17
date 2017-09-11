###Chat Server - project 1 CS 168
###  by Luis Torres
###Inspired by "http://www.binarytides.com/code-chat-application-server-client-sockets-python/"
import socket
import select
import sys
from utils import *

args = sys.argv
BUFFER_SIZE = 1024
### TO DO
# Create Channel implementation
#  - /join
#  - /create
#  - /list

def recvall(sock):
    #from stackoverflow "non-blocking socket in python"
    alldata = ""
    while len(data) < MESSAGE_LENGTH:
        data = sock.recv(MESSAGE_LENGTH - len(data))
        if not data:
            return None
        alldata += data
    return alldata

def isControlMessage(message):
    if message[:7] == "/create" or message[:5] == "/join" or message[:5] == "/list":
        return True
    else:
        return False

def parseControlMessage(message):
    """will return example, ['/create', 'dinner']"""
    reverseMsg = message[::-1]
    Msg = reverseMsg.lstrip()[::-1]
    return Msg.split(" ", 1)

class ChatServer(object):
    """ChatServer will have multiple clients and have the ablility to create channels"""
    def __init__(self, port):
        self.socket = socket.socket()
        self.socket.bind(("", int(port)))
        self.socket.listen(5)
        self.connections = [self.socket]
        self.clients = {}
        self.channels = {}

    def broadcast(self, sock, message):
        for socket in self.connections:
            if socket != self.socket and socket != sock:
                try:
                    socket.send(message)
                except:
                    socket.close()
                    self.connections.remove(socket)

    def hasChannel(self, socket):
        for channel in self.channels.itervalues():
            for sock in channel:
                if socket == sock:
                    return True
        return False

    def createChannel(self, socket, message):
        if len(message) == 1:
            socket.send(SERVER_CREATE_REQUIRES_ARGUMENT + "\n")
        elif message[1] in self.channels:
            socket.send(SERVER_CHANNEL_EXISTS.format(message[1]) + "\n")
        else:
            print "adding " + message[1]
            self.channels[message[1]] = [socket]

    def joinChannel(self, socket, message):
        if len(message) == 1:
            socket.send(SERVER_JOIN_REQUIRES_ARGUMENT + "\n")
        elif message[1] not in self.channels.keys():
            socket.send(SERVER_NO_CHANNEL_EXISTS.format(message[1]) + "\n")
        else:
            print "joining " + message[1]
            self.channels[message[1]].append(socket)
            """notify other clients of new join and channel leave"""

    def listChannel(self, socket, message):
        msg = ""
        for channel in self.channels.keys():
            msg = msg + channel + "\n"
        socket.send(msg)

    def start(self):
        while True:
            """will need to implement more features"""
            read, write, error = select.select(self.connections, [], [])
            for socket in read:
                ###New Connection
                if socket == self.socket:
                    #adding clients name to a dictionary by storing its specific port
                    (new_socket, address) = self.socket.accept()
                    self.connections.append(new_socket)
                    name = new_socket.recv(BUFFER_SIZE)
                    self.clients[socket] = name.replace(" ", "")
                    print "Connected to client " + self.clients[socket]

                else:
                    try:
                        message = socket.recv(BUFFER_SIZE)
                        if message:
                            if isControlMessage(message):
                                msg = parseControlMessage(message)
                                if msg[0] == "/create":
                                    self.createChannel(socket, msg)
                                elif msg[0] == "/join":
                                    self.joinChannel(socket, msg)
                                elif msg[0] == "/list":
                                    self.listChannel(socket, msg)
                            elif not self.hasChannel(socket):
                                socket.send(SERVER_CLIENT_NOT_IN_CHANNEL + "\n")

                            #self.broadcast(socket, data)
                    except:
                        socket.close()
                        #print "closing connection to " + self.clients[socket]
                        self.connections.remove(socket)

if __name__ == '__main__':
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = ChatServer(args[1])
    server.start()
