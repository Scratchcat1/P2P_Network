import ecdsa,hashlib,codecs,base64_System
class Stack:
    def __init__(self,max_size = 100):
        self._contents = []
        self._max_size = max_size

    def pop(self):
        if len(self._contents) == 0:
            raise Exception("Stack Underflow")
        return self._contents.pop(len(self._contents)-1)

    def peek(self):
        if len(self._contents) == 0:
            raise Exception("Stack Underflow")
        return self._contents[len(self._contents)-1]

    def push(self,item):
        self._contents.append(item)

    def get_size(self):
        return len(self._contents)

    def flush(self):
        self._contents = []

    
class Script_Processor:
    def __init__(self):
        self.create_commands()

    def process(self,Script):
        try:
            self._Script_List = Script.split("  ")
            self._stack = Stack()
            while len(self._Script_List) > 0:
                item = self._Script_List.pop(0)
                if item in self._Commands:
                    self._Commands[item]()
                else:
                    self._stack.push(item)
                print(self._stack._contents)
                
        except Exception as e:
            print("Script failed:",e)
            self._stack.flush()
            self._stack.push("False")

        return self.Validate_Stack()
            
        
    def create_commands(self):
        self._Commands = {
            "OP_DUP":self.OP_Dup,
            "OP_HASH":self.OP_Hash,
            "OP_VERIFY":self.OP_Verify,
            "OP_EQUAL":self.OP_Equal,
            "OP_DROP":self.OP_Drop,
            "IF":self.If}

    def OP_Dup(self):
        self._stack.push(self._stack.peek())

    def OP_Hash(self):
        hash_item = self._stack.pop()
        self._stack.push(hashlib.sha256(str(hash_item).encode()).hexdigest())

    def OP_Verify(self):  # Signature public_key data
        data = hashlib.sha256(str(self._stack.pop()).encode()).digest()
        public_key = self._stack.pop()
        sig = codecs.decode(self._stack.pop().encode(),"base64")
        PuKO = ecdsa.VerifyingKey.from_string(base64_System.b64_to_bstr(public_key))
        try:
            self._stack.push(PuKO.verify(sig,data))
        except Exception as e:
            print(e)
            self._stack.push("False")
        

    def OP_Equal(self):
        A,B = self._stack.pop(),self._stack.pop()
        if not A == B:
            self._stack.push("False")

    def OP_Drop(self):  #Drop the top stack item
        self._stack.pop()

    def If(self):
        code_sections = [[]]
        item = "IF"#self._Script_List.pop(0)
        count = 0
        while True:
            item = self._Script_List.pop(0)
##            print(self._Script_:

            if item not in ["ELIF","ELSE","ENDIF"] or count > 0:
                code_sections[-1].append(item)
            elif item in ["ELIF","ELSE"]:
                code_sections.append([])
            else:
                break

            if item == "IF":
                count +=1
            elif item == "ENDIF":
                count -=1
##        while item != "ENDIF":
##            count = 0
##            code_sections.append([])
##            while item not in ["ELIF","ELSE","ENDIF"] or count > 0:
##                item = self._Script_List.pop(0)
##                code_sections[-1].append(item)
##                print(item)
##                if item == "IF":
##                    count +=1
##                elif item == "ENDIF":
##                    count -=1
##                print(item,count)
##                
##            if item != "ENDIF":  # If not last item
##                item = self._Script_List.pop(0)
            print(code_sections)


    def Validate_Stack(self):
        """ In order to be valid the script stack must finish with either empty or only 1/True strings left over. """
        x = []
        while self._stack.get_size() > 0:
            if self._stack.pop() not in ["1","True"]:  # This is to prevent the system seeing arbitary items as True values
                return False
        return True  # If the stack is empty or everything is True
##        return (all(x) or len(x) == 0)
        
        

    
def if_test():
    s = Script_Processor()
    s.process("IF  IF  IF  1  ELSE  2  ENDIF  1  2  ELSE  3  ENDIF  ELIF  2  3  4  ELSE  a  a  a  ENDIF")
