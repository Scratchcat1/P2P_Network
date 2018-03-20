import Networking_System, Database_System, Alert_System, Chain_System, Block_System, Transaction_System, Mempool_System, Mining_System, base64_System, Wallet_System
import random,time,numpy,os

class Time_Keeper:
    def __init__(self):
        self._Offset = 0
    def adjust(self,Desired_Time):
        print(Desired_Time-time.time())
        self._Offset = Val_Limit(Desired_Time-time.time(),3600,-3600)  #Rearranged Offset + time.time = desired_time, offset max 1 hour
    def batch_adjust_time(self,time_lists):
        time_lists = numpy.array(time_lists)
        UQ,LQ = numpy.percentile(time_lists,75),numpy.percentile(time_lists,25)
        IQR = UQ-LQ
        filtered_time_list = list(filter(lambda x: x<UQ+IQR*1.5 and x>LQ-IQR*1.5,time_lists))  # Remove outlier
        self.adjust(sum(filtered_time_list)/len(filtered_time_list))
        
    def time(self):
        return time.time()+self._Offset
    def reset(self):
        self._Offset = 0
    def get_offset(self):
        return self._Offset

class Ticker:
    def __init__(self, Time_Period):
        self._Time_Period = Time_Period
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

class Rebroadcaster(Ticker):  #Ticker with storage
    def __init__(self,Time_Period = 60,max_size = 10000): 
        self._request_queue = []
        self._max_size = max_size
        super().__init__(Time_Period)#Broadcast inventory every timer_length seconds

    def add_block_hash(self,block_hash):
        self._request_queue.append({"Type":"Block","Payload":block_hash})

    def add_tx_hash(self,tx_hash):
        self._request_queue.append({"Type":"Transaction","Payload":tx_hash})

    def get_queue(self,reset = True):
        return_value = self._request_queue
        if reset:
            self.reset_queue()
        return return_value

    def reset_queue(self):
        self._request_queue = []

    def resize(self):   #If too large then purge older items
        if len(self._request_queue) > self._max_size:
            self._request_queue = self._request_queue[-self._maxsize:]
        
        
    
        

def Val_Limit(Value,Max,Min):   #https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range-python
    return max(min(Value,Max),Min)

    
class Main_Handler:
    def __init__(self,Node_Info = Networking_System.Network_Node("127.0.0.1"),Max_Connections = 15,Max_SC_Messages = 100, miner = None,wallet = Wallet_System.Wallet()):
        print("Starting Main_Handler...")
        self._db_con = Database_System.DBConnection()
        self._Node_Info = Node_Info
        self._Max_SC_Messages = Max_SC_Messages
        self._Max_Connections = Max_Connections
        self._miner = miner
        self._wallet = wallet
