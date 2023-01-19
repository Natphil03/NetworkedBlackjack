import socket
import sys
import threading
import queue
import time
from diffiehellman import diffie_hellman
import rsa
import pickle
import pem
from os import path


class ClientClass:
    def __init__(self, host="127.0.0.1", port=50000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.header = 1024
        self.connectedState = False
        self.negotiationState = False
        self.KeyShareState = False

        self.ClientPubKey = None
        self.ClientPrivKey = None
        self.ServerPubKey = None

        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.msgRecvThread = threading.Thread(target=self.recvMes, daemon=True)

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

    def encryption(self, message):
        return rsa.encrypt(message.encode("utf-8"), self.ServerPubKey)

    def decryption(self, message):
        return rsa.decrypt(message, self.ClientPrivKey).decode("utf-8")

    def readProc(self):
        while self.connectedState:
            try:
                if not self.iBuffer.empty():
                    message = self.iBuffer.get()
                    print(f"RECEIVED : {message}")
            except Exception as e:
                print(e)

    def writeProc(self):
        while self.connectedState:
            try:
                if not self.oBuffer.empty():
                    message = self.oBuffer.get()
                    if message:
                        if message == "QUIT":
                            self.connectedState = False
                        self.client.send(message)
            except socket.error as e:
                print("Server has Disconnected...")
                self.connectedState = False

    def recvMes(self):
        while self.connectedState:
            try:
                message = self.client.recv(self.header)
                print(message)
                decrypted = self.decryption(message)
                if decrypted:
                    if decrypted == "QUIT":
                        self.connectedState = False
                    else:
                        self.iBuffer.put(decrypted)
            except socket.error as e:
                print("Server has Disconnected...")
                self.connectedState = False

    def sendMessage(self, message):
        try:
            encrypted = self.encryption(message)
            self.oBuffer.put(encrypted)
            print("SENDING : ", message)
        except Exception as e:
            print(e)

    def runClient(self):

        endMessage = "QUIT"
        echoMessage = "Hello Server"

        try:
            if path.exists('private.pem') and path.exists('public.pem'):
                print("Keys Exist")
                with open('private.pem', mode='rb') as privatefile:
                    keydata = privatefile.read()
                    privkey = rsa.PrivateKey.load_pkcs1(keydata, format="PEM")


                with open('public.pem', mode='rb') as publicfile:
                    keydata = publicfile.read()
                    pubkey = rsa.PublicKey.load_pkcs1(keydata, format="PEM")

            else:
                print("Keys do not Exist")
                pubkey, privkey = rsa.newkeys(1024)

                with open('public.pem', mode='wb') as publicfile:
                    publicfile.write(pubkey.save_pkcs1("PEM"))

                with open('private.pem', mode='wb') as privatefile:
                    privatefile.write(privkey.save_pkcs1("PEM"))

                print("Keys Saved")
        except Exception as e:
            print(e)

        self.client.connect(self.addr)
        self.connectedState = True

        self.ClientPubKey = pubkey
        self.ClientPrivKey = privkey


        dumpClientPubKey = pickle.dumps(self.ClientPubKey)
        self.client.send(dumpClientPubKey)

        dump = self.client.recv(4096)
        self.ServerPubKey = pickle.loads(dump)

        self.readThread.start()
        self.writeThread.start()
        self.msgRecvThread.start()

        while self.connectedState:
            # user = input("Enter a Message : ")
            # self.sendMessage(user)

            self.sendMessage(echoMessage)
            time.sleep(5)

        self.readThread.join()
        self.writeThread.join()
        self.msgRecvThread.join()

        print("Closing Client...")
        self.client.close()


if __name__ == "__main__":
    client = ClientClass()
    client.runClient()
