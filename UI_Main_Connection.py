import Networking_System,json

class U_Node:
    def __init__(self):
##        self._address = address
        self._authenticated = False

    def get_authenticated(self):
        return self._authenticated
    def set_authenticated(self,value):
        self._authenticated = value

class UMC(Networking_System.Socket_Interface):
##    def __init__(self,send_queue,recv_queue):
##        self._send_queue = send_queue
##        self._recv_queue = recv_queue
##
##    
##    def Send(self,address,message):
##        self._send_queue.put(json.dumps(message))
##
##    def can_Recv(self):
##        return not self._recv_queue.empty()
##
##    def Recv(self):
##        message = json.loads(self._recv_queue.get())
##        message["Address"] = "UMC"
##        return message


    def Shutdown(self,Address):
        Message = {"Command":"Shutdown",
                            "Payload":{}}
        self.Send(Address,Message)

    def Connect(self,Address,Target_Address):
        Message = {"Command":"Connect",
                           "Payload":{"Address":Target_Address}}
        self.Send(Address,Message)

    def Disconnect(self,Target_Address):
        Message = {"Command":"Disconnect",
                              "Payload":{"Address":Target_Address}}
        self.Send(Address,Message)

    
        
        
        
