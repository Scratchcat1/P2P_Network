import ecdsa,hashlib,codecs
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
            Script_List = Script.split("  ")
            self._stack = Stack()
            while len(Script_List) > 0:
                item = Script_List.pop(0)
                if item in self._Commands:
                    self._Commands[item]()
                else:
                    self._stack.push(item)
                print(self._stack._contents)
                
        except Exception as e:
            print("Script failed:",e)
            self._stack.flush()
            self._stack.push(False)

        return self.Validate_Stack()
            
        
    def create_commands(self):
        self._Commands = {
            "OP_DUP":self.OP_Dup,
            "OP_HASH":self.OP_Hash,
            "OP_VERIFY":self.OP_Verify,
            "OP_EQUAL":self.OP_Equal}

    def OP_Dup(self):
        self._stack.push(self._stack.peek())

    def OP_Hash(self):
        hash_item = self._stack.pop()
        self._stack.push(hashlib.sha256(str(hash_item).encode()).hexdigest())

    def OP_Verify(self):  # Signature public_key data
        data = hashlib.sha256(str(self._stack.pop()).encode()).digest()
        public_key = self._stack.pop()
        sig = codecs.decode(self._stack.pop().encode(),"base64")
        PuKO = ecdsa.VerifyingKey.from_pem(public_key)
##        try:
        self._stack.push(PuKO.verify(sig,data))
##        except Exception as e:
##            print(e)
##            self._stack.push(False)
        

    def OP_Equal(self):
        A,B = self._stack.pop(),self._stack.pop()
        if not A == B:
            self._stack.push(False)


    def Validate_Stack(self):
        x = []
        while self._stack.get_size() > 0:
            x.append(self._stack.pop())
        return (all(x) or len(x) == 0)
        
        

    
    