##        self._UMC_SI = Networking_System.Socket_Interface(TPort = 9000)
        self._SI = Networking_System.Socket_Interface(Max_Connections)
        self._Network_Nodes = {}  #Address :Network_Node
        self._UMCs = {}  #UMC_Node lists list
        self._Time = Time_Keeper()
        

        self._Mempool = Mempool_System.Mempool()  #Stores unconfirmed transactions
        self._Chain = Chain_System.Chain(self._Mempool)
        if self._miner:
            self._miner.set_mempool(self._Mempool)
            self.Restart_Miner()

        self._Network_Nodes_Check_Timer = Ticker(300)    #Every 300 seconds check nodes
        self._Block_Sync_Timer = Ticker(300)
        self._Rebroadcaster = Rebroadcaster()



        self._Node_Commands = {
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

            
            "Inv":self.On_Inv,
            "Get_Blocks":self.On_Get_Blocks,
            "Get_Blocks_Full":self.On_Get_Blocks_Full,
            "Blocks":self.On_Blocks,
            "Transactions":self.On_Transactions,
                }
        self._UMC_Commands = {
            "Shutdown":self.On_UMC_Shutdown,
            "Connect":self.On_UMC_Connect,
            "Disconnect":self.On_UMC_Disconnect,
            "Get_Authentication":self.On_UMC_Get_Authentication,
            "Authentication":self.On_UMC_Authentication,
            "Config":self.On_UMC_Config,
            "Get_Connected_Addresses":self.On_UMC_Get_Connected_Addresses,
            "Get_UTXOs":self.On_UMC_Get_UTXOs,
            "Sign_Alert":self.On_UMC_Sign_Alert,
            "Get_Wallet_Addresses":self.On_UMC_Get_Wallet_Addresses,
            "New_Wallet_Address":self.On_UMC_New_Wallet_Address,
                }
        print("Main_Handler started.")

    def Main_Loop(self):
        self._Exit = False
        while not self._Exit:
            self.Process_SC_Messages()
            self.Check_Network_Nodes()
            self.Run_Rebroadcast()
            self.Check_Sync_Blocks()
            self.Check_Miner()
            time.sleep(1/60)



    def Process_SC_Messages(self):
        Processed_Message_Number = 0
        while not self._SI.Output_Queue_Empty() and Processed_Message_Number < self._Max_SC_Messages:
            message = self._SI.Get_Item()

            if message["Command"] in self._UMC_Commands and message["Address"] in self._UMCs:
                self._UMC_Commands[message["Command"]](message)  #Execute the relevant UMC command with the message as an argument
            elif message["Command"] in self._Node_Commands:
                self._Node_Commands[message["Command"]](message)  #Execute the relevant Node command with the message as an argument
                
            if message["Address"] in self._Network_Nodes:
                self._Network_Nodes[message["Address"]].Set_Last_Contact(self._Time.time())  #Mark as last contact 
            elif message["Address"] in self._UMCs:
                self._UMCs[message["Address"]].Set_Last_Contact(self._Time.time())  #Mark as last contact for UMCs
            Processed_Message_Number +=1

            
    ################################
    #                              #
    #    Below is misc/maintanace  #
    #                              #
    ################################


    def On_Peer_Connected(self,Message):
        self._Network_Nodes[Message["Payload"]["Address"]] = Network_System.Network_Node(Message["Payload"]["Address"])
        self._SI.Get_Node_Info(Message["Payload"]["Address"])
    def On_Peer_Disconnected(self,Message):
        self._Network_Nodes.pop(Message["Payload"]["Address"],None)
        self._UMCs.pop(Message["Payload"]["Address"],None)

    def On_Ping(self,Message):
        self._SI.Ping_Response(Message["Address"],Message["Payload"]["Time_Sent"],self._Time.time())
    def On_Ping_Response(self,Message):
        ping_time = Message["Payload"]["Remote_Time_Sent"]-Message["Payload"]["Time_Sent"]
        self._Network_Nodes[Message["Address"]].Set_Last_Ping(ping_time)

    def On_Get_Node_Info(self,Message):
        self._SI.Node_Info(Message["Address"],self._Node_Info.Get_Version(),self._Node_Info.Get_Type(),self._Node_Info.Get_Flags())
    def On_Node_Info(self,Message):
        if Message["Address"] in self._Network_Nodes:
            Node = self._Network_Nodes[Message["Address"]]
        else:
            Node = self._UMCs[Message["Address"]]
            
        Node.Set_Version(Message["Payload"]["Version"])
        Node.Set_Type(Message["Payload"]["Type"])
        Node.Set_Flags(Message["Payload"]["Flags"])
        if Message["Payload"]["Type"] == "UMC":
            self._UMCs[Message["Address"]]= Node        #Move node to UMC
            self._Network_Nodes.pop(Message["Address"],None) #Remove node from NetworkNodes
        elif Message["Address"] in self._UMCs:
            self._UMCs.pop(Message["Address"],None) #Remove node from UMCs if downgrading
            

    def On_Time_Sync(self,Message):
        self._SI.Time_Sync_Response(Message["Address"],self._Time.time())
    def On_Time_Sync_Response(self,Message):
        Node = self._Network_Nodes[Message["Address"]]
        Node.Set_Remote_Time(Message["Payload"]["Time"])

    def On_Alert(self,Message):
        if Alert_System.Alert_User_Verify(self._db_con,self._Time.time(),Message["Payload"]["Username"],Message["Payload"]["Message"],Message["Payload"]["TimeStamp"],Message["Payload"]["Signature"],Message["Payload"]["Level"]):
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
            self._db_con.Add_Peer(peer["IP"],peer["Port"],"",[],self._Time.time(),1,Update_If_Need = False)#Transfer peer without trust in type , flags etc
            

    def On_Get_Address(self,Message):
        self._SI.Get_Address_Response(Message["Address"])
    def On_Get_Address_Response(self,Message):
        self._Node_Info.Set_Address(Message["Payload"]["Address"])

    
    #####################################################################


    ################################
    #                              #
    #    Below is blockchain etc   #
    #                              #
    ################################

    def On_Inv(self,Message):
        for item in Message["Payload"]:
            if item["Type"] == "Block":
                if not self._Chain.has_block(item["Payload"]):  #If not yet has block
                    pass                                        #Add to request block queue
            elif item["Type"] == "Transaction":
                if not self._Mempool.has_tx(item["Payload"]):   #If does not currently have transaction
                    pass                                        #Reqiest transaction

    def On_Get_Blocks(self,Message):  #On remote needs to update chain
        Found = False
        for block_hash in Message["Payload"]:                   # for each hash known to remote
            if self._db_con.Is_Best_Chain_Block(block_hash):
                self._SI.Inv(Message["Address"],self._db_con.Find_Best_Chain_Section(block_hash))  #Send next best hashes once found best chain connection
                Found = True
                break
            
        if not Found: # If remote blockchain is completely broken
            self._SI.Inv(Message["Address"],self._db_con.Find_Best_Chain_Section(self._db_con.Get_Best_Chain_Block(0)[0][0])) #If broken send next hashes from genesis.
                
    def On_Get_Blocks_Full(self,Message):               #On remote node wants full blocks
        block_jsons = []
        for block_hash in Message["Payload"]:
            try:
                block_jsons.append(self._Chain.get_block_json(block_hash))
            except:
                print("Remote tried to request non existant block with block hash:",block_hash)
        self._SI.Blocks(Message["Address"],block_jsons)
            

    def On_Blocks(self,Message):                        #When getting the full block data
        for block_json in Message["Payload"]:
            block = Block_System.Block()
            block.import_json(block_json)
            if block.Verify(self._Time.time(),self._Chain.get_difficulty()):
                self._Chain.add_block(block)            #Add block if it valid
                self._Rebroadcaster.add_block_hash(block.Get_Block_Hash())
                if self._Chain.get_highest_block_hash() == block.Get_Block_Hash():   #If this is the highest block
                    self.Restart_Miner()                #Restart the miner if need be.
                self.UMC_Block_Send(block)
                

    def On_Transactions(self,Message):
        for tx_json in Message["Payload"]:
            tx = Transaction_System.Transaction()
            tx.json_import(tx_json)
            if tx.Verify():
                self._Mempool.add_transation_json(tx.Transaction_Hash(),tx_json,tx.Verify_Values())
                self._Rebroadcaster.add_tx_hash(tx.Transaction_Hash())
                
            
                                    


    



    #####################################################################
             
                
            

    def Check_Network_Nodes(self):
        if self._Network_Nodes_Check_Timer.is_go():
            print("Checking nodes")
            self._Network_Nodes_Check_Timer.reset()
            if len(self._Network_Nodes) < 15:
                difference = 15-len(self._Network_Nodes)
                peers = self._db_con.Get_Peers(Limit = difference)
                for peer in peers:
                    if (peer[0],peer[1]) not in self._Network_Nodes:    #If not already connected to node
                        self._SI.Create_Connection((peer[0],peer[1]))   #Create connection to node
                
            for Node in self._Network_Nodes.values():
                if Node.Get_Last_Contact() > 20*60:
                    self._SI.Ping(Node.Get_Address(),self._Time.time())  #Ping to keep connection alive
                if Node.Get_Last_Contact() > 90*60:
                    self._SI.Kill_Connection(Node.Get_Address())


    def Run_Rebroadcast(self):
        if self._Rebroadcaster.is_go():
            self._Rebroadcaster.reset()
            for address in random.sample(list(self._Network_Nodes),min(8,len(self._Network_Nodes))):
                self._SI.Inv(address,self._Rebroadcaster.get_queue(reset = False))
            self._Rebroadcaster.reset_queue()

    def Check_Sync_Blocks(self):
        if self._Block_Sync_Timer.is_go():
            self._Block_Sync_Timer.reset()
            if self._db_con.Get_Highest_Work_Block()[0][5] < self._Time.time() - 24*3600:
                print("Highest block to old, searching for new blocks")
                for address in random.sample(list(self._Network_Nodes),min(1,len(self._Network_Nodes))):    #Single node only, randomly selected, none if no connections 
                    known_hashes = self._db_con.Find_Best_Known_Pattern(self._Chain.get_highest_block_hash())
                    self._SI.Get_Blocks(address,known_hashes)

    def Check_Miner(self):
        if self._miner:
            if self._miner.has_found_block():
                block = self._miner.get_block()
