import socket
import threading
import ssl

# Fake NNTPS server: newsserver aka usenet server with TLS, with no articles
# Goal: testing TLS 1.3 on Ubuntu 18.10 and higher

# Base on https://stackoverflow.com/questions/23828264/how-to-make-a-simple-multithreaded-socket-server-in-python-that-remembers-client


class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(100)
        while True:
            client, address = self.sock.accept()
            print "Incoming connection from", address

            client.settimeout(5)
            #ctx = ssl.create_default_context()
            # ctx.options |= ssl.OP_NO_SSLv2
            #ctx.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
            #ctx.options &= ~ssl.OP_NO_SSLv3

            # wrap into SSL / TLS 
            sslconnstream = ssl.wrap_socket(client,
                                 server_side=True,
                                 ssl_version=ssl.PROTOCOL_TLS,
                                 certfile="/home/sander/.sabnzbd/admin/server.cert",
                                 keyfile="/home/sander/.sabnzbd/admin/server.key")
            print "SSL/TLS version:", sslconnstream.version()
   
            threading.Thread(target = self.listenToClient,args = (sslconnstream,address)).start()

    def listenToClient(self, client, address):
        size = 1024
        client.send("200 Welcome to FakeNewsserver!\r\n")
        while True:
            try:
                data = client.recv(size)
                if data:
                    # If a QUIT command, then respons 205 Goodbye
                    if data.upper().find('QUIT')==0:
                        client.send("205 Goodbye\r\n")
                        client.close()
                        print "Closing connection from", address
                        return False
                    else:
                        # ... otherwise always 480 Authentication Required
                        client.send("480 Authentication Required\r\n")
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False


if __name__ == "__main__":

    port_num = 2222
    print "FakeNewsserver listening on", port_num
    ThreadedServer('',port_num).listen()
    print " ... done"


