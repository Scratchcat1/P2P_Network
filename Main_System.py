import Networking_System,time,Database_System,Alert_System

class Time_Keeper:
    def __init__(self):
        self._Offset = 0
    def adjust(self,Desired_Time):
        self._Offset = Val_Limit(Desired_Time-time.time(),3600,-3600)  #Rearranged Offset + time.time = desired_time, offset max 1 hour
    def time(self):
        return time.time()+self._Offset
    def reset(self):
        self._Offset = 0
    def get_offset(self):
        return self._Offset

class Ticker:
    def __init__(self, Time_Period):
        self._Time_Period
        self._Last_Call = 0
    def is_go(self):
        if time.time() >= self._Time_Period+self._Last_Call:
            return True
        else:
            return False
    def wait(self):
        dtime = self._Last_Call+self._Time_Period - time.time()
        if dtime > 0:
            time.sleep(dtime)
        self._Last_Call = time.time()
    def reset(self):
        self._Last_Call = time.time()
    def zero(self):
        self._Last_Call = 0
    
        

def Val_Limit(Value,Max,Min):  #https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range-python
    return max(min(Value,Min),Max)

    
class Main_Handler:
    def __init__(self,Node_Info,Max_Connections = 15,Max_SC_Messages = 100):
        print("Starting Main_Handler...")
        self._DB = Database_System.DBConnection()
        self._Node_Info = Node_Info
        self._Max_SC_Messages = Max_SC_Messages
        self._Max_Connections = Max_Connections
        self._SI = Networking_System.Socket_Interface(Max_Connections)
        self._Network_Nodes = {}  #Address :Network_Node
        self._Time = Time_Keeper()

        self._Network_Nodes_Check_Timer = Timer(300)  #Every 300 seconds check nodes
        print("Main_Handler started.")

    def Main_Loop(self):
        while True:
            pass



    def Process_SC_Messages(self):
        Processed_Message_Number = 0
        while not self._SI.Output_Queue_Empty() and Processed_Message_Number < Max_SC_Messages:
            message = self._SI.Get_Item()
            Commands = {
                "Peer_Connected":self.On_Peer_Connected,
                "Peer_Disconnected":self.On_Peer_Disconnected,
                "Ping":self.On_Ping,
                "Ping_Response":self.On_Ping_Response,
                "Get_Node_Info":self.On_Get_Node_Info,
                "Node_Info":self.On_Node_Info,
                "Time_Sync":self.On_Time_Sync,
                "Time_Sync_Response":self.On_Time_Sync_Response,
                "Alert":self.On_Alert,
                "Exit":self.On_Exit,
                "Exit_Response":self.On_Exit_Response,
                "Get_Peers":self.On_Get_Peers,
                "Get_Peers_Response":self.On_Get_Peers_Response,
                "Get_Address":self.On_Get_Address,
                "Get_Address_Response":self.On_Get_Address_Response,
                    }

            if message["Command"] in Commands:
                Commands[message["Command"]](message)  #Execute the relevant command with the message as an argument
            if message["Address"] in self._Network_Nodes:
                self._Network_Nodes[message["Address"]].Set_Last_Contact(self._Time.time())  #Mark as last contact
                
                


    def On_Peer_Connected(self,Message):
        self._Network_Nodes[Message["Payload"]["Address"]] = Network_System.Network_Node(Message["Payload"]["Address"])
        self._SI.Get_Node_Info(Message["Payload"]["Address"])
    def On_Peer_Disconnected(self,Message):
        self._Network_Nodes.pop(Message["Payload"]["Address"],None)

    def On_Ping(self,Message):
        self._SI.Ping_Response(Message["Address"],Message["Payload"]["Time_Sent"],self._Time.time())
    def On_Ping_Response(self,Message):
        ping_time = Message["Payload"]["Remote_Time_Sent"]-Message["Payload"]["Time_Sent"]
        self._Network_Nodes[Message["Address"]].Set_Last_Ping(ping_time)

    def On_Get_Node_Info(self,Message):
        self._SI.Node_Info(Message["Address"],self._Node_Info.Get_Version(),self._Node_Info.Get_Type(),self._Node_Info.Get_Flags())
    def On_Node_Info(self,Message):
        Node = self._Network_Nodes[Message["Address"]]
        Node.Set_Version(Message["Payload"]["Version"])
        Node.Set_Type(Message["Payload"]["Type"])
        Node.Set_Flags(Message["Payload"]["Flags"])

    def On_Time_Sync(self,Message):
        self._SI.Time_Sync_Response(Message["Address"],self._Time.time())
    def On_Time_Sync_Response(self,Message):
        Node = self._Network_Nodes[Message["Address"]]
        Node.Set_Remote_Time(Message["Payload"]["Time"])

    def On_Alert(self,Message):
        if Alert_System.Alert_User_Verify(self._Time.time(),Message["Payload"]["Username"],Message["Payload"]["Message"],Message["Payload"]["TimeStamp"],Message["Payload"]["Signature"],Message["Payload"]["Level"]):
            for Address in self._Nodes:
                self._SI.Alert(Message["Payload"]["Username"],Message["Payload"]["Message"],Message["Payload"]["TimeStamp"],Message["Payload"]["Signature"],Message["Payload"]["Level"]-1)
        else:
            print("Invalid alert denied progress")

    def On_Exit(self,Message):
        self._SI.Exit_Response(Message["Address"])
        self._SI.Kill_Connection(Message["Address"])
    def On_Exit_Response(self,Message):
        self._SI.Kill_Connection(Message["Address"])

    def On_Get_Peers(self,Message):
        Peers = []
        for Node in self._Network_Nodes:
            Peers.append(Node.Get_Address())
        self._SI.Get_Peers_Response(Message["Address"],Peers)
    def On_Get_Peers_Response(self,Message):
        for peer in Message["Payload"]["Peers"]:
            self._DB.Add_Peer(peer["IP"],peer["Port"],"",[],self._Time.time(),1,Update_If_Need = False)#Transfer peer without trust in type , flags etc
            

    def On_Get_Address(self,Message):
        self._SI.Get_Address_Response(Message["Address"])
    def On_Get_Address_Response(self,Message):
        self._Node_Info.Set_Address(Message["Payload"]["Address"])

    




    def Spawn_Events(self):
        pass

    def Check_Network_Nodes(self):
        if self._Network_Nodes_Check_Timer.is_go():
            print("Checking nodes")
            self._Network_Nodes_Check_Timer.reset()
            if len(self._Network_Nodes) < 15:
                difference = 15-self._Network_Nodes
                
            for Node in self._Network_Nodes.values():
                if Node.Get_Last_Contact() > 20*60:
                    self._SI.Ping(Node.Get_Address(),self._Time.time())  #Ping to keep connection alive
                if Node.Get_Last_Contact() > 90*60:
                    self._SI.Kill_Connection(Node.Get_Address())
                    
                
        
        
        
        
        
        








        
