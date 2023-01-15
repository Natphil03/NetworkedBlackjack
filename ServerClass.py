import socket
import threading
import Blackjack
import queue


class ConnectionClass:
    def __init__(self):
        self.header = 1024
        self.readThread = threading.Thread(target=self.readProc, daemon=True)
        self.writeThread = threading.Thread(target=self.writeProc, daemon=True)
        self.connected = None
        self.reading = None
        self.completed = None
        self.conn = None
        self.addr = None

        self.iBuffer = queue.Queue()
        self.oBuffer = queue.Queue()

    def encrypt(self):
        pass

    def readProc(self):
        while self.connected:
            try:
                message = self.iBuffer.get()
                if message == "QUIT":
                    self.connected = False

            except Exception as e:
                print(e)

    def writeProc(self):
        while self.connected:
            message = self.oBuffer.get()
            if message:
                self.conn.send(message.encode("utf-8"))

    def handle_client(self, conn, addr):
        self.connected = True
        self.conn = conn
        self.addr = addr

        print(f"[NEW CONNECTION] {self.addr} Connected.")
        self.readThread.start()
        self.writeThread.start()

        while self.connected:
            message = self.conn.recv(self.header).decode("utf-8")
            if message:
                self.iBuffer.put(message)
                self.oBuffer.put(message)

            print(f"[{self.addr} {message}]")

        print(f"DISCONNECTING FROM [{self.addr}]")

        self.conn.close()
        self.writeThread.join()
        self.readThread.join()
        self.completed = True


class Server:
    def __init__(self):
        self.header = 1024
        self.port = 50005
        self.currentConnections = []
        self.host = "127.0.0.1"
        self.address = (self.host, self.port)
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.addr = None
        self.connection = None
        self.connectionThreads = []

    def start(self):
        self.serv.bind(self.address)
        self.serv.listen()
        self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        print(f"\n[LISTENING ON: ] {self.host}")

        while True:
            self.conn, self.addr = self.serv.accept()
            self.connection = ConnectionClass()

            connThread = threading.Thread(target=self.connection.handle_client,
                                          args=(self.conn, self.addr,), daemon=True).start()

            self.connectionThreads.append(connThread)
            print(self.connectionThreads)


if __name__ == '__main__':
    print("Starting Server")
    server = Server()
    server.start()
