import Database_System,Block_System,json

class Chain:
    def __init__(self):
        self._db_con = Database_System.DBConnection()
        self._highest_block_hash = self.get_highest_block_hash()

    def get_block_json(self,block_hash):
        with open(block_hash) as file_handle:
            block_json = file_handle.read()
        return block_json

    def get_block(self,block_hash):
        block_dict = json.loads(self.get_block_json(block_hash))
        block = Block_System.Block()
        block.Import(block_dict)
        return block

    def add_block_json(self,block_hash,block_json):
        with open(block_hash,"w") as file_handle:
            file_handle.write(block_json)

    def add_block(self,block):
        self._db_con.Add_Block(block.Get_Block_Hash(),block.Get_Block_Number(),block.Get_Difficulty(),block.Get_Prev_Block_Hash(),block.Get_TimeStamp())
        self.add_block_json(block.Get_Block_Hash(),json.dumps(block.Export()))
        
        if self.check_for_rebase(block.Get_Prev_Block_Hash()):
            self.rebase_chain()
        
    def get_highest_block_hash(self):
        return self._db_con.Get_Highest_Work_Block()[0][0]

    def check_for_rebase(self,new_block_hash_prev):
        if self._highest_block_hash == self.get_highest_block_hash(): # added to smaller chain so no height increase
            return False
        elif self._highest_block_hash == new_block_hash_prev: # new block added on top of old highest block, new highest block hash
            self._highest_block_hash = new_block_hash_prev
            return False
        else:
            return True  # new chain has overtaken old best chain so rebase needed

    def rebase_chain(self):
        common_root = self.establish_common_root_block(self._highest_block_hash)
        

    def establish_common_root_block(self,hash_a, hash_b):
        hash_a_set = set()
        hash_b_set = set()
        while len(hash_a_set.intersection(hash_b_set)) == 0:
            hash_a = self._db_con.Get_Block(hash_a)[4] #prev block hash
            hash_b = self._db_con.Get_Block(hash_b)[4] #prev block hash
        return hash_a_set.intersection(hash_b_set) # common root
            
            

    
        
