import socket,Threading_System,queue,Connection_System,time,recvall, threading
#Address is a tuple of ("IP",Port)
#Each "connection" has two socket pairs, Send and Recv, Send is the one the client formed, Recv is the one the client accepted.

                

def Create_Socket_Controller(Thread_Name,Command_Queue,Output_Queue,Max_Connections=15,TPort = 8000):
    SC = Socket_Controller(Thread_Name,Command_Queue,Output_Queue,Max_Connections,TPort)
    SC.main()

class Socket_Controller(Threading_System.Thread_Controller):
    _Name = ""
    def __init__(self,Thread_Name,Command_Queue,Output_Queue,Max_Connections=15,TPort = 8000):
        self._Thread_Name = "TC"+Thread_Name+">"
        self._Command_Queue = Command_Queue
        self._Output_Queue = Output_Queue
        self._Max_Connections = Max_Connections

        self._Threads = {}
        self._Return_Queues = {"I":queue.Queue(), "O":queue.Queue()}
        self._Addresses = set()

    
        self.Create_Thread("Incoming_Con",TargetCommand = Connection_System.Incoming_Connection_Handler,TargetArgs = (self._Return_Queues["I"],TPort))
        self.Create_Thread("Outgoing_Con",TargetCommand = Connection_System.Outgoing_Connection_Handler,TargetArgs = (self._Return_Queues["O"],TPort))

    def Add_Return_Queue(self,Address,Mode):
        return_queue = queue.Queue()
        self._Return_Queues[Address+(Mode,)] = return_queue
        return return_queue
        
    def main(self):
        self._Exit = False
        while not self._Exit:
            try:
                self.Process_Command_Queue()
                self.Process_IO_Con_Queues()
                self.Process_Socket_Queues()
            except Exception as e:
                print(self._Thread_Name," Error in Socket controller",e)
            time.sleep(0.1)
            
            
              
                

    def Process_Command_Queue(self):
        while not self._Command_Queue.empty():
            data = self._Command_Queue.get()  #Data will be in form ("Target","Command","Arguments")
            Target,Command,Arguments = data[0],data[1],data[2]
            if Target == "Controller":
                if Command == "Kill_Connection":
                    self.Kill_Connection(*Arguments)
                elif Command == "Create_Connection":
                    self.Create_Connection(*Arguments)
                elif Command == "GetAddresses":
                    self.Get_Addresses()
                    print("HI")
                elif Command == "Reset":
                    self.Reset(*Arguments)
                elif Command == "Exit":
                    self.Reset(*Arguments)
                    self._Exit = True

            else:
                self.PassData(Target,Command,Arguments)

    def Process_IO_Con_Queues(self):  #Checks the Incoming and Outcoming sockets.
        for letter in ["I","O"]:
            return_queue = self._Return_Queues[letter]
            while not return_queue.empty():
                data = return_queue.get()      #Gets a new connection object
                addr,conn = data
                if addr in self._Addresses:
                    self.Kill_Connection(addr)
                self._Addresses.add(addr)
                O_Return_Queue,I_Return_Queue = self.Add_Return_Queue(addr,"S"),self.Add_Return_Queue(addr,"R")
                self.Create_Thread(addr+("S",),TargetCommand = Send_Thread,TargetArgs = (addr,conn,O_Return_Queue))
                self.Create_Thread(addr+("R",),TargetCommand = Recv_Thread,TargetArgs = (addr,conn,I_Return_Queue))
                self.Return_New_Connection(addr)
                

    def Process_Socket_Queues(self):  #Checks all the thread return queues , processing them and returning the data where needed.
        for Base_Address in list(self._Addresses): # List to prevent changing size error if a node disconnects
            for letter in ["S","R"]:          #Iterates through each copy of items.
                Address = Base_Address + (letter,)       # Forms the (IP,Port,Mode)
                while not self._Return_Queues[Address].empty():
                    data = self._Return_Queues[Address].get()
                    Message,Data = data
                    if Message == "Error":
                        self.Kill_Connection(Base_Address)
                        self.Return_Connection_Failure(Base_Address)
                    else:
                        self._Output_Queue.put(Data)
                
    

    def Get_Addresses(self):
        self._Output_Queue.put({"Command":"SC_Addresses",
                                "Address":"SC",
                                "Payload":{"Addresses":self._Addresses}})
            

    def Kill_Connection(self,Address):
        if Address+("S",) in self._Threads:
            self.Close_Thread(Address+("S",)) #Closes the Send Connection
            self.Close_Thread(Address+("R",)) #Closes the Recv connection
            self._Addresses.remove(Address)

    def Create_Connection(self,Address):  #Creates a connection to the given address
        Outgoing_Con_Queue = self._Threads["Outgoing_Con"].Get_Queue()
        Outgoing_Con_Queue.put(("Connect",Address))

    def PassData(self,Target,Command,Arguments):
        if Target in self._Threads:
            Target_Queue = self._Threads[Target].Get_Queue()
            Target_Queue.put((Command,Arguments))

    def Return_New_Connection(self,Address):  #Inform that peer has connected
        self._Output_Queue.put({"Command":"Peer_Connected",
                                "Address":"SC",
                                 "Payload":{"Address":Address}})

    def Return_Connection_Failure(self,Address):   #Inform that peer has disconnected
        self._Output_Queue.put({"Command":"Peer_Disconnected",
                                "Address":"SC",
                                 "Payload":{"Address":Address}})


