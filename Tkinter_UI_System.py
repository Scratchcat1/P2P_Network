import tkinter as tk
import Auto_UI,Networking_System
import time, hashlib, autorepr
class UI_Window(autorepr.Base):
    def __init__(self,root):
        #########################################################################
        #   ROOT is the tk window
        #   Every item is placed within GLOBAL FRAME
        #   All changable UI is placed within MAIN FRAME (e.g. not menu bar)
        #
        #
        ##########################################################################
        self.logger_setup(__name__)
        self._root = root
        self._root.title("Very Window. Wow Display!")
        self._root.geometry("500x300+100+100")
        self._global_frame = tk.Frame(root)
        self._main_frame = tk.Frame(self._global_frame)
        self._ticker_frame = tk.Frame(self._global_frame)
        self._global_frame.grid(row = 0,column = 0)
        self._main_frame.grid(row = 1,column = 1)
        self._ticker_frame.grid(row = 2,column = 1)

        self._TARGET_ADDRESS = ("127.0.0.1",8000)
        self._message_queue = Message_Queue()
        self._node_info = Networking_System.Network_Node("127.0.0.1",Type = "UMC")
        self._UMC = Networking_System.Socket_Interface(TPort = 9000)
##        for i in range(100):
##            self._message_queue.put({"Command":i,"Address":i^2,"Payload":[i**2,i**3,i**4]})


        self.create_menubar()
        self.reset_global_frame()
        self.home_dialog()
        self.run_ticker()
        self._root.mainloop()

    def reset_global_frame(self):
        self._global_frame.destroy()
        self._global_frame = tk.Frame(root)
        self._global_frame.grid(row = 0,column = 0)

        abort_button = tk.Button(self._global_frame,text = "ABORT",command = lambda : self.home_dialog())
        abort_button.grid(row = 0,column = 0)


    def reset_main_frame(self):
        self._main_frame.destroy()
        self._main_frame = tk.Frame(self._global_frame,borderwidth = 2)
        self._main_frame.grid(row = 1,column = 1)
        self.set_banner(" ")

    def reset_ticker_frame(self):
        self._ticker_frame.destroy()
        self._ticker_frame = tk.Frame(self._global_frame,borderwidth = 2)
        self._ticker_frame.grid(row = 2,column = 1)
