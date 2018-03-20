import Networking_System,json

class U_Node:
    def __init__(self):
##        self._address = address
        self._authenticated = False
        self._enable_block_send = True
        self._tx_filter = {}

    def get_authenticated(self):
        return self._authenticated
    def set_authenticated(self,value):
        self._authenticated = value

    def config(self,config_data):
        """
        Config comes in the form []
        items:
        enable_block_send:Boolean
        tx_filter:
        """
        for item in config_data:
            if item == "enable_block_send":
                self._enable_block_send = config_data[item]
            elif item == "tx_filter":
                self._tx_filter = config_data[item]

    def get_enable_block_send(self):
        return self._enable_block_send
    

##    def tx_filter(self,tx):
##        if 

            
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

    def Disconnect(self,Address,Target_Address):
        Message = {"Command":"Disconnect",
                              "Payload":{"Address":Target_Address}}
        self.Send(Address,Message)

    def Config(self,Address,Config):
        Message = {"Command":"Config",
                   "Payload":Config}
        self.Send(Address,Message)

    def Get_Connected_Addresses(self,Address,Target_Address):
        Message = {"Command":"Disconnect",
                   "Payload":{}}
        self.Send(Address,Message)

    def Connected_Addresses(self,Address,Addresses):
        Message = {"Command":"Connected_Addresses",
                   "Payload":Addresses}
        self.Send(Address,Message)

    def Get_UTXOs(self,Address,Address_List):
        Message = {"Command":"Get_UTXOs",
                   "Payload":Address_List}
        self.Send(Address,Message)

    def UTXOs(self,Address,UTXOs):
        Message = {"Command":"UTXOs",
                   "Payload":UTXOs}
        self.Send(Address,Message)
        
        
        