class Basic_Socket_Interface:
    def __init__(self,Max_Connections = 15,TPort = 8000):
        self._SC_Out_Queue = queue.Queue()
        self._Command_Queue = Threading_System.Create_Controller()
        self._Command_Queue.put(("Controller","Create_Thread",("SC",Create_Socket_Controller,(self._SC_Out_Queue,Max_Connections,TPort))))
        self._lock = threading.Lock()

    def Kill_Connection(self,Address):
        self._Command_Queue.put(("SC","Controller","Kill_Connection",(Address,)))

    def Create_Connection(self,Address):
        self._Command_Queue.put(("SC","Controller","Create_Connection",(Address,)))

    def GetAddresses(self):
        self._Command_Queue.put(("SC","Controller","GetAddresses",()))

    def Send(self,Address,Payload):
        self._Command_Queue.put(("SC",Address+("S",),"Send",Payload))

    def SC_Reset(self):
        self._Command_Queue.put(("SC","Controller","Reset",()))

    def SC_Exit(self):
        self._Command_Queue.put(("Exit",()))

    def Output_Queue_Empty(self):
        return self._SC_Out_Queue.empty()

    def Get_Item(self):
        return self._SC_Out_Queue.get()

    def Get_Output_Queue(self):
        return self._SC_Out_Queue
    
    #Lock component to ensure correct order of access for certain program components
    def get_lock_object(self):
        return self._lock

    def acquire_lock(self,blocking = True, timeout = -1):
        return self._lock.acquire(blocking, timeout)

    def release_lock(self):
        self._lock.release()

    def is_locked(self):
        return self._lock.locked()

