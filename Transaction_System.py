import Database_System,Script_System,json,copy,hashlib, autorepr, copy

class Transaction(autorepr.Base):
    def __init__(self,db_con = None):
##        self._tx_hash = ""
        self.logger_setup(__name__)
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
        self._is_coinbase = value
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

    def add_output(self,value,locking_script,lock_time = 0):
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
                if prev_tx["Lock_Time"] > current_time:
                    raise Exception("Transaction output not yet unlocked. Current time is less than lock time")

                script_processor.set_unlocking_script(tx_in["Sig"])
                script_processor.set_locking_script(prev_tx["ScriptPubKey"])
                script_processor.set_hash_data(message)

                if not script_processor.process():
                    raise Exception("Transaction input does not satisfy the locking script of the previous transaction")
            return True
        except Exception as e:
            self._logger.error("Exception verifying transaction", exc_info = True)
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
        Transaction_Copy = copy.deepcopy(self.tx_export()) # forms independant copy of transaction.
##        Transaction_Copy.pop("Tx_Hash")
        for tx_in in Transaction_Copy["in"]:
            tx_in["Sig"] = ""
        raw_sig = hashlib.sha256(json.dumps(Transaction_Copy,sort_keys = True).encode()).hexdigest()
        return raw_sig

        
##    def calculate_tx_hash(self):
##        return hashlib.sha256(self.json_export().encode()).hexdigest()

    def finance_transaction(self,wallet,current_time,sorting_policy = [],tx_fee = 1, debug_verify = True):
        #This method is used to populate a transaction with UTXOs to finance the outputs plus the tx_fee
        #sorting_policy describes what system should be used to select the UTXOs i.e. random, highest_first, lowest_first, oldest_first, newest_first
        #debug verify will set if the program should check the transaction solution is correct or not.
        #the method will raise an error if it cannot complete financing.
        #the transaction will not be signed - only filled
        deficit = self.get_fee()*-1+tx_fee     #deficit is the amount the method must still collect to finance the transaction
        utxos = self._db_con.Find_Address_UTXOs(list(wallet.get_addresses()),sorting_policy = sorting_policy)
        script_processor = Script_System.Script_Processor()
        for utxo_info in utxos:
            if deficit <= 0:
                break
            if len(utxos) == 0:
                raise Exception("No more UTXOs. Cannot finance transaction")
            utxo = json.loads(utxo_info[1])
            if utxo["Lock_Time"] > current_time:
                continue    #Cannot be used as not yet unlocked
            script_processor.set_locking_script(utxo["ScriptPubKey"])
            script_type = script_processor.locking_script_type()
            if script_type != "TYPE_0":
                unlocking_script = script_processor.solve(script_type,wallet)   #This checks the tx is probably solvable
            else:
                continue

            correct = True
            if debug_verify:
                script_processor.set_unlocking_script(unlocking_script)
                correct = script_processor.process()
            if correct:
                self.add_input(utxo_info[0],utxo_info[2])
                deficit -= utxo["Value"]
            
            
            


    def __str__(self):
        data = [
            ("Tx_Hash",self.get_transaction_hash()),
            ("Inputs",self._in),
            ("Outputs",self._out),
            ("TimeStamp",self._timestamp)]
        return autorepr.str_repr(self,data)
            





def Pay_To_Address_Script(Address):
    return "OP_DUP  OP_HASH  "+Address+"  OP_EQUALVERIFY  OP_SIGVERIFY"

def Get_Prev_Transaction(db_con,Prev_Transaction_Hash,Index):
    utxo = db_con.Get_Transaction(Prev_Transaction_Hash,Index)
    if len(utxo) == 0:
        raise Exception("No such transaction "+Prev_Transaction_Hash)
    utxo = json.loads(utxo[0][1])
    return utxo


def test_financing():
    import Wallet_System
    w = Wallet_System.Wallet()
    w.load_wallet()
    target_address = w.generate_new_address()
    w.save_wallet()
    t = Transaction()
    t.add_output(60,target_address)
    t.finance_transaction(w,1000)
    return w,t

