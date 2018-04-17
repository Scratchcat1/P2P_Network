import Networking_System, Database_System, Alert_System, Chain_System, Block_System, Transaction_System, Mempool_System, Mining_System, base64_System, Wallet_System
import random,time,numpy,os,hashlib, autorepr

class Time_Keeper(autorepr.Base):
    def __init__(self):
        self.logger_setup(__name__)
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

class Request_Queue(Ticker):  #Ticker with storage
    def __init__(self,Time_Period = 60,max_size = 10000): 
        self._request_queue = []
        self._max_size = max_size
        super().__init__(Time_Period)#Broadcast inventory every timer_length seconds

    def add_block_hash(self, block_hash, address = None):
        self._request_queue.append({"Type":"Block","Payload":block_hash,"Address":address})

    def add_tx_hash(self, tx_hash, address = None):
        self._request_queue.append({"Type":"Transaction","Payload":tx_hash,"Address":address})

    def get_queue(self,reset = True):
        return_value = self._request_queue
        if reset:
            self.reset_queue()
        return return_value

    def reset_queue(self):
        self._request_queue = []

    def get_size(self):
        return len(self._request_queue)

    def resize(self):   #If too large then purge older items
        if len(self._request_queue) > self._max_size:
            self._request_queue = self._request_queue[-self._maxsize:]
        
        
    
        

def Val_Limit(Value,Max,Min):   #https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range-python
    return max(min(Value,Max),Min)

    
class Main_Handler(autorepr.Base):
    def __init__(self,Node_Info = Networking_System.Network_Node(("127.0.0.1",8000)),Max_Connections = 15,Max_SC_Messages = 100, miner = None,wallet = Wallet_System.Wallet()):
        self.logger_setup(__name__)
        self._logger.info("Starting Main_Handler...")
        self._db_con = Database_System.DBConnection()
        self._Node_Info = Node_Info
        self._Max_SC_Messages = Max_SC_Messages
        self._Max_Connections = Max_Connections
        self._miner = miner
        self._wallet = wallet
