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

        

def Connect_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("Connect to node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form

def Disconnect_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("Disconnect from node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form
        
def Shutdown_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("Shutdown")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

def UMC_Connect_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("UMC connect to a node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_query("Password",str)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%","%Password%"))
    return form
    
def UMC_Disconnect_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("UMC disconnect to a node")
    form.add_query("IP",str)
    form.add_query("Port",int)
    form.add_command("Go",kwargs.get("Go",None),("%IP%","%Port%"))
    return form

def Get_Connected_Addresses_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get connected node addresses")
    form.add_command("Go",kwargs.get("Go",None),())
    return form

def Get_Peers_Dialog(**kwargs):
    form = UI_Form()
    form.set_title("Get node peers")
    form.add_command("Go",kwargs.get("Go",None),())
    return form
    
