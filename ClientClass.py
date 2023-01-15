import socket
import threading
import queue
import time


class ClientClass:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = "127.0.0.1"
        self.port = 50005
        self.addr = (self.host, self.port)
        self.connectedState = False

        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.msgRecvThread = threading.Thread(target=self.recvMes, daemon=True)

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

    def readProc(self):
        while self.connectedState:
            msg = self.iBuffer.get()
            print(f"RECEIVED: [{msg}]")

    def writeProc(self):
        while self.connectedState:
            message = self.oBuffer.get()
            if message:
                if message == "QUIT":
                    self.connectedState = False
                    self.client.send(message.encode("utf-8"))
                else:
                    self.client.send(message.encode("utf-8"))

    def recvMes(self):
        while self.connectedState:
            self.iBuffer.put(self.client.recv(1024).decode("utf-8"))

    def runClient(self):
        self.client.connect(self.addr)
        self.connectedState = True


        endMessage = "QUIT"
        echoMessage = "ECHO : Hello"

        self.readThread.start()
        self.writeThread.start()
        self.msgRecvThread.start()

        while self.connectedState:
            self.oBuffer.put(echoMessage)
            time.sleep(1)
            #self.oBuffer.put(endMessage)





if __name__ == "__main__":
    client = ClientClass()
    client.runClient()