##        self._UMC_SI = Networking_System.Socket_Interface(TPort = 9000)
        self._SI = Networking_System.Socket_Interface(Max_Connections,TPort = self._Node_Info.Get_Address()[1])
        self._Network_Nodes = {}  #Address :Network_Node
        self._UMCs = {}  #UMC_Node lists list
        self._Time = Time_Keeper()
        

        self._Mempool = Mempool_System.Mempool()  #Stores unconfirmed transactions
        self._Chain = Chain_System.Chain(self._Mempool)
        if self._miner:
            self._miner.set_mempool(self._Mempool)
            self.restart_miner()

        self._Network_Nodes_Check_Timer = Ticker(300)    #Every 300 seconds check nodes
        self._Block_Sync_Timer = Ticker(300)
        self._rebroadcaster = Request_Queue()
        self._requester = Request_Queue()



        self._Node_Commands = {
            "Peer_Connected":self.on_peer_connected,
            "Peer_Disconnected":self.on_peer_disconnected,
            "Ping":self.on_ping,
            "Ping_Response":self.on_ping_response,
            "Get_Node_Info":self.on_get_node_info,
            "Node_Info":self.on_node_info,
            "Time_Sync":self.on_time_sync,
            "Time_Sync_Response":self.on_time_sync_response,
            "Alert":self.on_alert,
            "Exit":self.on_exit,
            "Exit_Response":self.on_exit_response,
            "Get_Peers":self.on_get_peers,
            "Get_Peers_Response":self.on_get_peers_response,
            "Get_Address":self.on_get_address,
            "Get_Address_Response":self.on_get_address_response,

            
            "Inv":self.on_inv,
            "Get_Blocks":self.on_get_blocks,
            "Get_Blocks_Full":self.on_get_blocks_full,
            "Blocks":self.on_blocks,
            "Transactions":self.on_transactions,
                }
        self._UMC_Commands = {
            "Shutdown":self.on_UMC_shutdown,
            "Connect":self.on_UMC_connect,
            "Disconnect":self.on_UMC_disconnect,
            "Get_Authentication":self.on_UMC_get_authentication,
            "Authentication":self.on_UMC_authentication,
            "Config":self.on_UMC_config,
            "Get_Connected_Addresses":self.on_UMC_get_connected_addresses,
            "Get_UTXOs":self.on_UMC_get_UTXOs,
            "Sign_Alert":self.on_UMC_sign_alert,
            "Get_Wallet_Addresses":self.on_UMC_get_wallet_addresses,
            "New_Wallet_Address":self.on_UMC_new_wallet_address,
            "Sign_Message":self.on_UMC_sign_message,
                }
        self._logger.info("Main_Handler started.")

    def main_loop(self):
        self._Exit = False
        while not self._Exit:
            try:
                self.process_SC_messages()
                self.check_network_nodes()
                self.run_rebroadcast()
                self.run_requester()
                self.check_sync_blocks()
                self.check_miner()
            except Exception as e:
                self._logger.error("Error in main loop", exc_info = True)
            time.sleep(1/60)

        #Shutdown procedures
        if self._miner:
            self._miner.close()
            self._logger.debug("Miner has been shut down")
        self._SI.SC_Exit()
        self._logger.info("Node has shutdown! Goodbye")



    def process_SC_messages(self):
        Processed_Message_Number = 0
        while not self._SI.Output_Queue_Empty() and Processed_Message_Number < self._Max_SC_Messages:
            message = self._SI.Get_Item()
            self._logger.DEBUG("Process MESSAGE %s" % (message,))

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


    def on_peer_connected(self,Message):
        self._Network_Nodes[Message["Payload"]["Address"]] = Networking_System.Network_Node(Message["Payload"]["Address"])
        self._SI.Get_Node_Info(Message["Payload"]["Address"])
    def on_peer_disconnected(self,Message):
        self._Network_Nodes.pop(Message["Payload"]["Address"],None)
        self._UMCs.pop(Message["Payload"]["Address"],None)

    def on_ping(self,Message):
        self._SI.Ping_Response(Message["Address"],Message["Payload"]["Time_Sent"],self._Time.time())
    def on_ping_response(self,Message):
        ping_time = Message["Payload"]["Remote_Time_Sent"]-Message["Payload"]["Time_Sent"]
        self._Network_Nodes[Message["Address"]].Set_Last_Ping(ping_time)

    def on_get_node_info(self,Message):
        self._SI.Node_Info(Message["Address"],self._Node_Info.Get_Version(),self._Node_Info.Get_Type(),self._Node_Info.Get_Flags())
    def on_node_info(self,Message):
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
            

    def on_time_sync(self,Message):
        self._SI.Time_Sync_Response(Message["Address"],self._Time.time())
    def on_time_sync_response(self,Message):
        Node = self._Network_Nodes[Message["Address"]]
        Node.Set_Remote_Time(Message["Payload"]["Time"])

    def on_alert(self,Message):
        if Alert_System.Alert_User_Verify(self._db_con,self._Time.time(),Message["Payload"]["Username"],Message["Payload"]["Message"],Message["Payload"]["TimeStamp"],Message["Payload"]["Signature"],Message["Payload"]["Level"]):
            for Address in self._Nodes:
                self._SI.Alert(Message["Payload"]["Username"],Message["Payload"]["Message"],Message["Payload"]["TimeStamp"],Message["Payload"]["Signature"],Message["Payload"]["Level"]-1)
        else:
            self._logger.debug("Invalid alert denied progress")

    def on_exit(self,Message):
        self._SI.Exit_Response(Message["Address"])
        self._SI.Kill_Connection(Message["Address"])
    def on_exit_response(self,Message):
        self._SI.Kill_Connection(Message["Address"])

    def on_get_peers(self,Message):
        Peers = []
        for Node in self._Network_Nodes:
            Peers.append(Node.Get_Address())
        self._SI.Get_Peers_Response(Message["Address"],Peers)
    def on_get_peers_response(self,Message):
        for peer in Message["Payload"]["Peers"]:
            self._db_con.Add_Peer(peer["IP"],peer["Port"],"",[],self._Time.time(),1,Update_If_Need = False)#Transfer peer without trust in type , flags etc
            

    def on_get_address(self,Message):
        self._SI.Get_Address_Response(Message["Address"])
    def on_get_address_response(self,Message):
        self._Node_Info.Set_Address(Message["Payload"]["Address"])

    
    #####################################################################


    ################################
    #                              #
    #    Below is blockchain etc   #
    #                              #
    ################################

    def on_inv(self,Message):
        for item in Message["Payload"]:
            if item["Type"] == "Block":
                if not self._Chain.has_block(item["Payload"]):  #If not yet has block
                    self._requester.add_block_hash(item["Payload"],Message["Address"])              #Add to request block queue
            elif item["Type"] == "Transaction":
                if not self._Mempool.has_tx(item["Payload"]):   #If does not currently have transaction
                    self._requester.add_tx_hash(item["Payload"],Message["Address"])                 #Request transaction

    def on_get_blocks(self,Message):  #On remote needs to update chain
        Found = False
        for block_hash in Message["Payload"]:                   # for each hash known to remote
            if self._db_con.Is_Best_Chain_Block(block_hash):
                inventory = [{"Type":"Block","Payload":payload} for payload in self._db_con.Find_Best_Chain_Section(block_hash)]    #Convert hashes into inventory messages
                self._SI.Inv(Message["Address"],inventory)  #Send next best hashes once found best chain connection
                Found = True
                break
            
        if not Found: # If remote blockchain is completely broken
            inventory = [{"Type":"Block","Payload":payload} for payload in self._db_con.Find_Best_Chain_Section(self._db_con.Get_Best_Chain_Block(0)[0][0])]    #Convert hashes into inventory messages
            self._SI.Inv(Message["Address"],inventory)      #If broken send next hashes from genesis.
                
    def on_get_blocks_full(self,Message):               #On remote node wants full blocks
        block_jsons = []
        for block_hash in Message["Payload"]:
            try:
                block_jsons.append(self._Chain.get_block_json(block_hash))
            except:
                print("Remote tried to request non existant block with block hash:",block_hash)
        self._SI.Blocks(Message["Address"],block_jsons)
            

    def on_blocks(self,Message):                        #When getting the full block data
        for block_json in Message["Payload"]:
            block = Block_System.Block()
            block.import_json(block_json)
            if not self._Chain.has_block(block.Get_Block_Hash()) and block.Verify(self._Time.time(),block.Get_Difficulty()):      ################################################# USING BLOCK DIFFICULTY AS CHAIN MAY NOT NOTICE DIFFICULTY CHANGE OvER TIME    ################
                self._Chain.add_block(block)            #Add block if it valid
                self._rebroadcaster.add_block_hash(block.Get_Block_Hash())
