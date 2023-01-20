import random
import socket
import threading
import queue
import time
from calendar import timegm
from time import *
import rsa
import pickle
from os import path
import string

class ConnectionClass:
    def __init__(self):
        self.header = 2048
        self.offset = 2
        self.timeFormat = '%Y-%m-%dT%H:%M:%SZ'
        self.NonceCharacters = string.ascii_letters + string.digits + string.punctuation
        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.msgRecvThread = threading.Thread(target=self.recvMes, daemon=True)

        self.connectedState = False
        self.playerInputState = False

        self.ServerPubKey = None
        self.ServerPrivKey = None
        self.ClientPubKey = None

        self.conn = None
        self.addr = None

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()
        self.playerInputBuffer = queue.Queue()

    def encrypt(self, message):
        try:
            return rsa.encrypt(message.encode("utf-8"), self.ClientPubKey)
        except rsa.pkcs1.CryptoError:
            return False

    def decrypt(self, message):
        try:
            return rsa.decrypt(message, self.ServerPrivKey).decode("utf-8")
        except rsa.pkcs1.DecryptionError as e:
            print(e)
            return False

    def sign(self, message):
        try:
            return rsa.sign(message.encode("utf-8"), self.ServerPrivKey, 'MD5')
        except rsa.pkcs1.CryptoError:
            return False

    def verify(self, message, signature):
        try:
            if rsa.verify(str(message).encode("utf-8"), signature, self.ClientPubKey) == 'MD5':
                return True
            else:
                return False
        except rsa.pkcs1.VerificationError:
            return False

    def generateSalt(self, length=6):
        random_chars = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.punctuation)
                               for _ in range(length))
        return ''.join(random_chars)

    def makeNonce(self):
        t = gmtime()

        time_str = strftime(self.timeFormat, t)
        return time_str + self.generateSalt()

    def splitNonce(self, nonce_string):

        time_str_len = len('0000-00-00T00:00:00Z')

        timestamp_str = nonce_string[:time_str_len]
        timestamp = timegm(strptime(timestamp_str, self.timeFormat))
        if timestamp < 0:
            raise ValueError('time out of range')
        return timestamp, nonce_string[time_str_len:]

    def checkTimeStamp(self, nonce_string):
        # Split nonce string into the time stamp and nonce
        stamp, _ = self.splitNonce(nonce_string)

        # get current time
        now = time()

        allowed_skew = self.offset
        # Time after which we should not use the nonce
        past = now - allowed_skew
        # Time that is too far in the future for us to allow
        future = now + allowed_skew
        # the stamp is not too far in the future and is not too far in
        # the past
        return past <= stamp <= future

    def readProc(self):
        while self.connectedState:
            try:
                if not self.iBuffer.empty():
                    message = self.iBuffer.get()
                    print(f"RECEIVED [{self.addr}] : ", message)
            except Exception as e:
                print(e)

    def writeProc(self):
        while self.connectedState:
            try:
                if not self.oBuffer.empty():
                    message = self.oBuffer.get()
                    if message:
                        self.conn.sendall(message)
            except socket.error as e:
                print("Client has Disconnected...")
                self.connectedState = False

    def processMessage(self, message):
        # Extracts values from dictionary message.
        messageContent = message["message"]
        messageSignature = message["signature"]
        messageNonce = message["timeStamp"]

        # decrypts message content.
        decrypted = self.decrypt(messageContent)

        # if the time stamp of the message exceeds time limit then quit connection
        if self.checkTimeStamp(messageNonce):
            pass
        else:
            print("POTENTIAL REPLAY ATTACK - QUITTING...")
            self.connectedState = False

        # if the decrypted message has been tampered with, e.g. hashes do not match prior and post communication.
        # Close connection
        if self.verify(decrypted, messageSignature):
            pass
        else:
            print("MESSAGE TAMPERED, CLOSING SESSION")
            self.connectedState = False

        # return decrypted message
        return decrypted

    def getPlayerInput(self):
        try:
            return self.playerInputBuffer.get()
        except Exception as e:
            print(e)
            print("Error Retrieving Player Input")

    def recvMes(self):
        while self.connectedState:
            try:
                # receive the message json.
                messageDump = self.conn.recv(2048)
                message = pickle.loads(messageDump)  # dump dictionary object to string.

                # process retrieved message
                decrypted = self.processMessage(message)

                # if message, if it is quit message then quit.
                if decrypted:
                    if decrypted == "QUIT":
                        self.connectedState = False

                    if self.playerInputState:
                        print("Adding Player Input")
                        self.playerInputBuffer.put(decrypted)
                    else:
                        # otherwise put onto inwards buffer.
                        self.iBuffer.put(decrypted)
            except Exception as e:
                print("Client has Disconnected...")
                self.connectedState = False

    def sendMessage(self, message):
        try:
            print(message)
            # encrypt message and sign with hash.
            encryptMsg = self.encrypt(message)
            signature = self.sign(message)

            # generate cryptographic nonce.
            nonceString = self.makeNonce()

            # format dictionary
            a_dict = {"message": encryptMsg, "signature": signature, "timeStamp": nonceString}
            # serialize dictionary for sending over socket as must be byte object.
            serialized_dict = pickle.dumps(a_dict)

            # send message.
            self.oBuffer.put(serialized_dict)

        except Exception as e:
            print(e)

    def keyExchange(self):
        dump = self.conn.recv(4096)
        self.ClientPubKey = pickle.loads(dump)
        dumpServerPubKey = pickle.dumps(self.ServerPubKey)
        self.conn.sendall(dumpServerPubKey)

    def handle_client(self, conn, addr, pubkey, privkey):
        # we are now connected.
        self.connectedState = True
        self.loggedOut = True

        self.conn = conn
        self.addr = addr
        self.ServerPubKey = pubkey
        self.ServerPrivKey = privkey
        echoMessage = "Hello Client"

        print(f"[NEW CONNECTION] {self.addr} Connected.")
        self.keyExchange()

        self.readThread.start()
        self.writeThread.start()
        self.msgRecvThread.start()

        while self.connectedState:
            continue
            # self.sendMessage(echoMessage)
            # sleep(5)

        self.readThread.join()
        self.writeThread.join()
        self.msgRecvThread.join()

        # print("Read Thread :", self.readThread.is_alive())
        # print("Write Thread :", self.writeThread.is_alive())
        # print("msgRecv Thread :", self.msgRecvThread.is_alive())

        print(f"DISCONNECTING FROM [{self.addr}]")

        self.conn.close()