##                print(block.export_json())
                internal_block_message = {"Command":"Blocks",
                                          "Address":("127.0.0.1",None),
                                          "Payload":[block.export_json()]}  #Includes generic address for localhost in case one wants to check if one created the block
                self.On_Blocks(internal_block_message)           #Add block to chain normally. This also restarts the miner

                    
    def Restart_Miner(self):
        if self._miner:
            block_info = self._db_con.Get_Highest_Work_Block()
            self._miner.restart_mine(self._Time.time(),self._Chain.get_difficulty(),block_info[0][1]+1,block_info[0][0])  #Start mining on the highest block.
        
        
    #######################################################################

    #################################
    #                               #
    #  UserMainConnection commands  #
    #                               #
    #################################

    def UMC_Block_Send(self,block):
        for UMC_Address,UMC in self._UMCs.values():
            if UMC.Get_Enable_Block_Send():
                self._SI.Blocks(UMC_Address,[Block])

##    def UMC_Check(self):
##        while not self._UMC_SI.Output_Queue_Empty():            
##            message = self._UMC_SI.Get_Item()
##            
##
##            if message["Command"] in self._UMC_Commands:
##                self._UMC_Commands[message["Command"]](message)
##            elif message["Command"] in self._Node_Commands:
##                self._Node_Commands[message["Command"]](message)  #Execute the relevant command with the message as an argument
##
    def On_UMC_Connect(self,message):
        self._SI.Create_Connection(message["Payload"]["Address"])
    def On_UMC_Disconnect(self,message):
        self._SI.Create_Connection(message["Payload"]["Address"])

    def On_UMC_Shutdown(self,message):
        self._Exit = True
        print("MAIN HANDLER IS SHUTTING DOWN")

    def On_UMC_Get_Authentication(self,message):
        salt = base64_System.str_to_b64(os.urandom(64))
        SECRET_KEY = 'vql5apinpc0ehjpc1vzuhcncd4tl0heifaimg9heckfg8+q9sbpidryer+utu2gf/ify1b0fmsd8\nbzipih53tvryuj9u0kqnifcinc3vj75mvgnpianj+bu7wlj7vxwbgjwq/jyufkxtxpimh572woxx\ncha6nllvgacc05jekwe=\n'
        key = hashlib.sha256((salt+SECRET_KEY).encode()).hexdigest()
        self._UMCs[message["Address"]].Set_Authentication(key)
        self._SI.Authentication_Challenge(message["Address"],salt)

    def On_UMC_Authentication(self,message):
        if message["Payload"]["Hash"] == self._UMCs[message["Address"]].Get_Authentication():
            self._UMCs[message["Address"]].Set_Authentication(True)
            self._SI.Authentication_Outcome(message["Address"],True)
        else:
            self._SI.Authentication_Outcome(message["Address"],False)

        
