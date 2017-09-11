###Chat Client - project 1 CS 168
### by Luis Torres
###Inspired by "http://www.binarytides.com/code-chat-application-server-client-sockets-python/"
import socket, select, sys
from utils import *

BUFFER_SIZE = 1024

def pad_message(message):
  while len(message) < MESSAGE_LENGTH:
    message += " "
  return message[:MESSAGE_LENGTH]

class ChatClient(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

    def prompt(self):
        sys.stdout.write(CLIENT_MESSAGE_PREFIX)
        sys.stdout.flush()

    def start(self):
        #connect to server
        try:
            self.socket.connect((self.address, self.port))
        except:
            error_message = CLIENT_CANNOT_CONNECT.format(self.address, self.port)
            print(error_message)

        #send client name to server
        self.socket.send(pad_message(self.name))

        self.prompt()
        while True:
            read, write, error = select.select([sys.stdin, self.socket], [], [])
            for socket in read:
                if socket == self.socket:
                    message = socket.recv(BUFFER_SIZE)
                    if message:
                        sys.stdout.write(message)
                        self.prompt()
                else:
                    message = sys.stdin.readline()
                    self.socket.send(message)
                    #stll need to fix '[Me] ' formating
                    self.prompt()


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 4:
        print "Please supply a name, server address, and port."
        sys.exit()
    client = ChatClient(args[1], args[2], args[3])
    client.start()
