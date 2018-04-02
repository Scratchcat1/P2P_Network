import ecdsa,hashlib,codecs,base64_System,re,Wallet_System
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
        self._locking_script = ""
        self._unlocking_script = ""
        self._hash_data = ""
        self._address_re_pattern = "[a-f0-9]{64}"
        self._public_key_pattern = "[a-zA-Z0-9/+]{64}"
        self.create_commands()

    def set_locking_script(self,locking_script):
        self._locking_script = locking_script
    def set_unlocking_script(self,unlocking_script):
        self._unlocking_script = unlocking_script
    def set_hash_data(self,data):
        self._hash_data = data


    #########################################
        ######  Processing section #####
    #########################################
    def process(self):
        try:
            script = self._unlocking_script+"  " + self._locking_script
            self._Script_List = script.split("  ")
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

        return self.validate_stack()
            
        
    def create_commands(self):
        self._Commands = {
            "OP_DUP":self.OP_DUP,
            "OP_HASH":self.OP_HASH,
            "OP_SIGVERIFY":self.OP_SIGVERIFY,
            "OP_EQUAL":self.OP_EQUAL,
            "OP_EQUALVERIFY":self.OP_EQUALVERIFY,
            "OP_DROP":self.OP_DROP,
            "IF":self.OP_IF}

    def OP_DUP(self):
        self._stack.push(self._stack.peek())

    def OP_HASH(self):
        hash_item = self._stack.pop()
        self._stack.push(hashlib.sha256(str(hash_item).encode()).hexdigest())

    def OP_SIGVERIFY(self):  # Signature public_key on stack   -> front
        public_key = self._stack.pop()
        sig = base64_System.b64_to_bstr(self._stack.pop().encode())
        PuKO = ecdsa.VerifyingKey.from_string(base64_System.b64_to_bstr(public_key))
        try:
            PuKO.verify(sig,self._hash_data.encode())
        except Exception as e:
            print(e)
            self._stack.push("False")
        

    def OP_EQUAL(self):
        A,B = self._stack.pop(),self._stack.pop()
        if A == B:
            self._stack.push("True")
        else:
            self._stack.push("False")
    def OP_EQUALVERIFY(self):
        A,B = self._stack.pop(),self._stack.pop()
        if A != B:
            raise Exception("OP_EQUALVERIFY failed on "+str(A)+" and  "+str(B))
        

    def OP_DROP(self):  #Drop the top stack item
        self._stack.pop()

    def OP_IF(self):
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

        Go_Else = True
        for x in range(len(code_sections)-1):
            if self._stack.pop() in ["1","True"]:
                print(code_sections[x])
                for item in code_sections[x][::-1]:
                    self._Script_List.insert(0,item)
                Go_Else = False
                break
        if Go_Else:
            for item in code_sections[-1][::-1]:
                self._Script_List.insert(0,item)
            
        print("IF SYSTEM:",code_sections)
        print("IF SYSTEM:",self._Script_List)


    def validate_stack(self):
        """ In order to be valid the script stack must finish with either empty or only 1/True strings left over. """
        x = []
        while self._stack.get_size() > 0:
            if str(self._stack.pop()) not in ["1","True"]:  # This is to prevent the system seeing arbitary items as True values
                return False
        return True  # If the stack is empty or everything is True


    #####################################################
        ######  Solving/Identification section #####
    #####################################################

    def find_addresses(self):
        return re.findall(self._address_re_pattern,self._locking_script)      #Identifies addresses as 64 charater long hex values, may get confused with other hashed values.
    def contained_wallet_addresses(self,wallet_addresses):
        return set(wallet_addresses).intersection(set(self.find_addresses()))
    def for_wallet(self,wallet_addresses):
        return len(self.contained_wallet_addresses(wallet_addresses)) > 0



    def locking_script_type(self):
        """
        Script identification
        This section will deal with the identification of script types using regex.
        Locking script types: Type:[Locking script,solution]
        0:["UNKNOWN","UKNOWN"]
        ######1:["OP_DUP OP_HASH Address OP_EQUALVERIFY OP_SIGVERIFY","Signature Public_key"]
        +------+---------------------------------------------------------------+---------------------------------+
        | Type |                         Locking_Script                        |         Unlocking_Script        |
        +------+---------------------------------------------------------------+---------------------------------+
        |  0   |                            UNKNOWN                            |              UNKNOWN            |
        |  1   | (OP_DUP OP_HASH Address OP_EQUALVERIFY OP_SIGVERIFY)*multiple | Signature Public_key * multiple |
        |  4   |               public_key OP_SIGVERIFY* multiple               |       Signature* multiple       |
        +------+---------------------------------------------------------------+---------------------------------+
        """

