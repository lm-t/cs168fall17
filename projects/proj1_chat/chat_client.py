###Chat Client - project 1 CS 168
### by Luis Torres
###Inspired by "http://www.binarytides.com/code-chat-application-server-client-sockets-python/"
import socket, select, sys
from utils import *

class ChatClient(object):

    def __init__(self, address, port):
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()
    def start(self):
        #connect to server
        try:
            self.socket.connect((self.address, self.port))
            print("connected to server")
        except:
            error_message = CLIENT_CANNOT_CONNECT.format(self.address, self.port)
            print(error_message)

        prompt()
        while True:
            read, write, error = select.select([sys.stdin, self.socket], [], [])
            for socket in read:
                if socket == self.socket:
                    message = socket.recv(4096)
                    sys.stdout.write(message)
                    prompt()
                else:
                    message = sys.stdin.readline()
                    self.socket.send(message)
                    prompt()

def prompt():
    sys.stdout.write("[Me] ")
    sys.stdout.flush()

if __name__ == '__main__':
    args = sys.argv
    if len(args) != 3:
        print "Please supply a server address and port."
        sys.exit()
    client = ChatClient(args[1], args[2])
    client.start()