class Socket_Interface_Extender:
    def Error(self,address,command, error_code = 2, error_info = "An error occured executing the command"):
        #Generic Error message - Used to describe that an error occured and what command caused it.
        message = {"Command":"Error",
                   "Payload":{"Command":command,
                              "Error_Code":error_code,
                              "Error_Info":error_info}}
    def Ping(self,Address,Time):
        #Used to ping a node, Time send is used to attempt to produce a ping statistic
        Ping_Message = {"Command":"Ping",
                       "Payload":{"Time_Sent":Time}}
        self.Send(Address,Ping_Message)

    def Ping_Response(self,Address,Time_Sent,Time):
        #Pong the node back, Time payload used to estimate a time for a ping.
        Ping_Response_Message = {"Command":"Ping_Response",
                                 "Payload":{"Time_Sent":Time_Sent,
                                            "Remote_Time_Sent":Time}}
        self.Send(Address,Ping_Response_Message)
        

    def Get_Node_Info(self,Address):
        #Get information about a node such as version, flags and type
        Get_Node_Info_Message = {"Command":"Get_Node_Info",
                             "Payload":{}}
        self.Send(Address,Get_Node_Info_Message)

    def Node_Info(self,Address,Version,Type,Flags):
        #Returns the Node Info request - Type can be either UMC - Priviliged user to main connection, Node - Conventional node or other
        Node_Info_Message = {"Command":"Node_Info",
                             "Payload":{"Version":Version,
                                        "Type":Type,
                                        "Flags":Flags}}
        self.Send(Address,Node_Info_Message)
        

    def Time_Sync(self,Address):
        #Get a time sync from a node. This requests the time of the remote node.
        Time_Sync_Message = {"Command":"Time_Sync",
                             "Payload":{}}
        self.Send(Address,Time_Sync_Message)

    def Time_Sync_Response(self,Address,Time):
        #respond to a time sync request. This takes the local time and sends it back.
        Time_Sync_Response_Message = {"Command":"Time_Sync_Response",
                                      "Payload":{"Time":Time}}
        self.Send(Address,Time_Sync_Response_Message)
        

    def Alert(self,Address,Username,Message,TimeStamp,Signature,Current_Level):
        #Alert the entire network using the message. Signed by a known user. TimeStamp to ensure can only be sent during that time.
        Alert_Message = {"Command":"Alert",
                         "Payload":{"Username":Username,
                                    "Message":Message,
                                    "TimeStamp":TimeStamp,
                                    "Signature":Signature,
                                    "Current_Level":Current_Level}}
        self.Send(Address,Alert_Message)

    def Exit(self,Address):
        #Request the connection between this and the remote node to end.
        Exit_Message = {"Command":"Exit",
                        "Payload":{}}
        self.Send(Address,Exit_Message)

    def Exit_Response(self,Address):
        #Acknowledge the node's desire to exit the connection.
        Exit_Response_Message = {"Command":"Exit_Response",
                                 "Payload":{}}
        self.Send(Address,Exit_Response_Message)
        

    def Get_Peers(self,Address):
        #Get_Peers is used to obtain the known peers for a remote node.
        Get_Peers_Message = {"Command":"Get_Peers",
                             "Payload":{}}
        self.Send(Address,Get_Peers_Message)

    def Get_Peers_Response(self,Address,Peers):
        #Peers is list containing addresses of peers. Details on node type are not accepted
        Get_Peers_Response_Message = {"Command":"Get_Peers_Response",
                                      "Payload":{"Peers":Peers}}
        self.Send(Address,Get_Peers_Response_Message)


    def Get_Address(self,Address):
        # Get the address of ones own node by asking the remote node what the address the current node is seen under.
        Get_Address_Message = {"Command":"Get_Address",
                               "Payload":{}}
        self.Send(Address,Get_Address_Message)

    def Get_Address_Response(self,Address):
        #Used to notify a node what address it is seen under.
        Get_Address_Response_Message = {"Command":"Get_Address_Response",
                               "Payload":{"Address":Address}}
        self.Send(Address,Get_Address_Response_Message)


    ################################################

    def Inv(self,Address,Inventory_List):
        #Inventory provides a list of all items the node has to offer. This contains dictionaries of {Type,Payload} where payload typically is a hash.
        Inv_Message = {"Command":"Inv",
                       "Payload":Inventory_List}
        self.Send(Address,Inv_Message)

    def Get_Blocks(self,Address,Known_Block_Hashes_List):
        #Get Blocks is used to syncronise the current node with the remote node by trying to find the next best block hash known by both nodes.
        Get_Blocks_Message = {"Command":"Get_Blocks",
                               "Payload":Known_Block_Hashes_List}
        self.Send(Address,Get_Blocks_Message)

    def Get_Blocks_Full(self,Address,Block_Hashes_List):
        #Used to obtain full block data in json format. Block_Hashes_List contains the desired block hashes in order.
        Get_Blocks_Full_Message = {"Command":"Get_Blocks_Full",
                                   "Payload":Block_Hashes_List}
        self.Send(Address,Get_Blocks_Full_Message)

    def Blocks(self,Address,Blocks_List):
        #Contains the ordered list of json blocks.
        Blocks_Message = {"Command":"Blocks",
                          "Payload":Blocks_List}
        self.Send(Address,Blocks_Message)

    def Get_Transactions(self,Address,Transaction_Hash_List):
        #Used to obtain the full json of the given transaction hashes.
        Message = {"Command":"Get_Transactions",
                   "Payload":Transaction_Hash_List}
        self.Send(Address,Message)

    def Transactions(self,Address,Transactions_List):
        #Used to send the full json of transactions.
        Transactions_Message = {"Command":"Transactions",
                                "Payload":Transactions_List}
        self.Send(Address,Transactions_Message)


class UMC_Interface_Extension:
    def Shutdown(self,Address):
        #Request the Node to shutdown
        Message = {"Command":"Shutdown",
                            "Payload":{}}
        self.Send(Address,Message)

    def Connect(self,Address,Target_Address):
        #Request the node to connect to the target address
        Message = {"Command":"Connect",
                    "Payload":{"Address":Target_Address}}
        self.Send(Address,Message)

    def Disconnect(self,Address,Target_Address):
        #Request the node to disconnect from the target address
        Message = {"Command":"Disconnect",
                              "Payload":{"Address":Target_Address}}
        self.Send(Address,Message)

