import Database_System,Script_System,json,copy,hashlib

class Transaction:
    def __init__(self,db_con = None):
        self._in = []
        self._out = []
        self._TimeStamp = 0

        if db_con is None:
            db_con = Database_System.DBConnection()
        self._db_con = db_con

    def Import(self,Transaction):
        self._in = Transaction["in"]
        self._out = Transaction["out"]
        self._TimeStamp = Transaction["TimeStamp"]

    def json_import(self,Transaction):
        self.Import(json.loads(Transaction))

    def Export(self):
        return {
            "in":self._in,
            "out":self._out,
            "TimeStamp":self._TimeStamp}

    def json_export(self):
        return json.dumps(self.Export(),sort_keys = True)

    #############################################

    def Get_Inputs(self):
        return self._in
    def Get_Outputs(self):
        return self._out
    def Get_TimeStamp(self):
        return self._TimeStamp
    def Is_Coinbase(self):
        return not(len(self._in))  #if has no inputs then must be coinbase

    ##############################################

    

    def Add_Input(self,Prev_Transaction_Hash,Index = 0):
        utxo = Get_Prev_Transaction(self._db_con,Prev_Transaction_Hash,Index)
        
        if utxo["Lock_Time"] > Time:
            raise Exception("Transaction output not yet unlocked")
##        tx_script = utxo["ScriptPubKey"]        
        
        self._in.append(
            {"Prev_Tx":Prev_Transaction_Hash,
             "Sig":"",
             "Index":Index,})

    def Add_Output(self,Value,Locking_Script,Lock_Time):
        if Value < 0:
            raise Exception("Negative values are illegal")
        self._out.append({
            "Value":Value,
            "ScriptPubKey":Locking_Script,
            "Lock_Time":Lock_Time,})

    def Sign(self,Wallet,TimeStamp):
        self._TimeStamp = TimeStamp
        raw_signature = self.Raw_Transaction_Sig(self.Export())
        for tx_in in self._in:
            address = Find_Address(Wallet,Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])["ScriptPubKey"])
            public_key = Wallet.Get_Public_Key(address)
            signature = Wallet.Sign(address,raw_signature)
            sig = signature + "  " + public_key
            tx_in["Sig"] = sig

    def Verify(self):
        self.Verify_Values()
        SP = Script_System.Script_Processor()
        raw_sig = self.Raw_Transaction_Sig(self.Export())
        for tx_in in self._in:
            prev_tx = Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])
            if not SP.process(tx_in["Sig"]+ "  " + raw_sig + "  " + prev_tx["ScriptPubKey"]):
                raise Exception("Transaction input does not satisfy the locking script of the previous transaction")

    def Verify_Values(self):
        fee = self.Get_Fee()
        if fee < 0:
            raise Exception("Outputs greater than input")
        return fee

    def Get_Fee(self):
        sum_inputs = 0
        sum_outputs = 0
        for tx_in in self._in:
            sum_inputs += Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])["Value"]
        for tx_out in self._out:
            value = tx_out["Value"]
            if value < 0:
                raise Exception("Negative Values are illegal")
            sum_outputs += value

        return sum_inputs-sum_outputs
        


    def Raw_Transaction_Sig(self):
        Transaction_Copy = json.loads(json.dumps(self.Export())) # forms independant copy of transaction.
        for tx_in in Transaction_Copy["in"]:
            tx_in["Sig"] = ""
        raw_sig = hashlib.sha256(json.dumps(Transaction_Copy,sort_keys = True).encode()).hexdigest()
        return raw_sig

            


    def Transaction_Hash(self):
        return hashlib.sha256(self.json_export().encode()).hexdigest()
            




###########################################################
    

