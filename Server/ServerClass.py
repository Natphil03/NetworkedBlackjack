import socket
import sys
import threading
import rsa
from os import path
import Blackjack


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

    def generateKeys(self):
        pubkey, privkey = rsa.newkeys(1024)
        with open('public.pem', mode='wb') as publicfile:
            publicfile.write(pubkey.save_pkcs1("PEM"))

        with open('private.pem', mode='wb') as privatefile:
            privatefile.write(privkey.save_pkcs1("PEM"))

    def loadKeys(self):
        with open('private.pem', mode='rb') as privatefile:
            keydata = privatefile.read()
            privkey = rsa.PrivateKey.load_pkcs1(keydata, format="PEM")

        with open('public.pem', mode='rb') as publicfile:
            keydata = publicfile.read()
            pubkey = rsa.PublicKey.load_pkcs1(keydata, format="PEM")

        return pubkey, privkey

    def start(self):
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serv.bind(self.address)
        self.serv.listen()

        try:
            if path.exists('private.pem') and path.exists('public.pem'):
                pubkey, privkey = self.loadKeys()
            else:
                self.generateKeys()
                pubkey, privkey = self.loadKeys()
        except Exception as e:
            print(e)
            print("Failed to get Keys, Quitting")
            sys.exit()

        print(f"\n[LISTENING ON: ] {self.host}")

        while True:
            self.conn, self.addr = self.serv.accept()

            self.gameSession = Blackjack.BlackJack()


            self.gameThread = threading.Thread(target=self.gameSession.startingGame,
                                               args=(self.conn, self.addr, pubkey, privkey), daemon=True)

            self.gameThread.start()


if __name__ == '__main__':
    print("Starting Server")
    server = Server()
    server.start()