##        tk.Grid.columnconfigure(self._ticker_frame,0,weight = 1)

    def set_banner(self,value):
        if hasattr(self,"_banner_label"):
            self._banner_label.destroy()
        self._banner_label = tk.Label(self._global_frame,text = value)
        self._banner_label.grid(row = 0,column = 1)

        
    def create_menubar(self):
        menubar = tk.Menu(self._root)
        menubar.add_command(label = "Test print",command = lambda :print("HI THIS IS TEST BUTTON MENU BAR"))

        gen_menubar = tk.Menu(menubar, tearoff = 0)
        gen_menubar.add_command(label = "Connect_Dialog",command = lambda :self.connect_dialog())
        gen_menubar.add_command(label = "Disconnect_Dialog",command = lambda :self.disconnect_dialog())
        gen_menubar.add_command(label = "Shutdown_Dialog",command = lambda :self.shutdown_dialog())
        gen_menubar.add_command(label = "Get_Connected_Addresses_Dialog",command = lambda :self.get_connected_addresses_dialog())
        gen_menubar.add_command(label = "Get_Peers_Dialog",command = lambda :self.get_peers_dialog())
        gen_menubar.add_command(label = "Get_UTXOs_Dialog",command = lambda :self.get_utxos_dialog())
        gen_menubar.add_command(label = "Send_Alert_Dialog",command = lambda :self.send_alert_dialog())
        menubar.add_cascade(label = "Generic",menu = gen_menubar)

        wallet_menubar = tk.Menu(menubar, tearoff = 0)
        wallet_menubar.add_command(label = "Get_Wallet_Addresses_Dialog",command = lambda :self.get_wallet_addresses_dialog())
        wallet_menubar.add_command(label = "New_Wallet_Address_Dialog",command = lambda :self.new_wallet_address_dialog())
        wallet_menubar.add_command(label = "Sign_Message_Dialog",command = lambda :self.sign_message_dialog())
        wallet_menubar.add_command(label = "Get_Wallet_Keys_Dialog",command = lambda :self.get_wallet_keys_dialog())
        wallet_menubar.add_command(label = "Dump_Wallet_Dialog",command = lambda :self.dump_wallet_dialog())
        menubar.add_cascade(label = "Wallet",menu = wallet_menubar)
        
        UMC_menubar = tk.Menu(menubar, tearoff = 0)
        UMC_menubar.add_command(label = "UMC_Connect_Dialog",command = lambda :self.UMC_connect_dialog())
        UMC_menubar.add_command(label = "UMC_Disconnect_Dialog",command = lambda :self.UMC_disconnect_dialog())
        menubar.add_cascade(label = "UMC",menu = UMC_menubar)
        
        self._root.config(menu = menubar)

    def wait_for_message(self,filter_func,wait_time = 2):
        start_time = time.time()
        with self._UMC.get_lock_object():        #Obtains the lock object and acquires the lock
            while start_time+wait_time > time.time():
                Processed_Message_Number = 0
                while not self._UMC.Output_Queue_Empty() and Processed_Message_Number < 100:    #Repeatedly attempts to process messages from the SI output queue
                    message = self._UMC.Get_Item()
    ##                print(message)
                    if filter_func(message):    #Determins if the message is the one desired.
                        print("Filtered wait for message %s" %(message,))
                        return message
                    else:
                        self._message_queue.put(message)
                        Processed_Message_Number +=1
                self._root.update_idletasks()
            return {"Command":"Error",
                    "Address":("N/A",-1),
                    "Payload":{"Command":str(filter_func),
                              "Error_Code":2,
                              "Error_Info":"Message was not recieved in the allotted time"}}
            

    def home_dialog(self):
        self.reset_main_frame()
        info_text = "HOME OF THE CATOTAC"
        info_text_widget = tk.Text(self._main_frame)
        info_text_widget.insert(tk.END,info_text)
        info_text_widget.configure(background = "LIGHTGRAY",state = tk.DISABLED)
        info_text_widget.grid(row = 0,column = 0)
        
    ###########################################################

    def connect_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.connect_dialog(Go = self.on_connect_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

        
    def on_connect_go(self,IP,Port):
        self.set_banner("Connection message sent for: "+IP+":"+str(Port))
        self._UMC.Connect(self._TARGET_ADDRESS,(IP,Port))

        ###########

    def disconnect_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.disconnect_dialog(Go = self.on_disconnect_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_disconnect_go(self,IP,Port):
        self.set_banner("Disconnection message sent for "+IP+":"+str(Port))
        self._UMC.Disconnect(self._TARGET_ADDRESS,(IP,Port))

        #########

    def shutdown_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.shutdown_dialog(Go = self.on_shutdown_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_shutdown_go(self):
        self.set_banner("Shutting down...")
        self._UMC.Shutdown(self._TARGET_ADDRESS)

        ########


    def UMC_connect_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.UMC_connect_dialog(Go = self.on_UMC_connect_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_UMC_connect_go(self,IP,Port,Password):
        self._UMC.Create_Connection((IP,Port))
        time.sleep(0.5) #Wait for connection to form
        self._UMC.Node_Info((IP,Port),self._node_info.Get_Version(),self._node_info.Get_Type(),self._node_info.Get_Flags())
        time.sleep(0.1)
        self._UMC.Get_Authentication((IP,Port))
        auth_challenge = self.wait_for_message(lambda m:m["Address"] == (IP,Port) and m["Command"] == "Authentication_Challenge")
        self._UMC.Authentication((IP,Port),hashlib.sha256((auth_challenge["Payload"]["Salt"]+Password).encode()).hexdigest())
        auth_outcome = self.wait_for_message(lambda m:m["Address"] == (IP,Port) and m["Command"] == "Authentication_Outcome")
        self.set_banner("Authentication Sucess:"+str(auth_outcome["Payload"]["Outcome"]))
        if auth_outcome["Payload"]["Outcome"]:
            self._TARGET_ADDRESS = (IP,Port)
            self._logger.info("%s:%s is now the target node" % (IP,Port))
        #########

    def UMC_disconnect_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.UMC_disconnect_dialog(Go = self.on_UMC_disconnect_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_UMC_disconnect_go(self,IP,Port):
        self._UMC.Exit((IP,Port))
        exit_response = self.wait_for_message(lambda m:m["Address"] == (IP,Port) and m["Command"] == "Exit_Response")
        self._UMC.Kill_Connection((IP,Port))
        if exit_response["Command"] == "Exit_Response":
            self.set_banner("Sucessfully disconnected from "+str(IP)+":"+str(Port))
        else:
            self.set_banner("Failure to disconnect. You may not be connected to this node")

        #########

    def get_connected_addresses_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.get_connected_addresses_dialog(Go = self.on_get_connected_addresses_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_get_connected_addresses_go(self):
        self.set_banner("Sent message for connected addresses")
        self._UMC.Get_Connected_Addresses(self._TARGET_ADDRESS)
        connected_addresses = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Connected_Addresses")
        self.display_message(connected_addresses)
        
        #########
        
    def get_peers_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.get_peers_dialog(Go = self.on_get_peers_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_get_peers_go(self):
        self.set_banner("Send message to get peers")
        self._UMC.Get_Peers(self._TARGET_ADDRESS)
        peers_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Get_Peers_Response")
        self.display_message(peers_message)

        ############
    def get_utxos_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.get_utxos_dialog(Go = self.on_get_utxos_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_get_utxos_go(self,wallet_addresses):
        self._UMC.Get_UTXOs(self._TARGET_ADDRESS, wallet_addresses)
        utxos_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "UTXOs")
        self.display_message(utxos_message)
        
        
        ############

    def send_alert_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.send_alert_dialog(Go = self.on_send_alert_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_send_alert_go(self, username, message, level):
        self.set_banner("Signing and sending alert")
        timestamp = time.time()
        self._UMC.Sign_Alert(self._TARGET_ADDRESS, username, message, timestamp, level)
        signature_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Signed_Alert")        
        self._UMC.Alert(self._TARGET_ADDRESS, username, message, timestamp, signature_message["Payload"]["Signature"], level)
        
        #############

    def get_wallet_addresses_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.get_wallet_addresses_dialog(Go = self.on_get_wallet_addresses_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_get_wallet_addresses_go(self):
        self._UMC.Get_Wallet_Addresses(self._TARGET_ADDRESS)
        wallet_addresses_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Addresses")
        self.display_message(wallet_addresses_message)

        ############

    def new_wallet_address_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.new_wallet_address_dialog(Go = self.on_new_wallet_address_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_new_wallet_address_go(self):
        self._UMC.New_Wallet_Address(self._TARGET_ADDRESS)
        wallet_address_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Addresses")
        self.display_message(wallet_address_message)

        ##########

    def sign_message_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.sign_message_dialog(Go = self.on_sign_message_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_sign_message_go(self,wallet_address,message):
        self._UMC.Sign_Message(self._TARGET_ADDRESS,wallet_address,message)
        signature_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Signed_Message")
        self.display_message(signature_message)

##        #########
##
##    def get_wallet_address_public_key_dialog(self):
##        self.reset_main_frame()
##        form = Auto_UI.get_wallet_address_public_key_dialog(Go = self.on_get_wallet_address_public_key_go())
##        Auto_UI.Tk_Form_Display().run(self._main_frame,form)
##
##    def on_get_wallet_address_public_key_go(self,wallet_address):
##        self._UMC.Get_Wallet_Address_Public_Key(self._TARGET_ADDRESS,wallet_address)
##        public_key_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Address_Public_Key")
##        self.display_message(public_key_message)
##
##        ###########
##
##    def get_wallet_address_private_key_dialog(self):
##        self.reset_main_frame()
##        form = Auto_UI.get_wallet_address_private_key_dialog(Go = self.on_get_wallet_address_private_key_go())
##        Auto_UI.Tk_Form_Display().run(self._main_frame,form)
##
##    def on_get_wallet_address_private_key_go(self,wallet_address):
##        self._UMC.Get_Wallet_Address_Private_Key(self._TARGET_ADDRESS,wallet_address)
##        private_key_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Address_Private_Key")
##        self.display_message(private_key_message)
##
        #########

    def get_wallet_keys_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.get_wallet_keys_dialog(Go = self.on_get_wallet_keys_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_get_wallet_keys_go(self,addresses_list, public_keys, private_keys):
        self.set_banner("Requested wallet keys from %s" %(self._TARGET_ADDRESS,))
        wallet_addresses = {}
        for address in addresses_list:
            wallet_addresses[address] = {"Public":False,"Private":False}
            if public_keys:
                wallet_addresses[address]["Public"] = True
            if private_keys:
                wallet_addresses[address]["Private"] = True
        self._UMC.Get_Wallet_Keys(self._TARGET_ADDRESS,wallet_addresses)
        keys_message = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Keys")
        self.display_message(keys_message)

        #########

    def dump_wallet_dialog(self):
        self.reset_main_frame()
        form = Auto_UI.dump_wallet_dialog(Go = self.on_dump_wallet_go)
        Auto_UI.Tk_Form_Display().run(self._main_frame,form)

    def on_dump_wallet_go(self):
        self.set_banner("Requested wallet dump")
        self._UMC.Dump_Wallet(self._TARGET_ADDRESS)
        wallet_dump = self.wait_for_message(lambda m:m["Address"] == self._TARGET_ADDRESS and m["Command"] == "Wallet_Dump_Data")
        self.display_message(wallet_dump)

        #########
        #wallet utxos
        #wallet transactions
        #########












        
    

    ##############################################################################

    def run_ticker(self):
        self.reset_ticker_frame()
        for i in range(100):    #process at maximum 100 messages before rendering.
            locked = self._UMC.acquire_lock(blocking = False)    #Attempt to get a lock
            if locked:
                if not self._UMC.Output_Queue_Empty():
                    message = self._UMC.Get_Item()  #obtains a single item
                    self._message_queue.put(message)
                    self._UMC.release_lock()
                else:
                    self._UMC.release_lock()
                    break       #Break if no more messages are available
                
        for i,message in enumerate(self._message_queue.peek()):
            text = str((message["Address"],message["Command"]))
            message_button = tk.Button(self._ticker_frame,text = text+" "*(206-len(text)),command = lambda message = message: self.display_message(message))
            message_button.grid(row = i,column = 0)
            
        self._logger.debug("Ticker queue length: %s" %(len(self._message_queue),))
        self._message_queue.remove()                #Remove old messages. After loop as these messages will have been displayed.
        self._root.after(10*1000,self.run_ticker)   #Schedule ticker to run again in 10 seconds.

    def display_message(self,message):
        self.reset_main_frame()
        command_label = tk.Label(self._main_frame,text = "Command:")
        command_value_label = tk.Label(self._main_frame,text = message["Command"])
        address_label = tk.Label(self._main_frame,text = "Address:")
        address_value_label = tk.Label(self._main_frame,text = message["Address"])
        command_label.grid(row = 1,column = 0,sticky = tk.W),command_value_label.grid(row = 1,column = 1,sticky = tk.W),address_label.grid(row = 2,column = 0,sticky = tk.W),address_value_label.grid(row = 2,column = 1,sticky = tk.W)
            
        if message["Command"] not in ["Transaction","Block"] and len(message["Payload"]) > 0:
            payload_label = tk.Label(self._main_frame,text = "Payload:")
            payload_label.grid(row = 3,column = 0,sticky = tk.W)

            for i,item in enumerate(list(message["Payload"])):
                payload_value_label = tk.Label(self._main_frame,text = item)
                payload_value_label.grid(row = 3+i,column = 1,sticky = tk.W)
        

##if message["Command"] in ["Transaction","Block"]:
##            payload = []
##            for item in message["Payload"]:
##                payload.append(json.loads(item))
##        else:
##            payload = message["Payload"]
##
##
##
##    def display_message_group_component(self,grouped_items, offset_row, recursion_level, offset_column=1):
##        MAX_GROUP_COMPONENT_DISPLAY_RECURSION_LEVEL = 3
##        for i,item in enumerate(grouped_item):
##            if type(item) in [list,dict] and recursion_level <= MAX_GROUP_COMPONENT_DISPLAY_RECURSION_LEVEL:
##                offset_row += self.display_message_group_component(item, offset_row, recursion_level + 1,offset_column + 1)
        


    
            
        

##def Entry_Label(frame,label_text,entry_default="",row = 1, column = 0):
##    label = tk.Label(frame,text = label_text)
##    entry = tk.Entry(frame)
##    entry.insert(0,entry_default)
##
##    label.grid(row = row,column = column)
##    entry.grid(row = row,column = column+1)
##    return label,entry
    
    

        
        
class Message_Queue:
    def __init__(self,max_size = 100):
        """Stores messages. max_size = 0 for any size"""
        self._queue = []
        self._max_size = max_size

    def put(self,message):
        while len(self._queue) >= self._max_size and self._max_size > 0:
            self._queue.pop(0)
        self._queue.append(message)

    def get(self,position = 0):
        return self._queue[position]

    def peek(self,number = 10):
        items = [self._queue[x] for x in range(min(number,len(self._queue)))]
        return items

    def remove(self,number = 3):
        items = [self._queue.pop(0) for x in range(min(number,len(self._queue)))]
        return items

    def __len__(self):
        return len(self._queue)
    
        
def Weight(frame):
    for x in range(60):
        tk.Grid.columnconfigure(frame, x, weight=1)

    for y in range(30):
        tk.Grid.rowconfigure(frame, y, weight=1)
            












    



if __name__ == "__main__":
    root = tk.Tk()
    window = UI_Window(root)
##    root.quit()
##    root.mainloop()