def Create_Transaction(Wallet,Input_Transactions,Output_Transactions,Time):
    #Input_Transactions  <- List of transactions in form {Transaction_Hash,Index}
    #Output_Transactions <- list of transactions in form {Value, Locking Script,LockTime}
    transaction = {
        "in":[],
        "out":Output_Transactions,
        "TimeStamp":Time}

    new_inputs,new_inputs_addresses,funds_available = Obtain_Input_Transactions(Wallet,Input_Transactions,Time)  #Obtain all input transactions and addresses
    if Check_Output_Values(Output_Transactions, funds_available):
        raise Exception("Output values are not valid")
    
    transaction["in"] = new_inputs
    sigs = []
    raw_sig = Get_Transaction_Signature(transaction)
    for address in new_inputs_addresses:   #Generate the signatures required
        public_key = Wallet.Get_Public_Key(address)
        signature = Wallet.Sign(address,raw_sig)
        sig = signature + "  " + public_key
        sigs.append(sig)
        
    for x in range(len(sigs)):  #Transfer the signatures to the transaction
        transaction["in"][x]["Sig"] = sigs[x]
    return transaction
        

def Obtain_Input_Transactions(Wallet,Input_Transactions,Time):
    db_con = Database_System.DBConnection()
    new_inputs = []
    new_inputs_addresses = []
    funds_available = 0
    for tx_dict in Input_Transactions:
        new_input = {
            "Prev_Tx":tx_dict["Hash"],
            "Sig":"",
            "Index":tx_dict["Index"]}
        utxo = db_con.Get_Transaction(tx_dict["Hash"],tx_dict["Index"])
        if len(utxo) == 0:
            raise Exception("No such transaction "+tx_dict["Hash"])
        utxo = json.loads(utxo[0][1])
        
        if utxo["Lock_Time"] > Time:
            raise Exception("Transaction output not yet unlocked")
        tx_script = utxo["ScriptPubKey"]
        new_inputs_addresses.append(Find_Address(Wallet,tx_script))
        new_inputs.append(new_input)
        funds_available += utxo["Value"]
    return new_inputs,new_inputs_addresses,funds_available

            

def Find_Address(Wallet,tx_script):
    Sucess = False
    for address in Wallet.Get_Addresses():
        if address in tx_script:
            Sucess = True
            break
    if Sucess:
        return address
    else:
        raise Exception("You do not own the address for this transaction")

def Pay_To_Address_Script(Address):
    return "OP_DUP  OP_HASH  "+Address+"  OP_EQUAL  OP_VERIFY"

def Get_Prev_Transaction(db_con,Prev_Transaction_Hash,Index):
    utxo = db_con.Get_Transaction(Prev_Transaction_Hash,Index)
    if len(utxo) == 0:
        raise Exception("No such transaction "+Prev_Transaction_Hash)
    utxo = json.loads(utxo[0][1])
    return utxo



######    Validate   ######

def Check_Output_Values(Output_Transactions,funds_available):
    Check_Outputs_For_Negative(Output_Transactions)
    sum_out = 0
    for transaction in Output_Transactions:
        sum_out += transaction["Value"]
    return sum_out <= funds_available

def Check_Outputs_For_Negative(Outputs):
    for output in Outputs:
        if output["Value"] < 0:
            raise Exception("Negative outputs are illegal")


def Validate_Transaction(Transaction,Time):  #dictionary form transaction
    db_con = Database_System.DBConnection()
    sum_inputs,sum_outputs = 0,0
    
    SP = Script_System.Script_Processor()
    raw_sig = Get_Transaction_Signature(Transaction)

    for tx_in in Transaction["in"]:
        prev_tx = db_con.Get_Transaction(tx_in["PrevTx"],tx_in["Index"])
        if len(prev_tx) == 0:
            raise Exception("Transaction has invalid input transaction")
        prev_tx = json.loads(prev_tx)
        sum_inputs += prev_tx["Value"]
##        Signature,Public_Key = tx_in["Sig"]
##        if not SP.process(Signature + "  " + raw_sig + "  " + Public_Key + prev_tx["ScriptPubKey"]):
        if not SP.process(tx_in["Sig"]+ "  " + raw_sig + "  " + prev_tx["ScriptPubKey"]):
            raise Exception("Transaction input does not satisfy the locking script of the previous transaction")
        if prev_tx["Lcck_Time"] > Time:
            raise Exception("Previous transaction is not yet valid")

    Check_Outputs_For_Negatives(Transaction["out"])
    for out in Transaction["out"]:
        sum_outputs += out["Value"]

    fee = sum_inputs - sum_outputs
    if fee < 0:
        raise Exception("Output exceeds input")
    
        
        
    
            
        
