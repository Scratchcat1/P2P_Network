import Merkle_Tree,Database_System,Transaction_System


class Block:
    def __init__(self):
        self._Block_Hash
        self._Difficulty
        self._Merkle_Root
        self._Block_Number
        self._Prev_Block_Hash
        self._Transactions = []
        self._TimeStamp
        self._Nonce
        self._db_con.Database_System.DBConnection()

    def Import(self,Block):
        self._Block_Hash = Block["Block_Hash"]
        self._Difficulty = Block["Difficulty"]
        self._Merkle_Root = Block["Merkle_Root"]
        self._Block_Number = Block["Block_Number"]
        self._Prev_Block_Hash = Block["Prev_Block_Hash"]
        self._Transactions = Block["Transactions"]
        self._TimeStamp = Block["TimeStamp"]
        self._Nonce = Block["Nonce"]

    def Export(self):
        return {
            "Block_Hash":self._Block_Hash
            "Difficulty":self._Difficulty,
            "Merkle_Root":self._Merkle_Root,
            "Block_Number":self._Block_Number,
            "Prev_Block_Hash":self._Prev_Block_Hash,
            "Transactions":self._Transactions,
            "TimeStamp":self._TimeStamp,
            "Nonce":self._Nonce,}

    def Add_Transaction(self,Transaction):
        self._Transactions.append(Transaction.json_export())

    def Get_Transaction_Objects(self):
        txs = []
        for tx_json in self._Transactions:
            tx = Transaction_System.Transaction(db_con = self._db_con)
            tx.json_import(tx_json)
            txs.append(tx)
        return txs
    
    def Verify_Transactions(self):
        for tx in self.Get_Transaction_Objects():
            tx.Verify()

    def Verify_Merkle_Root(self):
        merkle_tree = Merkle_Tree.Merkle_Tree()
        txs = self.Get_Transaction_Objects()
        for tx in txs:
            merkle_tree.Add_Hash(tx.Transaction_Hash())

        return merkle_root.Verify(self._Merkle_Root)

    def Verify_Prev_Details(self):
        block = self._db_con.Get_Block(self._Prev_Block_Hash)
        if len(block) == 0:
            raise Exception("No such previous Block")
        block = block[0]
        if block[1] != self.Block_Number -1:  #Block numbers not sequential
            raise Exception("Block number is not sequential")
        
