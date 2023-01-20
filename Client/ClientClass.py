import random
import socket
import threading
import queue
from calendar import timegm
from time import *
import rsa
import pickle
from os import path
import string


class ClientClass:
    def __init__(self, host="127.0.0.1", port=50000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.header = 2048
        self.offset = 2
        self.timeFormat = '%Y-%m-%dT%H:%M:%SZ'
        self.NonceCharacters = string.ascii_letters + string.digits + string.punctuation

        self.connectedState = False
        self.currentState = None
        self.playerInputState = False

        self.ClientPubKey = None
        self.ClientPrivKey = None
        self.ServerPubKey = None

        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.msgRecvThread = threading.Thread(target=self.recvMes, daemon=True)

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

    def generateSalt(self, length=6):
        # generates a random 6 character/digit phrase as a salt. Outputs as a string. Length is 6 as parameterized.
        random_chars = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.punctuation)
                               for _ in range(length))
        return ''.join(random_chars)

    def makeNonce(self):
        # gets current time
        time = gmtime()
        # turns current time into a string using the self.time_fmt format.
        time_str = strftime(self.timeFormat, time)
        # returns the time string with a unique salt.
        return time_str + self.generateSalt()

    def splitNonce(self, nonce_string):
        # find the length of the time string following the format.
        time_str_len = len('0000-00-00T00:00:00Z')
        # the time slice in the nonce string is the slice of the length from the left to the right.
        timestamp_str = nonce_string[:time_str_len]
        # calculates unix timestamp following the format.
        timestamp = timegm(strptime(timestamp_str, self.timeFormat))
        if timestamp < 0:
            raise ValueError('Time Error')
        # returns the timestamp and total nonce salt excluded.
        return timestamp, nonce_string[time_str_len:]

    def checkTimeStamp(self, nonce_string):
        # Split nonce string into the time stamp and nonce
        stamp, _ = self.splitNonce(nonce_string)

        #get current time
        now = time()

        # allowed time difference, allows for communication and processing overhead
        allowed_skew = self.offset
        # Time after which we should not use the nonce
        past = now - allowed_skew
        # Time that is too far in the future for us to allow
        future = now + allowed_skew
        # the stamp is not too far in the future and is not too far in
        # the past
        return past <= stamp <= future

    def encrypt(self, message):
        # encrypt encoded message with servers public key, returns the encrypted bytes
        try:
            return rsa.encrypt(message.encode("utf-8"), self.ServerPubKey)
        except rsa.pkcs1.CryptoError:
            return False

    def decrypt(self, message):
        # decrypts using clients private key and decodeds
        try:
            return rsa.decrypt(message, self.ClientPrivKey).decode("utf-8")
        except rsa.pkcs1.DecryptionError:
            return False

    def sign(self, message):
        # sign the message with the private key using MD5 hashing to detect if tampered with
        try:
            return rsa.sign(message.encode("utf-8"), self.ClientPrivKey, 'MD5')
        except rsa.pkcs1.CryptoError as e:
            print(e)
            return False

    def verify(self, message, signature):
        # verify if signature has changed since being communicated.
        try:
            return rsa.verify(message.encode("utf-8"), signature, self.ServerPubKey) == 'MD5'
        except rsa.pkcs1.VerificationError:
            return False

    def readProc(self):
        # while connected, if the buffer is not empty, get the latest message and output
        while self.connectedState:
            try:
                if not self.iBuffer.empty():
                    message = self.iBuffer.get()
                    print(f"{message}")
            except Exception as e:
                print(e)

    def writeProc(self):
        # while connected, get the latest message from buffer.
        while self.connectedState:
            try:
                if not self.oBuffer.empty():
                    message = self.oBuffer.get()
                    if message:
                        # if message is quit, close the connction
                        if message == "QUIT":
                            self.connectedState = False
                        # send the message to peer.
                        self.client.send(message)
            except socket.error as e:
                print("Server has Disconnected...")
                self.connectedState = False

    def processMessage(self, message):
        # extract dictionary values from message
        messageContent = message["message"]
        messageSignature = message["signature"]
        messageNonce = message["timeStamp"]

        # decrypt the messageContents
        decrypted = self.decrypt(messageContent)

        # if the time stamp has exceeded the time limit then close the connection as potential MIM
        if self.checkTimeStamp(messageNonce):
            pass
        else:
            print("POTENTIAL REPLAY ATTACK - QUITTING...")
            self.connectedState = False

        # verify the signature of decrypted message, ensure not tampered with.
        if self.verify(decrypted, messageSignature):
            pass
        else:
            print("MESSAGE TAMPERED, CLOSING SESSION")
            self.connectedState = False

        return decrypted

    def recvMes(self):
        # while connected.
        while self.connectedState:
            try:
                # check if new message, if so, load message.
                messageDump = self.client.recv(2048)
                message = pickle.loads(messageDump)

                # process the message.
                decrypted = self.processMessage(message)

                if decrypted:
                    # if message is QUIT, close the connection, otherwise add to buffer.
                    if decrypted == "QUIT":
                        self.connectedState = False

                    elif decrypted == "[PlayerInputState]":
                        self.playerInputState = True
                        print("player state")

                    elif decrypted == "[EndPlayerInputState]":
                        self.playerInputState = False
                        print("player state end")

                    else:
                        self.iBuffer.put(decrypted)

            except Exception as e:
                print("Server has Disconnected...")
                self.connectedState = False

    def sendMessage(self, message):
        try:
            # encrypt the message
            encryptMsg = self.encrypt(message)
            # sign the message
            signature = self.sign(message)
            # add nonce to the message with timeStamp.
            nonceString = self.makeNonce()
            a_dict = {"message": encryptMsg, "signature": signature, "timeStamp": nonceString}
            # serialize the dictinary
            serialized_dict = pickle.dumps(a_dict)
            # put dictionary onto buffer.
            self.oBuffer.put(serialized_dict)
            print("SENDING : ", message)

        except Exception as e:
            print(e)

    def generateKeys(self):
        # generate new keys.
        pubkey, privkey = rsa.newkeys(1024)
        return pubkey, privkey

    def KeyExchange(self):
        # Sending client public key
        dumpClientPubKey = pickle.dumps(self.ClientPubKey)
        self.client.send(dumpClientPubKey)
        # receiving server public key
        dump = self.client.recv(4096)
        self.ServerPubKey = pickle.loads(dump)

    def runClient(self):
        endMessage = "QUIT"
        echoMessage = "Hello Server"

        #  Generate new keys for every client so no two clients have same public key
        self.ClientPubKey, self.ClientPrivKey = self.generateKeys()

        # connect to server
        self.client.connect(self.addr)

        self.KeyExchange()

        self.connectedState = True

        self.readThread.start()
        self.writeThread.start()
        self.msgRecvThread.start()

        count = 0
        while self.connectedState:
            if self.playerInputState:
                if count < 3:
                    count += 1
                    message = input()
                    self.sendMessage(message)
                else:
                    continue
            continue

            # self.sendMessage(echoMessage)
            # sleep(5)
            # self.sendMessage(echoMessage)
            # sleep(5)
            # self.sendMessage(endMessage)

        # end threads
        self.readThread.join()
        self.writeThread.join()
        self.msgRecvThread.join()

        print("Closing Client...")
        self.client.close()


if __name__ == "__main__":
    client = ClientClass()
    client.runClient()
