# Credut: https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
##EOF_SIGNAL = b"END_OF_PACKET"
##def recvall(con,BUFFER_SIZE = 1024,EOF_SIGNAL = EOF_SIGNAL):
##    data = b""
##    while True:
##        packet = con.recv(BUFFER_SIZE)
##        data += packet
##        if len(packet) < BUFFER_SIZE or EOF_SIGNAL in packet:
##            break
##    data = data.replace(EOF_SIGNAL,b"",1)
##    return data

#CREDIT -> https://stackoverflow.com/questions/28583242/client-receiving-two-separate-message-as-one-with-python-socket
import struct,codecs

def Send(con,message):
    message = codecs.encode(str(message))
    con.send(struct.pack("i",len(message))+message)

def Recv(con):
    size = struct.unpack("i",con.recv(struct.calcsize("i")))[0]
    data = b""
    while len(data) < size:
        msg = con.recv(size-len(data))
        if not msg:
            raise Exception("Socket read error. Remote connection most likely terminated.")
        data += msg
    return codecs.decode(data)
            