#####################

    def Config(self,Address,Config):
        #Used to define the configuration for the sending UMC on the node it is targeting
        Message = {"Command":"Config",
                   "Payload":Config}
        self.Send(Address,Message)

    def Get_Connected_Addresses(self,Address):
        #Request the addresses the node is connected to.
        Message = {"Command":"Disconnect",
                   "Payload":{}}
        self.Send(Address,Message)

    def Connected_Addresses(self,Address,Addresses):
        #Send back the list of connected addresses 
        Message = {"Command":"Connected_Addresses",
                   "Payload":Addresses}
        self.Send(Address,Message)

#####################

    def Get_UTXOs(self,Address,Address_List):
        #Get the UTXOs which match an address in the address list.
        Message = {"Command":"Get_UTXOs",
                   "Payload":Address_List}
        self.Send(Address,Message)

    def UTXOs(self,Address,UTXOs):
        #Send a list of UTXOs
        Message = {"Command":"UTXOs",
                   "Payload":UTXOs}
        self.Send(Address,Message)
        
###################
        
    def Get_Authentication(self,Address):
        #Request the start of an authentication procedure to become an authenticated UMC connection
        Message = {"Command":"Get_Authentication",
                   "Payload":{}}
        self.Send(Address,Message)

    def Authentication_Challenge(self,Address,salt):
        #Send the challenge to the UMC
        Message = {"Command":"Authentication_Challenge",
                   "Payload":{"Salt":salt}}
        self.Send(Address,Message)

    def Authentication(self,Address,Hash):
        #Return the hash to the node to prove the UMC has the secret key
        Message = {"Command":"Authentication",
                   "Payload":{"Hash":Hash}}
        self.Send(Address,Message)

    def Authentication_Outcome(self,Address,Outcome):
        #Respond to an authentication with the outcome of the authentication.
        Message = {"Command":"Authentication_Outcome",
                   "Payload":{"Outcome":Outcome}}
        self.Send(Address,Message)

###################

    def Sign_Alert(self,Address,Username,Message,TimeStamp,Level):   #Get the node to sign the alert
        Message = {"Command":"Sign_Alert",
                   "Payload":{"Username":Username,
                              "Message":Message,
                              "TimeStamp":TimeStamp,
                              "Level":Level}}
        self.Send(Address,Message)

    def Signed_Alert(self,Address,Signature):
        Message = {"Command":"Sign_Alert",
                   "Payload":{"Signature":Signature}}
        self.Send(Address,Message)

##################

    def Get_Wallet_Addresses(self,Address):
        Message = {"Command":"Get_Wallet_Addresses",
                   "Payload":{}}
        self.Send(Address,Message)

    def Wallet_Addresses(self,Address,Wallet_Addresses):
        Message = {"Command":"Wallet_Addresses",
                   "Payload":Wallet_Addresses}
        self.Send(Address,Message)

    def New_Wallet_Address(self,Address):
        Message = {"Command":"New_Wallet_Address",
                   "Payload":{}}
        self.Send(Address,Message)

    def Sign_Message(self,Address,Wallet_Address,Sign_Message):
        Message = {"Command":"Sign_Message",
                   "Payload":{"Sign_Message":Sign_Message,
                              "Wallet_Address":Wallet_Address}}
        self.Send(Address,Message)

    def Signed_Message(self,Address,Signature):
        Message = {"Command":"Signed_Message",
                   "Payload":{"Signature":Signature}}
        self.Send(Address,Message)

    def Get_Wallet_Address_Public_Key(self,Address,Wallet_Address):
        Message = {"Command":"Get_Wallet_Address_Public_Key",
                   "Payload":{"Wallet_Address":Wallet_Address}}
        self.Send(Address,Message)

    def Wallet_Address_Public_Key(self,Address,Public_Key):
        Message = {"Command":"Wallet_Address_Public_Key",
                   "Payload":{"Public_Key":Public_Key}}
        self.Send(Address,Message)

    def Get_Wallet_Address_Private_Key(self,Address,Wallet_Address):
        Message = {"Command":"Get_Wallet_Address_Private_Key",
                   "Payload":{"Wallet_Address":Wallet_Address}}
        self.Send(Address,Message)

    def Wallet_Address_Private_Key(self,Address,Private_Key):
        Message = {"Command":"Wallet_Address_Private_Key",
                   "Payload":{"Private_Key":Private_Key}}
        self.Send(Address,Message)

    def Dump_Wallet(self,Address):
        Message = {"Command":"Dump_Wallet",
                   "Payload":{}}
        self.Send(Address,Message)

    def Wallet_Dump_Data(self,Address,Wallet_Dump):
        Message = {"Command":"Wallet_Dump_Data",
                   "Payload":{"Wallet_Dump":Wallet_Dump}}
        self.Send(Address,Message)

    def Get_Wallet_UTXOs(self,Address,Wallet_Address_List = []):        #Response is a UTXO message
        Message = {"Command":"Get_Wallet_UTXOs",
                   "Payload":{"Wallet_Address_List":Wallet_Address_List}}
        self.Send(Address,Message)

    def Get_Wallet_Transactions(self,Address,Wallet_Address_List = []): #Response is a Transaction message
        Message = {"Command":"Get_Wallet_Transactions",
                   "Payload":{"Wallet_Address_List":Wallet_Address_List}}
        self.Send(Address,Message)

        








