import Database_System,Script_System,json,copy,hashlib, autorepr

class Transaction(autorepr.AutoRepr):
    def __init__(self,db_con = None):
##        self._tx_hash = ""
        self._is_coinbase = False
        self._in = []
        self._out = []
        self._timestamp = 0

        if db_con is None:
            db_con = Database_System.DBConnection()
        self._db_con = db_con

    def tx_import(self,Transaction):
##        self._tx_hash = Transaction["Tx_Hash"]
        self._is_coinbase = Transaction["Is_Coinbase"]
        self._in = Transaction["in"]
        self._out = Transaction["out"]
        self._timestamp = Transaction["TimeStamp"]

    def json_import(self,Transaction):
        self.tx_import(json.loads(Transaction))

    def tx_export(self):
        return {
##            "Tx_Hash":self._tx_hash,
            "Is_Coinbase":self._is_coinbase,
            "in":self._in,
            "out":self._out,
            "TimeStamp":self._timestamp}

    def json_export(self):
        return json.dumps(self.tx_export(),sort_keys = True)

    #############################################
##    def set_tx_hash(self,tx_hash):
##        self._tx_hash = tx_hash
    def set_is_coinbase(self,value):
        self._coinbase = value
    def set_timestamp(self,timestamp):
        self._timestamp = timestamp
    
    def get_transaction_hash(self):
        return hashlib.sha256(self.json_export().encode()).hexdigest()      #return self._tx_hash
    def get_inputs(self):
        return self._in
    def get_outputs(self):
        return self._out
    def get_timestamp(self):
        return self._timestamp
    def get_is_coinbase(self):
        return self._is_coinbase
    def get_input_utxos(self):
        #Get all inputs and return them
        input_utxos = []
        for tx_in in self._in:
            clean_tx_in = tx_in.copy()
            clean_tx_in.pop("Sig")
            input_utxos.append(clean_tx_in)
        return input_utxos

    ##############################################

    

    def add_input(self,prev_transaction_hash,index = 0):
##        utxo = Get_Prev_Transaction(self._db_con,prev_transaction_hash,index)
        
##        if utxo["Lock_Time"] > Time:
##            raise Exception("Transaction output not yet unlocked")
##        tx_script = utxo["ScriptPubKey"]        
        
        self._in.append(
            {"Prev_Tx":prev_transaction_hash,
             "Sig":"",
             "Index":index,})

    def add_output(self,value,locking_script,lock_time):
##        if Value < 0:
##            raise Exception("Negative values are illegal")
        self._out.append({
            "Value":value,
            "ScriptPubKey":locking_script,
            "Lock_Time":lock_time,})

    def sign(self,wallet,timestamp):
        self._timestamp = timestamp
        message = self.raw_transaction_sig()
        for tx_in in self._in:
            prev_utxo = Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])
            script_processor = Script_System.Script_Processor()
            script_processor.set_locking_script(prev_utxo["ScriptPubKey"])
            script_processor.set_hash_data(message)
            script_type = script_processor.locking_script_type()
            
            if script_type != "TYPE_0":
                unlocking_script = script_processor.solve(script_type,wallet)
                tx_in["Sig"] = unlocking_script
            else:
                raise Exception("Automatic transaction solver cannot identify type of locking script")

            
            

    def verify(self,current_time):
        try:
##            if self.calculate_tx_hash() != self._tx_hash:
##                raise Exception("Transaction hash does not match")
            if self.get_fee() < 0:
                raise Exception("Sum of outputs exceeds sum of inputs")
            script_processor = Script_System.Script_Processor()
            message = self.raw_transaction_sig()
            for tx_in in self._in:
                prev_tx = Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])
                if prev_tx["Lock_Time"] > Time:
                    raise Exception("Transaction output not yet unlocked. Current time is less than lock time")

                script_processor.set_unlocking_script(tx_in["Sig"])
                script_processor.set_locking_script(prev_tx["ScriptPubKey"])
                script_processor.set_hash_data(message)

                if not script_processor.process():
                    raise Exception("Transaction input does not satisfy the locking script of the previous transaction")
            return True
        except Exception as e:
            return False


    def get_fee(self):
        sum_inputs = 0
        sum_outputs = 0
        for tx_in in self._in:
            sum_inputs += Get_Prev_Transaction(self._db_con,tx_in["Prev_Tx"],tx_in["Index"])["Value"]
        for tx_out in self._out:
            value = tx_out["Value"]
            if value < 0:
                raise Exception("Negative Values are illegal")
            sum_outputs += value

##        if sum_inputs - sum_outputs < 0:        #Not really needed as if no negative outputs then cannot be negative
##            raise Exception("Negative values are illegal")

        return sum_inputs-sum_outputs
        


    def raw_transaction_sig(self):
        #tx digest bases on the values : inputs, outputs and timestamp, inputs do not have signatures
        Transaction_Copy = self.tx_export().copy() # forms independant copy of transaction.
##        Transaction_Copy.pop("Tx_Hash")
        for tx_in in Transaction_Copy["in"]:
            tx_in["Sig"] = ""
        raw_sig = hashlib.sha256(json.dumps(Transaction_Copy,sort_keys = True).encode()).hexdigest()
        return raw_sig

        
