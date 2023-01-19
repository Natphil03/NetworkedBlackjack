import socket
import threading
import queue
import time

from os import path

from diffiehellman import diffie_hellman
import rsa
import pem
import pickle
import random


class ConnectionClass:
    def __init__(self):
        self.header = 1024
        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.msgRecvThread = threading.Thread(target=self.recvMes, daemon=True)

        self.connectedState = False
        self.KeyShareState = False


        self.ServerPubKey = None
        self.ServerPrivKey = None

        self.ClientPubKey = None

        self.conn = None
        self.addr = None

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

    def encrypt(self, message):
        return rsa.encrypt(message.encode("utf-8"), self.ClientPubKey)

    def decrypt(self, message):
        return rsa.decrypt(message, self.ServerPrivKey).decode("utf-8")

    def readProc(self):
        while self.connectedState:
            try:
                if not self.iBuffer.empty():
                    message = self.iBuffer.get()
                    print("RECEIVED : ", message)
            except Exception as e:
                print(e)

    def writeProc(self):
        while self.connectedState:
            try:
                if not self.oBuffer.empty():
                    message = self.oBuffer.get()
                    if message:
                        self.conn.send(message)
            except socket.error as e:
                print("Client has Disconnected...")
                self.connectedState = False

    def recvMes(self):
        while self.connectedState:
            try:
                message = self.conn.recv(self.header)
                print(message)
                decrypted = self.decrypt(message)
                if decrypted:
                    if decrypted == "QUIT":
                        self.connectedState = False
                    else:
                        self.iBuffer.put(decrypted)
            except socket.error as e:
                print("Client has Disconnected...")
                self.connectedState = False

    def sendMessage(self, message):
        try:
            encryptMsg = self.encrypt(message)
            self.oBuffer.put(encryptMsg)
            print("SENDING : ", message)
        except Exception as e:
            print(e)

    def sendUnEncryptedMessage(self, message):
        try:
            self.oBuffer.put(message.encode("utf-8"))
            print("SENDING : ", message)
        except Exception as e:
            print(e)

    def handle_client(self, conn, addr, pubkey, privkey):
        self.connectedState = True
        self.KeyShareState = True

        self.conn = conn
        self.addr = addr

        self.ServerPubKey = pubkey
        self.ServerPrivKey = privkey

        endMessage = "QUIT"
        echoMessage = "Hello Client"
        acknowledge = "[Key Exchange State]"

        print(f"[NEW CONNECTION] {self.addr} Connected.")

        dump = self.conn.recv(4096)
        self.ClientPubKey = pickle.loads(dump)

        dumpServerPubKey = pickle.dumps(self.ServerPubKey)
        self.conn.send(dumpServerPubKey)

        self.readThread.start()
        self.writeThread.start()
        self.msgRecvThread.start()

        while self.connectedState:
            self.sendMessage(echoMessage)
            time.sleep(5)

        self.readThread.join()
        self.writeThread.join()
        self.msgRecvThread.join()

        print(f"DISCONNECTING FROM [{self.addr}]")

        self.conn.close()


class Server:
    def __init__(self, host="127.0.0.1", port=50000):
        self.connThread = None
        self.header = 1024
        self.port = port
        self.host = host
        self.address = (self.host, self.port)
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None
        self.connection = None

        self.negotiationState = False

    def start(self):
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind(self.address)
        self.serv.listen()

        try:
            if path.exists('private.pem') and path.exists('public.pem'):
                print("Keys Exist")
                with open('private.pem', mode='rb') as privatefile:
                    keydata = privatefile.read()
                    privkey = rsa.PrivateKey.load_pkcs1(keydata, format="PEM")

                    #privkey = pem.parse(privatefile.read())
                    #privkey = str(privkey[0]).replace('-----BEGIN RSA PRIVATE KEY-----', "").replace('-----END RSA PRIVATE KEY-----',
                     #                                                                                "").strip()

                with open('public.pem', mode='rb') as publicfile:
                    keydata = publicfile.read()
                    pubkey = rsa.PublicKey.load_pkcs1(keydata, format="PEM")
                    # privkey = pem.parse(publicfile.read())
                    # privkey = str(privkey[0]).replace('-----BEGIN RSA PRIVATE KEY-----', "").replace(
                    #     '-----END RSA PRIVATE KEY-----',
                    #     "").strip()

                    #pubkey = rsa.PublicKey.load_pkcs1(keydata, format="PEM")
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

        print(f"\n[LISTENING ON: ] {self.host}")

        while True:
            self.conn, self.addr = self.serv.accept()
            self.connection = ConnectionClass()

            self.connThread = threading.Thread(target=self.connection.handle_client,
                                               args=(self.conn, self.addr, pubkey, privkey), daemon=True)

            self.connThread.start()


if __name__ == '__main__':
    print("Starting Server")
    server = Server()
    server.start()
