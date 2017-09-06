###Chat Server - project 1 CS 168
###  by Luis Torres
###Inspired by "http://www.binarytides.com/code-chat-application-server-client-sockets-python/"
import socket
import select
import sys
from utils import *

args = sys.argv

### TO DO
# Create Channel implementation
#  - /join
#  - /create
#  - /list

class ChatServer(object):
    """ChatServer will have multiple clients and have the ablility to create channels"""
    def __init__(self, port):
        self.socket = socket.socket()
        self.socket.bind(("", int(port)))
        self.socket.listen(5)
        self.connections = [self.socket]

    def broadcast(self, sock, message):
        for socket in self.connections:
            if socket != self.socket and socket != sock:
                try:
                    socket.send(message)
                except:
                    socket.close()
                    self.connections.remove(socket)

    def start(self):
        while True:
            """will need to implement more features"""
            read, write, error = select.select(self.connections, [], [])
            for socket in read:
                ###New Connection
                if socket == self.socket:
                    (new_socket, address) = self.socket.accept()
                    self.connections.append(new_socket)
                    self.broadcast(socket, "Welcome to the ChatServer!\n")
                else:
                    try:
                        message = socket.recv(4096)
                        if data:
                            self.broadcast(socket,"[" + str(socket.getpeername()) + "]" + data)
                    except:
                        socket.close()
                        self.connections.remove(socket)

if __name__ == '__main__':
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = ChatServer(args[1])
    server.start()
