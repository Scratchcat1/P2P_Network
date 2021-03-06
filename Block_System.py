import Merkle_Tree,Database_System,Transaction_System,json,hashlib,Script_System
import autorepr

class Block(autorepr.Base):
    def __init__(self,Difficulty = -1,Block_Number = -1, Prev_Block_Hash = "",db_con = None):
        self.logger_setup(__name__)
        self._Block_Hash = ""
        self._Difficulty = Difficulty
        self._Merkle_Root = ""
        self._Block_Number = Block_Number
        self._Prev_Block_Hash = Prev_Block_Hash
        self._Transactions = []
        self._TimeStamp = 0
        self._Nonce = 0

        if db_con is None:
            db_con = Database_System.DBConnection()  #Helps with excessive creation of connections as can use same for multiple items.
        self._db_con = db_con

    def Import(self,block):
        self._Block_Hash = block["Block_Hash"]
        self._Difficulty = block["Difficulty"]
        self._Merkle_Root = block["Merkle_Root"]
        self._Block_Number = block["Block_Number"]
        self._Prev_Block_Hash = block["Prev_Block_Hash"]
        self._Transactions = block["Transactions"]
        self._TimeStamp = block["TimeStamp"]
        self._Nonce = block["Nonce"]

    def import_json(self,block_json):
        self.Import(json.loads(block_json))

    def Export(self):
        return {
            "Block_Hash":self._Block_Hash,
            "Difficulty":self._Difficulty,
            "Merkle_Root":self._Merkle_Root,
            "Block_Number":self._Block_Number,
            "Prev_Block_Hash":self._Prev_Block_Hash,
            "Transactions":self._Transactions,
            "TimeStamp":self._TimeStamp,
            "Nonce":self._Nonce,}

    def export_json(self):
        return json.dumps(self.Export())

    def Set_TimeStamp(self,TimeStamp):
        self._TimeStamp = TimeStamp
    def Set_Block_Hash(self,block_hash):
        self._Block_Hash = block_hash

    def Get_Block_Hash(self):
        return self._Block_Hash
    def Get_Block_Number(self):
        return self._Block_Number
    def Get_Difficulty(self):
        return self._Difficulty
    def Get_Prev_Block_Hash(self):
        return self._Prev_Block_Hash
    def Get_TimeStamp(self):
        return self._TimeStamp

    def Add_Transaction(self,Transaction):
        self._Transactions.append(Transaction.json_export())

    def Get_Transaction_Objects(self):
        txs = []
        for tx_json in self._Transactions:
            tx = Transaction_System.Transaction(db_con = self._db_con)
            tx.json_import(tx_json)
            txs.append(tx)
        return txs

    def Get_Raw_Hash_Source(self):
        source = self.Export()
        source.pop("Block_Hash")  # Alternatively set to constant
        source.pop("Transactions")
        json_source = json.dumps(source,sort_keys = True)
        return json_source

    def Calculate_Merkle_Root(self):
        merkle_tree = Merkle_Tree.Merkle_Tree()
        txs = self.Get_Transaction_Objects()
        for tx in txs:
            merkle_tree.Add_Hash(tx.get_transaction_hash())

        merkle_root = merkle_tree.Calculate_Root()
        return merkle_root

    def Set_Merkle_Root(self,merkle_root):
        self._Merkle_Root = merkle_root

    ######### Verification ##############
    
    def Verify_Transactions(self):
        coinbase_count = 0
        coinbase_tx = None
        fee = 0
        used_utxos = set()
        for tx in self.Get_Transaction_Objects():
            if tx.get_is_coinbase():   #Coinbase does not need to verify inputs as it has none
                coinbase_count += 1
                coinbase_tx = tx
            else:
                if not tx.verify(self._TimeStamp):  #Timestamp allows checking of lock time
                    raise Exception("Transaction",tx.get_transaction_hash()," is not valid")
                fee += tx.get_fee()
                for input_utxo in tx.get_input_utxos():  #Ensures that the utxo has not been used before
                    if input_utxo in used_utxos:
                        raise Exception("Double spend detected. Two transactions reference same input")
                    used_utxos.add(input_utxo)
                
        if coinbase_count > 1:
            raise Exception("More than one coinbase transaction is not allowed")
        if fee+50 < coinbase_tx.get_fee()*-1:
            raise Exception("Coinbase output more than fees + 50")

    def Verify_Merkle_Root(self):
        if self.Calculate_Merkle_Root() != self._Merkle_Root:
            raise Exception("Invalid merkle root")  #Must be valid merkle root

    def Verify_Prev_Details(self):
        block = self._db_con.Get_Block(self._Prev_Block_Hash)
        if len(block) == 0:
            raise Exception("No such previous Block")
        block = block[0]
        if block[1] != self._Block_Number -1:  #Block numbers not sequential
            raise Exception("Block number is not sequential")

    def Verify_Block_Hash(self):
        json_source = self.Get_Raw_Hash_Source()
        hash_value = hashlib.sha256(json_source.encode()).hexdigest()
