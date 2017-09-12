###Chat Server - project 1 CS 168
###  by Luis Torres
###Inspired by "http://www.binarytides.com/code-chat-application-server-client-sockets-python/"
import socket
import select
import sys
from utils import *

args = sys.argv
BUFFER_SIZE = 1024

def pad_message(message):
  while len(message) < MESSAGE_LENGTH:
    message += " "
  return message[:MESSAGE_LENGTH]

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
    if message[0] == "/":
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
        self.buffer = {}

    def broadcast(self, socket, message, isNotSpecial, chnl):
        if isNotSpecial:
            reverseMsg = message[::-1]
            msg = reverseMsg.lstrip()[::-1]
            client = "[%s] " % self.clients[socket]
            msg = client + msg
            print "client message: " + msg
        else:
            msg = message
        for sock in self.channels[chnl]:
            if sock != self.socket and sock != socket:
                sock.send(msg)

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
        elif self.hasChannel(socket):
            for channel in self.channels.keys():
                if socket in self.channels[channel]:
                    client = self.clients[socket]
                    self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(client), False, channel)
                    self.channels[channel].remove(socket)
                    self.channels[message[1]] = [socket]
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
            client = self.clients[socket]
            if self.hasChannel(socket):
                for channel in self.channels.keys():
                    if socket in self.channels[channel]:
                        self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(client), False, channel)
                        self.channels[channel].remove(socket)
            self.channels[message[1]].append(socket)
            self.broadcast(socket, SERVER_CLIENT_JOINED_CHANNEL.format(client), False, message[1])

    def listChannel(self, socket, message):
        msg = ""
        for channel in self.channels.keys():
            msg = msg + channel + "\n"
        socket.send(msg)

    def process(self, message, socket):
        if message:
            if isControlMessage(message):
                msg = parseControlMessage(message)
                if msg[0] == "/create":
                    self.createChannel(socket, msg)
                elif msg[0] == "/join":
                    self.joinChannel(socket, msg)
                elif msg[0] == "/list":
                    self.listChannel(socket, msg)
                else:
                    socket.send(SERVER_INVALID_CONTROL_MESSAGE.format(msg[0]))
            elif not self.hasChannel(socket):
                socket.send(SERVER_CLIENT_NOT_IN_CHANNEL + "\n")
            else:
                for channel in self.channels.keys():
                    if socket in self.channels[channel]:
                        chnl = channel
                self.broadcast(socket, message, True, chnl)
        else:
            #remove broken socket
            if socket in self.connections:
                self.connections.remove(socket)
            client = self.clients[socket]
            if self.hasChannel(socket):
                for channel in self.channels.keys():
                    if socket in self.channels[channel]:
                        self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(client), False, channel)
                        self.channels[channel].remove(socket)

    def start(self):
        while True:
            read, write, error = select.select(self.connections, [], [])
            for socket in read:
                ###New Connection
                if socket == self.socket:
                    #adding clients name to a dictionary by storing its specific port
                    (new_socket, address) = self.socket.accept()
                    self.connections.append(new_socket)
                    self.buffer[new_socket] = ""
                    name = new_socket.recv(BUFFER_SIZE)
                    self.clients[new_socket] = name.replace(" ", "")
                    print "Connected to client " + self.clients[new_socket]
                else:
                    try:
                        message = socket.recv(BUFFER_SIZE)
                        # message = self.recvbuff(socket)
                        # if self.messageComplete(socket):
                        buffer_message = ""
                        if len(message) != 0:
                            for char in list(message):
                                if len(self.buffer[socket]) < MESSAGE_LENGTH:
                                    self.buffer[socket] += char
                                print len(self.buffer[socket]), self.buffer[socket]
                                if len(self.buffer[socket]) == MESSAGE_LENGTH:
                                    buffer_message = self.buffer[socket]
                                    self.buffer[socket] = ""
                            message = buffer_message
                        self.process(message, socket)
                    except:
                        print "socket closed"
                        self.clients.pop(socket)
                        socket.close()

if __name__ == '__main__':
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = ChatServer(args[1])
    server.start()
