#chat server - project 1 CS 168
#  by Luis Torres
import socket
import sys

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

    def start(self):
        while True:
            """will need to implement more features"""
            (new_socket, address) = self.socket.accept()
            msg = new_socket.recv(1024)
            tmp = msg
            while tmp:
                tmp = new_socket.recv(1024)
                msg += tmp
            print msg

if __name__ == '__main__':
    if len(args) != 2:
        print "Please supply a port."
        sys.exit()
    server = ChatServer(args[1])
    server.start()