##        print(hash_value)
        if not (hash_value == self._Block_Hash and int(hash_value,16) < 2**256 - self._Difficulty):
            raise Exception("Invalid block hash value")

    def Verify_TimeStamp(self,Time):
        if self._TimeStamp - 2*3600 > Time:
            raise Exception("Block too far into future")

        prev_blocks = []
        block_hash = self._Prev_Block_Hash
        while len(prev_blocks) < 12:
            block = self._db_con.Get_Block(block_hash)
            if len(block) == 0:
                break
            prev_blocks.append(block[0])
            block_hash = block[0][4] # next prev block hash

        median_time = sum([block[5] for block in prev_blocks])/len(prev_blocks)
        if median_time > self._TimeStamp:
            raise Exception("Block is older than median time")

    def Verify(self, Time, Difficulty):
        try:
            if not self._Difficulty == Difficulty:
                raise Exception("Block has invalid difficulty value")
            self.Verify_Prev_Details()
            self.Verify_Block_Hash()
            self.Verify_TimeStamp(Time)
            self.Verify_Merkle_Root()
            self.Verify_Transactions()
            return True
        except Exception as e:
            self._logger.debug("Exception in verification of block. Error: %s" % (e,))
            return False

    ###############################################
    def Mine(self, iterations = 100000):
        raw_hash_source = json.loads(self.Get_Raw_Hash_Source())
        for i in range(iterations):
            raw_hash_source["Nonce"] = i
            block_hash = hashlib.sha256(json.dumps(raw_hash_source,sort_keys = True).encode()).hexdigest()
            if int(block_hash,16) < 2**256 - self._Difficulty:
                self._logger.info("Found block hash: %s after %s iterations" % (block_hash,i))
                self._Nonce = i
                self._Block_Hash = block_hash
                return block_hash
            
##        print("Failed to find hash after ",iterations,"iterations")
        return False


    def Update_UTXO(self,Mempool):       #Remove inputs from utxo and add outputs to utxo
        self._logger.info("Adding block %s UTXOs to the UTXO" % (self._Block_Hash,))
        old_utxos = []                   # this will contain all the old transaction details. If a rebase were necessary then the transaction details would be included with the block which changed them and would not need to be obtained from searching the blockchain
        script_processor = Script_System.Script_Processor()
        for tx in self.Get_Transaction_Objects():
            Mempool.remove_tx(tx.get_transaction_hash())            #Removes the relevant transactions which are in the block
            for tx_in in tx.get_inputs():
                old_utxos.append(self._db_con.Remove_Transaction(tx_in["Prev_Tx"],tx_in["Index"]))
            for index,tx_out in enumerate(tx.get_outputs()):
                script_processor.set_locking_script(tx_out["ScriptPubKey"])
                self._db_con.Add_Transaction(tx.get_transaction_hash(),json.dumps(tx_out),index,tx_out["Value"],self._Block_Hash)
                self._db_con.Link_Transaction_Addresses(tx.get_transaction_hash(),index,script_processor.find_addresses())
        return old_utxos

    def Rollback_UTXO(self,old_utxos,Mempool):
        self._logger.info("Removing block %s UTXOs to the UTXO" % (self._Block_Hash,))
        script_processor = Script_System.Script_Processor()
        for old_utxo in old_utxos:
            script_processor.set_locking_script(old_utxo[1])
            self._db_con.Add_Transaction(*old_utxo)  #old_tx is dump of utxo, this adds it back in
            self._db_con.Link_Transaction_Addresses(old_utxo[0],old_utxo[2],script_processor.find_addresses())

        for tx in self.Get_Transaction_Objects():
            if not tx.get_is_coinbase(): #Coinbase transactions should not be readded
                Mempool.add_transaction_json(tx.get_transaction_hash(),tx.json_export(),tx.get_fee())  #Readds the transaction
            for index,tx_out in enumerate(tx.get_ouputs()):
##                print(tx.Transaction_Hash(),index)
##                print(self._Block_Hash)
                self._db_con.Remove_Transaction(tx.get_transaction_hash(),index)


                
    def __str__(self):
        data = [
            ("Block_Hash",self._Block_Hash),
            ("Block_Number",self._Block_Number),
            ("Difficulty",self._Difficulty),
            ("Merkle_Root",self._Merkle_Root),
            ("Prev_Block_Hash",self._Prev_Block_Hash),
            ("Transactions",len(self._Transactions)),
            ("TimeStamp",self._TimeStamp),
            ("Nonce",self._Nonce)
            ]
        return autorepr.str_repr(self,data)
    
    

















def test(bn = 0,tim = 0,dif = 1,pblk = ""):
    import Wallet_System
    db_con = Database_System.DBConnection()
##    w = Wallet_System.Wallet()
##    w.Load_Wallet()
    w = None
    b = Block(Block_Number = bn,Difficulty = dif,Prev_Block_Hash=pblk,db_con = db_con)
##    print(t.Transaction_Hash())
    t = coinbase_tx(tim)
    b.Add_Transaction(t)
    b.Set_TimeStamp(tim)
##    print(t.Is_Coinbase())
    b.Set_Merkle_Root(b.Calculate_Merkle_Root())
    b.Mine()
    b.Verify(tim,dif)
    return w,t,b
    
    
def coinbase_tx(tim):
    t = Transaction_System.Transaction()
    t.add_output(50,Transaction_System.Pay_To_Address_Script('ac236dce52860e10fda735c743ac54d565a089b19d2addcdfd501610cd564379'))
    t.set_timestamp(tim)
    t.set_is_coinbase(True)
    return t
