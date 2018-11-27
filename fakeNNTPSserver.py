# Fake NNTPS server: newsserver aka usenet server with TLS, with no articles
# Goal: testing TLS 1.3 on Ubuntu 18.10 and higher

# Based on https://stackoverflow.com/questions/23828264/how-to-make-a-simple-multithreaded-socket-server-in-python-that-remembers-client

import socket
import threading
import ssl

import logging
logging.basicConfig(filename='fakeNNTPSserver.log', format='%(asctime)s %(message)s', level=logging.INFO)
logging.info('fakeNNTPSserver started')


mycertfile="/etc/letsencrypt/live/news.appelboor.com/fullchain.pem"
mykeyfile="/etc/letsencrypt/live/news.appelboor.com/privkey.pem"


# mycertfile="/home/sander/.sabnzbd/admin/server.cert"
# mykeyfile="/home/sander/.sabnzbd/admin/server.key"


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
            #tnr = str(threading.current_thread()).split('(')[1].split(',')[0] # <Thread(Thread-4, started 1977611360)>
            logging.info("Incoming connection from %s", address)

            client.settimeout(5)
            #ctx = ssl.create_default_context()
            # ctx.options |= ssl.OP_NO_SSLv2
            #ctx.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_TLSv1_3
            #ctx.options &= ~ssl.OP_NO_SSLv3

            # wrap into SSL / TLS
            sslconnstream = ssl.wrap_socket(client,
                                 server_side=True,
                                 ssl_version=ssl.PROTOCOL_TLS,
                                 #certfile="/etc/letsencrypt/live/news.appelboor.com/fullchain.pem",
                                 #keyfile="/etc/letsencrypt/live/news.appelboor.com/privkey.pem"
				 certfile = mycertfile,
				 keyfile = mykeyfile
                            )


            logging.info("Connection from %s has TLS version %s", address, sslconnstream.version())
            # Handle in a thread:
            threading.Thread(target = self.listenToClient,args = (sslconnstream,address)).start()

    def listenToClient(self, client, address):
        size = 1024
        client.send("200 Welcome to FakeNewsserver!\r\n")

        tnr = str(threading.current_thread()).split('(')[1].split(',')[0] # <Thread(Thread-4, started 1977611360)>
        #print "SJ: tnr is ", tnr

        while True:
            try:
                data = client.recv(size)
                logging.debug("%s client said: %s", tnr, data.rstrip())

                if data:
                    # If a QUIT command, then respons 205 Goodbye
                    if data.upper().find('QUIT')==0:
                        client.send("205 Goodbye\r\n")
                        client.close()
                        logging.info("%s Closing connection from %s", tnr, address)
                        return False
                    elif data.upper().find('AUTHINFO USER')==0:
                        client.send("381 PASS required\r\n")
                    elif data.upper().find('AUTHINFO PASS')==0:
                        client.send("502 Access denied\r\n")

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
    port_num = 563
    logging.info("FakeNewsserver listening on %s", port_num)
    while True:
        try:
            ThreadedServer('',port_num).listen()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logging.warning("Exception: %s", message)
            #print message
            #except:
               #print "Oops"

    print " ... done"


