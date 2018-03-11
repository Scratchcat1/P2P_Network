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
            command_button = tk.Button(frame,text = command["Command_Label"],command = lambda : self.run_command(command["Function"],command["Arguments"]))
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
                
        

        

        

        
        
    