##                print(self._Chain.get_highest_block_hash(),block.Get_Prev_Block_Hash(),block.Get_Block_Number(),block.Get_Difficulty())
                if self._Chain.get_highest_block_hash() == block.Get_Block_Hash():   #If this is the highest block
                    self.restart_miner()                #Restart the miner if need be.
                self.UMC_block_send(block)
                

    def on_transactions(self,Message):
        for tx_json in Message["Payload"]:
            tx = Transaction_System.Transaction()
            tx.json_import(tx_json)
            if not self._Mempool.has_tx(tx.get_transaction_hash()) and tx.verify():
                self._Mempool.add_transation_json(tx.get_transaction_hash(),tx_json,tx.get_fee())
                self._rebroadcaster.add_tx_hash(tx.get_transaction_hash())
                
            
                                    


    



    #####################################################################
    #
    #       General maintainance
    #
    #
    #
    #####################################################################
             
                
            

    def check_network_nodes(self):
        if self._Network_Nodes_Check_Timer.is_go():
            self._logger.info("Checking state of connected nodes")
            self._Network_Nodes_Check_Timer.reset()
            if len(self._Network_Nodes) < 15:
                difference = 15-len(self._Network_Nodes)
                peers = self._db_con.Get_Peers(Limit = difference)
                for peer in peers:
                    if (peer[0],peer[1]) not in self._Network_Nodes:    #If not already connected to node
                        self._SI.Create_Connection((peer[0],peer[1]))   #Create connection to node
                
            for Node in self._Network_Nodes.values():
                if Node.Get_Last_Contact() < time.time() - 20*60:
                    self._SI.Ping(Node.Get_Address(),self._Time.time())  #Ping to keep connection alive
                if Node.Get_Last_Contact() < time.time() - 90*60:
                    self._SI.Kill_Connection(Node.Get_Address())


    def run_rebroadcast(self):
        if self._rebroadcaster.is_go():
            self._logger.debug("Rebroadcasting data to a random set of nodes. Size of rebroadcast queue is %s" % (self._rebroadcaster.get_size(),))
            self._rebroadcaster.reset()
            for address in random.sample(list(self._Network_Nodes),min(8,len(self._Network_Nodes))):
                self._SI.Inv(address,self._rebroadcaster.get_queue(reset = False))
            self._rebroadcaster.reset_queue()

    def run_requester(self):
        if self._requester.is_go():
            self._logger.debug("Requesting data from remote nodes. Size of request queue is %s" % (self._requester.get_size(),))
            self._requester.reset()
            packets = {}
            for item in self._requester.get_queue():
                packets.setdefault((item["Type"],item["Address"]),[]).append(item["Payload"])
            for key,values in packets.items():
                target_type,address = key
                if target_type == "Block":
                    self._SI.Get_Blocks_Full(address,values)
                elif target_type == "Transaction":
                    self._SI.Get_Transactions(address,values)       #ASDFHEFHWUEHFWUEFHWHEF
                #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    #ASDFHEFHWUEHFWUEFHWHEF#ASDFHEFHWUEHFWUEFHWHEF
                    

    

    def check_sync_blocks(self):
        if self._Block_Sync_Timer.is_go():
            self._Block_Sync_Timer.reset()
            if self._db_con.Get_Highest_Work_Block()[0][5] < self._Time.time() - 24*3600:
                self._logger.info("Highest block to old, searching for new blocks")
                for address in random.sample(list(self._Network_Nodes),min(1,len(self._Network_Nodes))):    #Single node only, randomly selected, none if no connections 
                    known_hashes = self._db_con.Find_Best_Known_Pattern(self._Chain.get_highest_block_hash())
                    self._SI.Get_Blocks(address,known_hashes)

    def check_miner(self):
        if self._miner:
            if self._miner.has_found_block():
                block = self._miner.get_block()