##    def On_UMC_Connected(self,Message):
##        self._UMCs[Message["Payload"]["Address"]] = UI_Main_Connection.U_Node(Message["Payload"]["Address"])
##    def On_UMC_Disconnected(self,Message):
##        self._UMCs.pop(Message["Payload"]["Address"],None)
    def On_UMC_Config(self,Message):
        self._UMCs[Message["Address"]].config(Message["Payload"])

    def On_UMC_Get_Connected_Addresses(self,Message):
        self._UMC_SI.Connected_Addresses(Message["Address"],list(self._Network_Nodes))

    def On_UMC_Get_UTXOs(self,Message):
        UTXOs = self._DB.Get_UTXOs_Match(Message["Payload"])
        self._UMC_SI.UTXOs(Message["Address"],UTXOs)


##############

    def On_UMC_Sign_Alert(self,Message):
        alert_details = Message["Payload"]
        success,signature = Alert_System.Sign_Alert(self._db_con, alert_details["Username"], alert_details["Message"], alert_details["TimeStamp"], alert_details["Level"])
        if success:
            self._SI.Signed_Alert(Message["Address"],signature)
        else:
            #Sig contains error message if failed
            self._SI.Error(Message["Address"],"Sign_Alert",error_info = signature)

    def On_UMC_Get_Wallet_Addresses(self,Message):
        self._SI.Wallet_Addresses(Message["Address"],self._wallet.Get_Addresses())

    def On_UMC_New_Wallet_Address(self,Message):
        #Generate new address and save wallet
        self._SI.Wallet_Addresses(Message["Address"],[self._wallet.Generate_New_Address()])
        self._wallet.Save_Wallet()
        
    def On_Sign_Message(self,Message):
        if self._Wallet.has_address(Message["Payload"]["Wallet_Address"]):
            signature = self._Wallet.sign(Message["Payload"]["Wallet_Address"],Message["Payload"]["Sign_Message"])
            self._SI.Signed_Message(Message["Address"],signature)
        else:
            self._SI.Error(Message["Address"],"Sign_Message",error_info = "Address not in wallet. Cannot sign")
    #####################################################################
        
        
        



def Miner_Run():
    miner = Mining_System.Miner(None,Block_System.coinbase_tx(0),2)
    m = Main_Handler(Miner = miner)
    m.Main_Loop()




        
