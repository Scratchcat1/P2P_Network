import tkinter as tk


class UI_Window:
    def __init__(self,root):
        #########################################################################
        #   ROOT is the tk window
        #   Every item is placed within GLOBAL FRAME
        #   All changable UI is placed within MAIN FRAME (e.g. not menu bar)
        #
        #
        ##########################################################################
        self._root = root
        self._root.title("HI")
        self._root.geometry("500x300+100+100")
        self._global_frame = tk.Frame(root)
        self._main_frame = tk.Frame(self._global_frame)
        self._ticker_frame = tk.Frame(self._global_frame)
        self._global_frame.grid(row = 0,column = 0)
        self._main_frame.grid(row = 1,column = 1)
        self._ticker_frame.grid(row = 2,column = 1)

        self._TARGET_ADDRESS = ("127.0.0.1",9000)
        self._message_queue = Message_Queue()
        for i in range(100):
            self._message_queue.put({"Command":i,"Address":i^2,"Payload":[i**2,i**3,i**4]})


        self.create_menubar()
        self.reset_global_frame()
        self.Home_Dialog()
        self.run_ticker()
        self._root.mainloop()

    def reset_global_frame(self):
        self._global_frame.destroy()
        self._global_frame = tk.Frame(root)
        self._global_frame.grid(row = 0,column = 0)

        abort_button = tk.Button(self._global_frame,text = "ABORT",command = lambda : self.Home_Dialog())
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

        gen_menubar = tk.Menu(menubar, tearoff = 1)
        gen_menubar.add_command(label = "Connect_Dialog",command = lambda :self.Connect_Dialog())
        gen_menubar.add_command(label = "Disconnect_Dialog",command = lambda :self.Disconnect_Dialog())
        gen_menubar.add_command(label = "Shutdown_Dialog",command = lambda :self.Shutdown_Dialog())
        menubar.add_cascade(label = "Generic",menu = gen_menubar)
        self._root.config(menu = menubar)


    def Home_Dialog(self):
        self.reset_main_frame()
        info_text = "HOME OF THE CATOTAC"
        info_text_widget = tk.Text(self._main_frame)
        info_text_widget.insert(tk.END,info_text)
        info_text_widget.configure(background = "LIGHTGRAY",state = tk.DISABLED)
        info_text_widget.grid(row = 0,column = 0)
        
    ###########################################################

    def Connect_Dialog(self):
        self.reset_main_frame()
        ip_label,ip_entry = Entry_Label(self._main_frame,"IP")
        port_label,port_entry = Entry_Label(self._main_frame,"Port","8000",row = 2)
        
        
        go_button = tk.Button(self._main_frame,text = "Go",command = lambda : self.On_Connect_Go(ip_entry.get(),int(port_entry.get())))
        go_button.grid(row = 3,column = 0)
        
    def On_Connect_Go(self,IP,Port):
        self.set_banner("Connection message sent for: "+IP+" "+str(Port))
        self._UMC.Connect(self._TARGET_ADDRESS,(IP,Port))



    def Disconnect_Dialog(self):
        self.reset_main_frame()
        ip_label,ip_entry = Entry_Label(self._main_frame,"IP")
        port_label,port_entry = Entry_Label(self._main_frame,"Port","8000",row = 2)

        go_button = tk.Button(self._main_frame,text = "Go",command = lambda : self.On_Disconnect_Go(ip_entry.get(),int(port_entry.get())))
        go_button.grid(row = 3,column = 0)

    def On_Disconnect_Go(self,IP,Port):
        self.set_banner("Disconnection message sent for "+IP+" "+str(Port))
        self._UMC.Disconnect(self._TARGET_ADDRESS,(IP,Port))


    def Shutdown_Dialog(self):
        self.reset_main_frame()
        label = tk.Label(self._main_frame,text = "Are you sure you want to shutdown?")
        label.grid(row = 1,column = 0)

        go_button = tk.Button(self._main_frame,text = "Go",command = lambda : self.On_Shutdown_Go())
        go_button.grid(row = 3,column = 0)

    def On_Shutdown_Go(self):
        self.set_banner("Shutting down...")
        self._UMC.Shutdown(self._TARGET_ADDRESS)


    





    ##############################################################################

    def run_ticker(self):
        self.reset_ticker_frame()
        self._message_queue.remove()
        for i,message in enumerate(self._message_queue.peek()):
            text = str((message["Address"],message["Command"]))
            message_button = tk.Button(self._ticker_frame,text = text+" "*(206-len(text)),command = lambda message = message: self.display_message(message))
            message_button.grid(row = i,column = 0)
        print("HI")

        self._root.after(10*1000,self.run_ticker)

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

            for i,item in enumerate(message["Payload"]):
                payload_value_label = tk.Label(self._main_frame,text = item)
                payload_value_label.grid(row = 3+i,column = 1,sticky = tk.W)
        

        


    
            
        

def Entry_Label(frame,label_text,entry_default="",row = 1, column = 0):
    label = tk.Label(frame,text = label_text)
    entry = tk.Entry(frame)
    entry.insert(0,entry_default)

    label.grid(row = row,column = column)
    entry.grid(row = row,column = column+1)
    return label,entry
    

##def Dialog_Creator(frame,configuration):
    

        
        
class Message_Queue:
    def __init__(self,max_size = 100):
        """Stores messages. max_size = 0 for any size"""
        self._queue = []
        self._max_size = max_size

    def put(self,message):
        while len(self._queue) >= self._max_size and max_size > 0:
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