##                print(block.export_json())
                internal_block_message = {"Command":"Blocks",
                                          "Address":self._Node_Info.Get_Address(),
                                          "Payload":[block.export_json()]}  #Includes generic address for localhost in case one wants to check if one created the block
                self.on_blocks(internal_block_message)           #Add block to chain normally. This also restarts the miner

                    
    def restart_miner(self):
        if self._miner:
            block_info = self._db_con.Get_Highest_Work_Block()
            self._miner.restart_mine(self._Time.time(),self._Chain.get_difficulty(),block_info[0][1]+1,block_info[0][0])  #Start mining on the highest block.
        
        
    #######################################################################

    #################################
    #                               #
    #  UserMainConnection commands  #
    #                               #
    #################################

    def UMC_block_send(self,block):
        for UMC_Address,UMC in self._UMCs.items():
            if UMC.Get_Enable_Block_Send():
                self._SI.Blocks(UMC_Address,[block.export_json()])



    def on_UMC_connect(self,message):
        self._SI.Create_Connection(message["Payload"]["Address"])
    def on_UMC_disconnect(self,message):
        #Potentially exit this in a more graceful manner
        self._SI.Kill_Connection(message["Payload"]["Address"])

    def on_UMC_shutdown(self,message):
        self._Exit = True
        self._logger.info("MAIN HANDLER IS SHUTTING DOWN")

    def on_UMC_get_authentication(self,message):
        salt = base64_System.str_to_b64(os.urandom(64))
        SECRET_KEY = 'lolcat'
        key = hashlib.sha256((salt+SECRET_KEY).encode()).hexdigest()
        self._UMCs[message["Address"]].Set_Authentication(key)
        self._SI.Authentication_Challenge(message["Address"],salt)

    def on_UMC_authentication(self,message):
        if message["Payload"]["Hash"] == self._UMCs[message["Address"]].Get_Authentication():
            self._UMCs[message["Address"]].Set_Authentication(True)
            self._SI.Authentication_Outcome(message["Address"],True)
        else:
            self._SI.Authentication_Outcome(message["Address"],False)

        

    def on_UMC_config(self,Message):
        self._UMCs[Message["Address"]].config(Message["Payload"])

    def on_UMC_get_connected_addresses(self,Message):
        self._SI.Connected_Addresses(Message["Address"],list(self._Network_Nodes))

    def on_UMC_get_UTXOs(self,Message):
        UTXOs = self._DB.Find_Address_UTXOs(Message["Payload"])
        self._SI.UTXOs(Message["Address"],UTXOs)


##############

    def on_UMC_sign_alert(self,Message):
        alert_details = Message["Payload"]
        success,signature = Alert_System.Sign_Alert(self._db_con, alert_details["Username"], alert_details["Message"], alert_details["TimeStamp"], alert_details["Level"])
        if success:
            self._SI.Signed_Alert(Message["Address"],signature)
        else:
            #Sig contains error message if failed
            self._SI.Error(Message["Address"],"Sign_Alert",error_info = signature)

    def on_UMC_get_wallet_addresses(self,Message):
        self._SI.Wallet_Addresses(Message["Address"],self._wallet.Get_Addresses())

    def on_UMC_new_wallet_address(self,Message):
        #Generate new address and save wallet
        self._SI.Wallet_Addresses(Message["Address"],[self._wallet.Generate_New_Address()])
        self._wallet.Save_Wallet()
        
    def on_UMC_sign_message(self,Message):
        if self._Wallet.has_address(Message["Payload"]["Wallet_Address"]):
            signature = self._Wallet.sign(Message["Payload"]["Wallet_Address"],Message["Payload"]["Sign_Message"])
            self._SI.Signed_Message(Message["Address"],signature)
        else:
            self._SI.Error(Message["Address"],"Sign_Message",error_info = "Address not in wallet. Cannot sign")
    #####################################################################
        
        
        



def miner_run():
    miner = Mining_System.Miner(None,Block_System.coinbase_tx(0),1)
    m = Main_Handler(miner = miner)
    m.main_loop()




        