##    def calculate_tx_hash(self):
##        return hashlib.sha256(self.json_export().encode()).hexdigest()


    def __str__(self):
        data = [
            ("Tx_Hash",self.get_tx_hash()),
            ("Inputs",self._in),
            ("Outputs",self._out),
            ("TimeStamp",self.self._timestamp)]
        return autorepr.str_repr(self,data)
            




###########################################################
    

##def Create_Transaction(Wallet,Input_Transactions,Output_Transactions,Time):
##    #Input_Transactions  <- List of transactions in form {Transaction_Hash,Index}
##    #Output_Transactions <- list of transactions in form {Value, Locking Script,LockTime}
##    transaction = {
##        "in":[],
##        "out":Output_Transactions,
##        "TimeStamp":Time}
##
##    new_inputs,new_inputs_addresses,funds_available = Obtain_Input_Transactions(Wallet,Input_Transactions,Time)  #Obtain all input transactions and addresses
##    if Check_Output_Values(Output_Transactions, funds_available):
##        raise Exception("Output values are not valid")
##    
##    transaction["in"] = new_inputs
##    sigs = []
##    raw_sig = Get_Transaction_Signature(transaction)
##    for address in new_inputs_addresses:   #Generate the signatures required
##        public_key = Wallet.Get_Public_Key(address)
##        signature = Wallet.Sign(address,raw_sig)
##        sig = signature + "  " + public_key
##        sigs.append(sig)
##        
##    for x in range(len(sigs)):  #Transfer the signatures to the transaction
##        transaction["in"][x]["Sig"] = sigs[x]
##    return transaction
##        
##
##def Obtain_Input_Transactions(Wallet,Input_Transactions,Time):
##    db_con = Database_System.DBConnection()
##    new_inputs = []
##    new_inputs_addresses = []
##    funds_available = 0
##    for tx_dict in Input_Transactions:
##        new_input = {
##            "Prev_Tx":tx_dict["Hash"],
##            "Sig":"",
##            "Index":tx_dict["Index"]}
##        utxo = db_con.Get_Transaction(tx_dict["Hash"],tx_dict["Index"])
##        if len(utxo) == 0:
##            raise Exception("No such transaction "+tx_dict["Hash"])
##        utxo = json.loads(utxo[0][1])
##        
##        if utxo["Lock_Time"] > Time:
##            raise Exception("Transaction output not yet unlocked")
##        tx_script = utxo["ScriptPubKey"]
##        new_inputs_addresses.append(Find_Address(Wallet,tx_script))
##        new_inputs.append(new_input)
##        funds_available += utxo["Value"]
##    return new_inputs,new_inputs_addresses,funds_available

            

##def Find_Address(Wallet,tx_script):
##    Sucess = False
##    for address in Wallet.Get_Addresses():
##        if address in tx_script:
##            Sucess = True
##            break
##    if Sucess:
##        return address
##    else:
##        raise Exception("You do not own the address for this transaction")

def Pay_To_Address_Script(Address):
    return "OP_DUP  OP_HASH  "+Address+"  OP_EQUAL  OP_VERIFY"

def Get_Prev_Transaction(db_con,Prev_Transaction_Hash,Index):
    utxo = db_con.Get_Transaction(Prev_Transaction_Hash,Index)
    if len(utxo) == 0:
        raise Exception("No such transaction "+Prev_Transaction_Hash)
    utxo = json.loads(utxo[0][1])
    return utxo



######    Validate   ######

##def Check_Output_Values(Output_Transactions,funds_available):
##    Check_Outputs_For_Negative(Output_Transactions)
##    sum_out = 0
##    for transaction in Output_Transactions:
##        sum_out += transaction["Value"]
##    return sum_out <= funds_available
##
##def Check_Outputs_For_Negative(Outputs):
##    for output in Outputs:
##        if output["Value"] < 0:
##            raise Exception("Negative outputs are illegal")


##def Validate_Transaction(Transaction,Time):  #dictionary form transaction
##    db_con = Database_System.DBConnection()
##    sum_inputs,sum_outputs = 0,0
##    
##    SP = Script_System.Script_Processor()
##    raw_sig = Get_Transaction_Signature(Transaction)
##
##    for tx_in in Transaction["in"]:
##        prev_tx = db_con.Get_Transaction(tx_in["PrevTx"],tx_in["Index"])
##        if len(prev_tx) == 0:
##            raise Exception("Transaction has invalid input transaction")
##        prev_tx = json.loads(prev_tx)
##        sum_inputs += prev_tx["Value"]
####        Signature,Public_Key = tx_in["Sig"]
####        if not SP.process(Signature + "  " + raw_sig + "  " + Public_Key + prev_tx["ScriptPubKey"]):
##        if not SP.process(tx_in["Sig"]+ "  " + raw_sig + "  " + prev_tx["ScriptPubKey"]):
##            raise Exception("Transaction input does not satisfy the locking script of the previous transaction")
##        if prev_tx["Lcck_Time"] > Time:
##            raise Exception("Previous transaction is not yet valid")
##
##    Check_Outputs_For_Negatives(Transaction["out"])
##    for out in Transaction["out"]:
##        sum_outputs += out["Value"]
##
##    fee = sum_inputs - sum_outputs
##    if fee < 0:
##        raise Exception("Output exceeds input")
##    
##        
##        
##    
##            
##        
