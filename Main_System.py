import Networking_System,time

class Time_Keeper:
    def __init__(self):
        self._Offset = 0
    def adjust(self,Desired_Time):
        self._Offset = Desired_Time-time.time()  #Rearranged Offset + time.time = desired_time
    def time(self):
        return time.time()+self._Offset
    def reset(self):
        self._Offset = 0
    def get_offset(self):
        return self._Offset

    
class Main_Handler:
    def __init__(self,Node_Info,Max_Connections = 15,Max_SC_Messages = 100):
        print("Starting Main_Handler...")
        self._Node_Info = Node_Info
        self._Max_SC_Messages = Max_SC_Messages
        self._Max_Connections = Max_Connections
        self._SI = Networking_System.Socket_Interface(Max_Connections)
        self._Network_Nodes = {}  #Address :Network_Node
        self._Time = Time_Keeper()
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
        print("ADD THIS IN. Verification, adjustment etc.")

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
        print("Add this in. Store it in database or something")

    def On_Get_Address(self,Message):
        self._SI.Get_Address_Response(Message["Address"])
    def On_Get_Address_Response(self,Message):
        self._Node_Info.Set_Address(Message["Payload"]["Address"])

    
        
        
        
        
        
        
        








        