##        if re.match("^OP_DUP  OP_HASH  "+ self._address_re_pattern+"  OP_EQUALVERIFY  OP_SIGVERIFY$",self._locking_script):
##            return "TYPE_1"
        if re.match("^(OP_DUP  OP_HASH  "+ self._address_re_pattern+"  OP_EQUALVERIFY  OP_SIGVERIFY(  )?)+$",self._locking_script):
            return "TYPE_1"
        
##        elif re.match("^"+self._public_key_pattern+"  OP_SIGVERIFY$",self._locking_script):
##            return "TYPE_3"
        elif re.match("^("+self._public_key_pattern+"  OP_SIGVERIFY(  )?)$",self._locking_script):
            return "TYPE_4"



        else:
            return "TYPE_0"

    def solve(self,locking_script_type,wallet):
        """
        Script solution
        This section produces solutions for the various locking script types
        """
        if type(locking_script_type) == int:
            locking_script_type = "TYPE_"+str(locking_script_type)
    
##        if locking_script_type == "TYPE_1": 
##            address = self.find_addresses()[0]        #Finds the address, only a single address so first item
##            signature = wallet.sign(address,self._hash_data)
##            return signature + "  " + wallet.get_public_key(address)

        if locking_script_type == "TYPE_1":
            locking_scripts =[]
            for section in re.findall("OP_DUP  OP_HASH  "+ self._address_re_pattern+"  OP_EQUALVERIFY  OP_SIGVERIFY",self._locking_script):
                address = re.findall(self._address_re_pattern,section)[0]     #Finds address
                signature = wallet.sign(address,self._hash_data)
                locking_scripts.append(signature + "  " + wallet.get_public_key(address))
            return "  ".join(locking_scripts)

##        elif locking_script_type == "TYPE_3":
##            public_key = re.findall(self._public_key_pattern,self._locking_script)[0]
##            return wallet.sign(wallet.to_address(public_key),self._hash_data)

        elif locking_script_type == "TYPE_4":
            locking_scripts = []
            for section in re.findall(self._public_key_pattern+"  OP_SIGVERIFY",self._locking_script):
                public_key = re.findall(self._public_key_pattern,section)[0]
                locking_scripts.append(wallet.sign(wallet.to_address(public_key),self._hash_data))
            return "  ".join(locking_scripts)












        
def P2PKH_test():
    w = Wallet_System.Wallet()
    w.load_wallet()
    x ="OP_DUP  OP_HASH  6dee6d35267bb441455bf045e5e55fe2493fcae52f6d86a0800a6f7749c4ad2c  OP_EQUALVERIFY  OP_SIGVERIFY"
    y = "  ".join([x for i in range(3)])
    s = Script_Processor()
    s.set_locking_script(y)
    unl = s.solve(1,w)
    s.set_unlocking_script(unl)
    print(s.process())
        
    
def P2PK_test():
    w = Wallet_System.Wallet()
    w.load_wallet()
    x ="ZkKfKHpMqIU2p3DqgKWAdf0qeSodoEN944b/1To7Ye6St2+VbjhY7fW+g5d0MiN6  OP_SIGVERIFY"
    y = "  ".join([x for i in range(3)])
    s = Script_Processor()
    s.set_locking_script(y)
    unl = s.solve(4,w)
    s.set_unlocking_script(unl)
    print(s.process())
    
def if_test():
    s = Script_Processor()
    s.set_unlocking_script("False  True")
    s.set_locking_script("IF  IF  IF  1  ELSE  2  ENDIF  1  2  ELSE  x  ENDIF  ELIF  2  3  4  ELSE  a  a  a  ENDIF  x  OP_EQUALVERIFY")
    print("Result:",s.process())



