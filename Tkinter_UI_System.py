import tkinter


class UI_Window:
    def __init__(self,root):
        #########################################################################
        #   ROOT is the tkinter window
        #   Every item is placed within GLOBAL FRAME
        #   All changable UI is placed within MAIN FRAME (e.g. not menu bar)
        #
        #
        ##########################################################################
        self._root = root
        self._root.title("HI")
        self._root.geometry("500x300+100+100")
        self._global_frame = tkinter.Frame(root)
        self._main_frame = tkinter.Frame(self._global_frame)
        self._global_frame.grid(row = 0,column = 0)
        self._main_frame.grid(row = 1,column = 0)

        self._TARGET_ADDRESS = ("127.0.0.1",9000)

        self.create_menubar()
        self.reset_global_frame()
        self.Home_Dialog()
        self._root.mainloop()

    def reset_global_frame(self):
        self._global_frame.destroy()
        self._global_frame = tkinter.Frame(root)
        self._global_frame.grid(row = 0,column = 0)

        abort_button = tkinter.Button(self._global_frame,text = "ABORT",command = lambda : self.Home_Dialog())
        abort_button.grid(row = 0,column = 0)


    def reset_main_frame(self):
        self._main_frame.destroy()
        self._main_frame = tkinter.Frame(self._global_frame)
        self._main_frame.grid(row = 1,column = 1)
        self.set_banner(" ")

    def set_banner(self,value):
        if hasattr(self,"_banner_label"):
            self._banner_label.destroy()
        self._banner_label = tkinter.Label(self._global_frame,text = value)
        self._banner_label.grid(row = 0,column = 1)

        
    def create_menubar(self):
        menubar = tkinter.Menu(self._root)
        menubar.add_command(label = "Test print",command = lambda :print("HI THIS IS TEST BUTTON MENU BAR"))

        gen_menubar = tkinter.Menu(menubar, tearoff = 1)
        gen_menubar.add_command(label = "Connect_Dialog",command = lambda :self.Connect_Dialog())
        gen_menubar.add_command(label = "Disconnect_Dialog",command = lambda :self.Disconnect_Dialog())
        gen_menubar.add_command(label = "Shutdown_Dialog",command = lambda :self.Shutdown_Dialog())
        menubar.add_cascade(label = "Generic",menu = gen_menubar)
        self._root.config(menu = menubar)


    def Home_Dialog(self):
        self.reset_main_frame()
        info_text = "HOME OF THE CATOTAC"
        info_text_widget = tkinter.Text(self._main_frame)
        info_text_widget.insert(tkinter.END,info_text)
        info_text_widget.configure(background = "LIGHTGRAY",state = tkinter.DISABLED)
        info_text_widget.grid(row = 0,column = 0)
        
    ###########################################################

    def Connect_Dialog(self):
        self.reset_main_frame()
        ip_label,ip_entry = Entry_Label(self._main_frame,"IP")
        port_label,port_entry = Entry_Label(self._main_frame,"Port","8000",row = 2)
        
        
        go_button = tkinter.Button(self._main_frame,text = "Go",command = lambda : self.On_Connect_Go(ip_entry.get(),int(port_entry.get())))
        go_button.grid(row = 3,column = 0)
        
    def On_Connect_Go(self,IP,Port):
        self.set_banner("Connection message sent for: "+IP+" "+str(Port))
        self._UMC.Connect(self._TARGET_ADDRESS,(IP,Port))



    def Disconnect_Dialog(self):
        self.reset_main_frame()
        ip_label,ip_entry = Entry_Label(self._main_frame,"IP")
        port_label,port_entry = Entry_Label(self._main_frame,"Port","8000",row = 2)

        go_button = tkinter.Button(self._main_frame,text = "Go",command = lambda : self.On_Disconnect_Go(ip_entry.get(),int(port_entry.get())))
        go_button.grid(row = 3,column = 0)

    def On_Disconnect_Go(self,IP,Port):
        self.set_banner("Disconnection message sent for "+IP+" "+str(Port))
        self._UMC.Disconnect(self._TARGET_ADDRESS,(IP,Port))


    def Shutdown_Dialog(self):
        self.reset_main_frame()
        label = tkinter.Label(self._main_frame,text = "Are you sure you want to shutdown?")
        label.grid(row = 1,column = 0)

        go_button = tkinter.Button(self._main_frame,text = "Go",command = lambda : self.On_Shutdown_Go())
        go_button.grid(row = 3,column = 0)

    def On_Shutdown_Go(self):
        self.set_banner("Shutting down...")
        self._UMC.Shutdown(self._TRAGET_ADDRESS)
        
        

        


    
            
        

def Entry_Label(frame,label_text,entry_default="",row = 1, column = 0):
    label = tkinter.Label(frame,text = label_text)
    entry = tkinter.Entry(frame)
    entry.insert(0,entry_default)

    label.grid(row = row,column = column)
    entry.grid(row = row,column = column+1)
    return label,entry
    

##def Dialog_Creator(frame,configuration):
    

        
        



















    



if __name__ == "__main__":
    root = tkinter.Tk()
    window = UI_Window(root)
##    root.mainloop()
