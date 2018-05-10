import tkinter as tk
import re


TK_TYPES = {
    "Entry":tk.Entry,
    "Label":tk.Label,
    "Checkbutton":tk.Checkbutton}
TK_VARS = {
    str:tk.StringVar,
    int:tk.IntVar,
    float:tk.DoubleVar,
    bool:tk.BooleanVar}
class UI_Form:
    def __init__(self):
        self._title = ""
        self._queries = []
        self._commands = []

    def set_title(self,title):
        self._title = title

    def add_query(self,query_label,query_type = str,default_value = None,tk_type = "NA"):
        self._queries.append({"Query_Label":query_label,
                              "Query_Type":query_type,
                              "Default_Value":default_value,
                              "Tk_Type":tk_type})
    def add_command(self,command_label,function,arguments):
        self._commands.append({"Command_Label":command_label,
                               "Function":function,
                               "Arguments":arguments})

    def update_command(self,command_label,function,arguments= None):
        for command in self._commands:
            if command["Command_Label"] == command_label:
                command["Function"] = function
                if arguments:
                    command["Arguments"] = arguments
                break
            
    def dump(self):
        return {"Title":self._title,
                "Queries":self._queries,
                "Commands":self._commands}

    def load(self,dict_form):
        self._title = dict_form["Title"]
        self._queries = dict_form["Queries"]
        self._commands = dict_form["Commands"]



       
        

class Tk_Form_Display:
    """
    Tkinter auto UI form. Uses GRID!
    """
    def __init__(self,start_column = 1,start_row = 1):
        self._start_column = start_column
        self._start_row = start_row
        self._form_objects = {}
        self._commands = {}

    def run(self,frame,form):
        if type(form) == UI_Form:
            form = form.dump()

        row = self._start_row

        title_label = tk.Label(frame,text = form["Title"])
        title_label.grid(row = row, column = self._start_column)
        row+=1

        for query in form["Queries"]:
            query_label = tk.Label(frame,text = query["Query_Label"])
            
            tk_object = TK_TYPES.get(query.get("Tk_Type",None),tk.Entry)  #If has not Defined Tk_Type or unknown then use entry
            tk_item = tk_object(frame)
##            if query.get("Default_Value",None) != None:
##                tk_item.
            self._form_objects[query["Query_Label"]] = {"item":tk_item,"query":query}

            query_label.grid(row = row,column = self._start_column)
            tk_item.grid(row = row,column = self._start_column +1)
            row +=1


        column = self._start_column
        for command in form["Commands"]:
            command_button = tk.Button(frame,text = command["Command_Label"],command = lambda f= command["Function"],a=command["Arguments"]: self.run_command(f,a))
            command_button.grid(row = row, column = column)
            column +=1

    def run_command(self,function,arguments):
        new_args = []
        for arg in arguments:
            if type(arg) != str or not re.match("^%.+%$",arg):      #Command is not a variable
                new_args.append(arg)
            else:
                new_args.append(  self._form_objects[arg[1:-1]]["query"]["Query_Type"](  self._form_objects[arg[1:-1]]["item"].get()   ))

        function(*new_args)
                

class Text_Form_Display:
    """
    Text Auto_UI form
    """
    def __init__(self):
        pass

    def run(self,form):
        if type(form) == UI_Form:
            form = form.dump()
        self._results = {}
        print("TITLE: ",form["Title"])

        print("QUERIES:")
        print("Fill out these queries.")
        base_string = create_base_string(max([len(item["Query_Label"]) for item in form["Queries"]]))
        for query in form["Queries"]:
            self._results[query["Query_Label"]] = query["Query_Type"](input(base_string.format(query["Query_Label"],">>")))
        print(self._results)


        print("COMMANDS:")
        print("Choose a command.")
        base_string = create_base_string(len(str(len(form["Commands"]))))
        for i,command in enumerate(form["Commands"]):
            print(base_string.format(str(i+1),command["Command_Label"]))
        print("Enter -1 to cancel.")
        
        target_command = int(input("Command Number >>"))
        if target_command in range(1,len(form["Commands"])+1):
            self.run_command(form["Commands"][target_command-1]["Function"],form["Commands"][target_command-1]["Arguments"])

    def run_command(self,function,arguments):
        new_args = []
        for arg in arguments:
            if type(arg) != str or not re.match("^%.+%$",arg):      #Command is not a variable
                new_args.append(arg)
            else:
                new_args.append(self._results[arg[1:-1]])

        function(*new_args)
            


