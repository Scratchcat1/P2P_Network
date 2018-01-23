import socket,Threading_System,queue,Connection_System,time,codecs,recvall
import json
#Address is a tuple of ("IP",Port)
#Each "connection" has two socket pairs, Send and Recv, Send is the one the client formed, Recv is the one the client accepted.

                

def Create_Socket_Controller(Thread_Name,Command_Queue,Output_Queue,Max_Connections=15):
    SC = Socket_Controller(Thread_Name,Command_Queue,Output_Queue,Max_Connections)
    SC.main()

class Socket_Controller(Threading_System.Thread_Controller):
    _Name = ""
    def __init__(self,Thread_Name,Command_Queue,Output_Queue,Max_Connections=15):
        self._Thread_Name = "TC"+Thread_Name+">"
        self._Command_Queue = Command_Queue
        self._Output_Queue = Output_Queue
        self._Max_Connections = Max_Connections

        self._Threads = {}
        self._Return_Queues = {"I":queue.Queue(), "O":queue.Queue()}
        self._Addresses = set()

    
        self.Create_Thread("Incoming_Con",TargetCommand = Connection_System.Incoming_Connection_Handler,TargetArgs = (self._Return_Queues["I"],))
        self.Create_Thread("Outgoing_Con",TargetCommand = Connection_System.Outgoing_Connection_Handler,TargetArgs = (self._Return_Queues["O"],))

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
                addr,Outgoing_Con,Incoming_Con = data

                self._Addresses.add(addr)
                O_Return_Queue,I_Return_Queue = self.Add_Return_Queue(addr,"S"),self.Add_Return_Queue(addr,"R")
                self.Create_Thread(addr+("S",),TargetCommand = Send_Thread,TargetArgs = (addr,Outgoing_Con,O_Return_Queue))
                self.Create_Thread(addr+("R",),TargetCommand = Recv_Thread,TargetArgs = (addr,Incoming_Con,I_Return_Queue))
                self.Return_New_Connection(addr)
                

    def Process_Socket_Queues(self):  #Checks all the thread return queues , processing them and returning the data where needed.
        for Base_Address in self._Addresses:
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
    def __init__(self,Max_Connections = 15):
        self._SC_Out_Queue = queue.Queue()
        self._Command_Queue = Threading_System.Create_Controller()
        self._Command_Queue.put(("Controller","Create_Thread",("SC",Create_Socket_Controller,(self._SC_Out_Queue,Max_Connections))))

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

    def Get_Item(self):
        return self._SC_Out_Queue.get()

    def Get_Output_Queue(self):
        return self._SC_Out_Queue

class Socket_Interface(Basic_Socket_Interface):
    def Ping(self,Address,Time):  #Used to ping a node
        Ping_Message = {"Command":"Ping",
                       "Payload":{"Time_Sent":Time}}
        self.Send(Address,Ping_Message)

    def Ping_Response(self,Address,Time_Sent,Time):  #Pong the node back
        Ping_Response_Message = {"Command":"Ping_Response",
                                 "Payload":{"Time_Sent":Time_Sent,
                                            "Remote_Time_Sent":Time}}
        self.Send(Address,Ping_Response_Message)
        

    def Time_Sync(self,Address):    #Get a time sync from a node
        Time_Sync_Message = {"Command":"Time_Sync",
                             "Payload":{}}
        self.Send(Address,Time_Sync_Message)

    def Time_Sync_Response(self,Address,Time):   #respond to a time sync request
        Time_Sync_Response_Message = {"Command":"Time_Sync_Response",
                                      "Payload":{"Time":Time}}
        self.Send(Address,Time_Sync_Response_Message)
        

    def Alert(self,Address,Username,Message,Signature,Level,Current_Level):   #Alert the entire network using the message
        Alert_Message = {"Command":"Alert",
                         "Payload":{"Username":Username,
                                    "Message":Message,
                                    "Signature":Signature,
                                    "Level":Level,
                                    "Current_Level":Current_Level}}
        self.Send(Address,Alert_Message)
        

    def Get_Node_Info(self,Address):    #Get information about a node.
        Get_Node_Info_Message = {"Command":"Get_Node_Info",
                             "Payload":{}}
        self.Send(Address,Get_Node_Info_Message)

    def Node_Info(self,Address,Version,Type,Flags):    #Returns the Node Info request
        Node_Info_Message = {"Command":"Node_Info",
                             "Payload":{"Version":Version,
                                        "Type":Type,
                                        "Flags":Flags}}
        self.Send(Address,Node_Info_Message)


    def Get_Address(self,Address):   # Get the address of ones own node
        Get_Address_Message = {"Command":"Get_Address",
                               "Payload":{}}
        self.Send(Address,Get_Address_Message)

    def Get_Address_Response(self,Address):
        Get_Address_Response_Message = {"Command":"Get_Address_Response",
                               "Payload":{"Address":Address}}
        self.Send(Address,Get_Address_Response_Message)


    def Get_Peers(self,Address):
        Get_Peers_Message = {"Command":"Get_Peers",
                             "Payload":{}}
        self.Send(Address,Get_Peers_Message)

    def Get_Peers_Response(self,Address,Peers):  #Peers is list containing addresses of peers
        Get_Peers_Response_Message = {"Command":"Get_Peers",
                                      "Payload":{"Peers":Peers}}
        self.Send(Address,Get_Peers_Response_Message)




class Network_Node:
    def __init__(self,Address,Type = "",Flags = [],Last_Contact = time.time(),Last_Ping = 100,Remote_Time = time.time()):
        self._Address = Address
        self._Type = Type
        self._Flags = Flags
        self._Last_Contact = Last_Contact
        self._Last_Ping = Last_Ping
        self._Remote_Time = Remote_Time

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

    
        
        
        
        
        
        

        
        
                                 
                                 



    


def Send_Thread(Thread_Name,Command_Queue,addr,Connection,Return_Queue):
    Exit = False
    while not Exit:
        try:
            data = Command_Queue.get()
            Command,Data = data
            print("IS THIS OK TO SEND DATA : ",Data)
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
            obtained_data = json.loads(obtained_data.replace("'","\""))
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
        
            
                    
        

    

    


                
                    
                    
            
        