class Socket_Interface(Basic_Socket_Interface,Socket_Interface_Extender,UMC_Interface_Extension):
    def __binder(self):     #Used to form the new class
        pass            

        
def Make_Inv_Item(Type,Payload):
    return {"Type":Type,
            "Payload":Payload}
        




class Network_Node:
    def __init__(self,Address,Version = -1,Type = "",Flags = [],Last_Contact = time.time(),Last_Ping = 100,Remote_Time = time.time()):
        self._Address = Address
        self._Version = Version
        self._Type = Type
        self._Flags = Flags
        self._Last_Contact = Last_Contact
        self._Last_Ping = Last_Ping
        self._Remote_Time = Remote_Time
        self._Authentication = False
        self._Enable_Block_Send = True

    def Get_Version(self):
        return self._Version
    def Set_Version(self,Version):
        self._Version = Version

    def Get_Address(self):
        return self._Address
    def Set_Address(self,Address):
        self._Address = Address

    def Get_Type(self):
        return self._Type
    def Set_Type(self,Type):
        self._Type = Type

    def Get_Flags(self):
        return self._Flags
    def Set_Flags(self,Flags):
        self._Flags = Flags

    def Get_Last_Contact(self):
        return self._Last_Contact
    def Set_Last_Contact(self,Time):
        self._Last_Contact = Time

    def Get_Last_Ping(self):
        return self._Last_Ping
    def Set_Last_Ping(self,Ping):
        self._Last_Ping = Ping

    def Get_Remote_Time(self):
        return self._Remote_Time
    def Set_Remote_Time(self,Time):
        self._Remote_Time = Time

    def Is_Authenticated(self):
        return self._Authentication is True
    def Get_Authentication(self):
        return self._Authentication
    def Set_Authentication(self,Value):
        self._Authentication = Value

    def Get_Enable_Block_Send(self):
        return self._Enable_Block_Send

    
        
        
        
        
        
        

        
        
                                 
                                 



    


def Send_Thread(Thread_Name,Command_Queue,addr,Connection,Return_Queue):
    Exit = False
    while not Exit:
        try:
            data = Command_Queue.get()
            Command,Data = data
##            print("IS THIS OK TO SEND DATA : ",Data)
            if Command == "Send":
                recvall.Send(Connection,Data)
            elif Command == "Exit":
                Exit = True
                Connection.close()
        except Exception as e:
            print("Exception in sending thread ",Thread_Name,":",e,".Disconnecting")
            Exit = True
            Return_Queue.put(("Error",()))
            
    print(Thread_Name,addr," Send is closing")


def Recv_Thread(Thread_Name,Command_Queue,addr,Connection,Return_Queue):
    Exit = False
    while not Exit:
        try:
            obtained_data = recvall.Recv(Connection)
            obtained_data["Address"] = addr
            Return_Queue.put(("Message",obtained_data))

            
            if not Command_Queue.empty():
                data = Command_Queue.get()
                Command,Data = data
                if Command == "Exit":
                    Exit = True
                    Connection.close()
        except Exception as e:
            print("Exception in Recv thread ",Thread_Name,":",e,".Disconnecting")
            Exit = True
            Return_Queue.put(("Error",()))
            
    print(Thread_Name,addr," Recv is closing")
        
            
                    
        

    

    


                
                    
                    
            
        