def create_base_string(size):
    return "{0:"+str(size)+"} : {1}"

        
#######################################################

#######################################################


#Connect the node to a server
def connect_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Connect to node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form

#Connect the node from a server
def disconnect_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Disconnect from node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form

#Shutdown the node
def shutdown_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Shutdown")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

#Connect the UMC to a node
def UMC_connect_dialog(**kwargs):
    form = UI_Form()
    form.set_title("UMC connect to a node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_query("Password",str)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%","%Password%"))
    return form

#Disconnect the UMC from a node
def UMC_disconnect_dialog(**kwargs):
    form = UI_Form()
    form.set_title("UMC disconnect to a node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form

#Get the nodes connected to the current node
def get_connected_addresses_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get connected node addresses")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

#Get the peers of the current node
def get_peers_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get node peers")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

#Get all the UTXOs
def get_utxos_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get the UTXOs from the node")
    form.add_query("Wallet addresses comma separated",lambda x:x.replace(" ","").split(","))
    form.add_command("Go",kwargs.get("Go",None),("%Wallet addresses comma separated%",))
    return form

#Send an alert using the credentials stored on the current node
def send_alert_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Send an alert")
    form.add_query("Username",str)
    form.add_query("Message",str)
    form.add_query("Level",int)
    form.add_command("Go",kwargs.get("Go",None),("%Username%","%Message%","%Level%"))
    return form

#Get the wallet addresses for the wallet attached to the node
def get_wallet_addresses_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get wallet addresses")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

#Create a new address in the wallet attached to the node
def new_wallet_address_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Create a new wallet address")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

#Sign the message supplied using the given address private key in the wallet
def sign_message_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Sign a message")
    form.add_query("Wallet Address",str)
    form.add_query("Message",str)
    form.add_command("Go",kwargs.get("Go",None),("%Wallet Address%","%Message%"))
    return form

###Get the public key of an address in the wallet
##def get_wallet_address_public_key_dialog(**kwargs):
##    form = UI_Form()
##    form.set_title("Get the public key of a wallet")
##    form.add_query("Address",str)
##    form.add_command("Go",kwargs.get("Go",None),("%Address",))
##    return form
##
###Get the private key of an address in the wallet
##def get_wallet_address_private_key_dialog(**kwargs):
##    form = UI_Form()
##    form.set_title("Get the private key of a wallet")
##    form.add_query("Address",str)
##    form.add_command("Go",kwargs.get("Go",None),("%Address"))
##    return form

#Get wallet keys
def get_wallet_keys_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get wallet keys")
    form.add_query("Wallet addresses comma separated",lambda x:x.replace(" ","").split(","))
    form.add_query("Get public keys Y/N",lambda x:x[0].upper() == "Y")
    form.add_query("Get private keys Y/N",lambda x:x[0].upper() == "Y")
    #List of addresses, public keys bool, private keys bool
    form.add_command("Go",kwargs.get("Go",None),("%Wallet addresses comma separated%","%Get public keys Y/N%","%Get private keys Y/N%"))
    return form

#Dump the wallet to json
def dump_wallet_dialog(**kwargs):
    form = UI_Form()
    form.set_title("Dump the wallet and return the information")
    form.add_command("Go",kwargs.get("Go",None),())
    return form
##
###Get the UTXOs in the wallet
##def get_wallet_UTXOs_dialog(**kwargs):
##    form = UI_Form()
##    form.set_title("Get the UTXOs in the wallet")
##    form.add_command("Go",kwargs.get("Go",None),())
##    return form
##
###Get all the transactions associated with this wallet.
##def get_wallet_transactions_dialog(**kwargs):
##    form = UI_Form()
##    form.set_title("Get the transactions in the wallet")
##    form.add_command("Go",kwargs.get("Go",None),())
##    return form

