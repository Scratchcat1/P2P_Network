import Merkle_Tree,Database_System,Transaction_System,json,hashlib


class Block:
    def __init__(self,Difficulty = -1,Block_Number = -1, Prev_Block_Hash = ""):
        self._Block_Hash = ""
        self._Difficulty = Difficulty
        self._Merkle_Root = ""
        self._Block_Number = Block_Number
        self._Prev_Block_Hash = Prev_Block_Hash
        self._Transactions = []
        self._TimeStamp = 0
        self._Nonce = 0
        self._db_con = Database_System.DBConnection()

    def Import(self,block):
        self._Block_Hash = block["Block_Hash"]
        self._Difficulty = block["Difficulty"]
        self._Merkle_Root = block["Merkle_Root"]
        self._Block_Number = block["Block_Number"]
        self._Prev_Block_Hash = block["Prev_Block_Hash"]
        self._Transactions = block["Transactions"]
        self._TimeStamp = block["TimeStamp"]
        self._Nonce = block["Nonce"]

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
            merkle_tree.Add_Hash(tx.Transaction_Hash())

        merkle_root = merkle_tree.Calculate_Root()
        return merkle_root

    def Set_Merkle_Root(self,merkle_root):
        self._Merkle_Root = merkle_root

    ######### Verification ##############
    
    def Verify_Transactions(self):
        coinbase_count = 0
        coinbase_tx = None
        fee = 0
        for tx in self.Get_Transaction_Objects():
            if tx.Is_Coinbase():   #Coinbase does not need to verify inputs as it has none
                coinbase_count += 1
                coinbase_tx = tx
            else:
                fee += tx.Verify()
                
        if coinbase_count > 1:
            raise Exception("More than one coinbase transaction is not allowed")
        if fee+50 < coinbase_tx.Get_Fee()*-1:
            raise Exception("Coinbase output more than fees + 50")

    def Verify_Merkle_Root(self):
        if self.Calculate_Merkle_Root() != self._Merkle_Root:
            raise Exception("Invalid merkle root")  #Must be valid merkle root

    def Verify_Prev_Details(self):
        block = self._db_con.Get_Block(self._Prev_Block_Hash)
##        if len(block) == 0:
##            raise Exception("No such previous Block")
##        block = block[0]
##        if block[1] != self.Block_Number -1:  #Block numbers not sequential
##            raise Exception("Block number is not sequential")

    def Verify_Block_Hash(self):
        json_source = self.Get_Raw_Hash_Source()
        hash_value = hashlib.sha256(json_source.encode()).hexdigest()
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
            block_hash = block[4] # next prev block hash

##        median_time = sum([block[5] for block in prev_blocks])/len(prev_blocks)
##        if median_time > self._TimeStamp:
##            raise Exception("Block is older than median time")

    def Verify(self, Time, Difficulty):
        if not self._Difficulty == Difficulty:
            raise Exception("Block has invalid difficulty value")
        self.Verify_Prev_Details()
        self.Verify_Block_Hash()
        self.Verify_TimeStamp(Time)
        self.Verify_Merkle_Root()
        self.Verify_Transactions()

    ###############################################

    def Mine(self, iterations = 100000):
        for i in range(iterations):
            self._Nonce = i
            raw_hash_source = self.Get_Raw_Hash_Source()
##            raw_hash_source["Nonce"] = i
            block_hash = hashlib.sha256(raw_hash_source.encode()).hexdigest()
            if int(block_hash,16) < 2**256 - self._Difficulty:
                print("Found block hash:",block_hash,"after",i,"iterations")
                self._Block_Hash = block_hash
                return block_hash
            
        print("Failed to find hash after ",iterations,"iterations")
        return False


    def Update_UTXO(self):  #Remove inputs from utxo and add outputs to utxo
        old_utxos = []# this will contain all the old transaction details. If a rebase were necessary then the transaction details would be included with the block which changed them and would not need to be obtained from searching the blockchain
        for tx in self.Get_Transaction_Objects():
            for tx_in in tx.Get_Inputs():
                old_utxos.append(self._db_con.Remove_Transaction(tx_in["Prev_Tx"],tx_in["Index"]))
            for index,tx_out in enumerate(tx.Get_Outputs()):
                self._db_con.Add_Transaction(tx.Transaction_Hash(),json.dumps(tx_out),index,tx_out["Value"],self._Block_Hash)
                
        return old_utxos

    def Rollback_UTXO(self,old_utxos):
        for old_utxo in old_utxos:
            self._db_con.Add_Transaction(*old_utxo)  #old_tx is dump of utxo, this adds it back in

        for tx in self.Get_Transaction_Objects():
            for index,tx_out in enumerate(tx.Get_Outputs()):
                self._db_con.Remove_Transaction(tx.Transaction_Hash(),index)
                
        
    
        
    

















def test():
    import Wallet_System
    w = Wallet_System.Wallet()
    w.Load_Wallet()
    t = Transaction_System.Transaction()
    b = Block(Block_Number = 0)
    t.Add_Output(50,Transaction_System.Pay_To_Address_Script('258a4410e9d9cea10cd5efd9885422ad69b1bec8dd2c9555c37f87587a47b222'),0)
    b.Add_Transaction(t)
    print(t.Is_Coinbase())
    b.Set_Merkle_Root(b.Calculate_Merkle_Root())
    b.Mine()
    b.Verify(1000,-1)
    





    
        
