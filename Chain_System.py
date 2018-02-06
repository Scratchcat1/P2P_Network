import Database_System,Block_System,json,os

class Chain:
    def __init__(self):
        self._db_con = Database_System.DBConnection()
        try:
            self._highest_block_hash = self.get_highest_block_hash()
        except:
            self._highest_block_hash = ""

    def get_block_json(self,block_hash):
        with open(os.path.join("blocks","block_"+block_hash)) as file_handle:
            block_json = file_handle.read()
        return block_json

    def get_block(self,block_hash):
        block_dict = json.loads(self.get_block_json(block_hash))
        block = Block_System.Block()
        block.Import(block_dict)
        return block

    def add_block_json(self,block_hash,block_json):
        with open(os.path.join("blocks","block_"+block_hash),"w") as file_handle:
            file_handle.write(block_json)

    def add_block(self,block):
        self._db_con.Add_Block(block.Get_Block_Hash(),block.Get_Block_Number(),block.Get_Difficulty(),block.Get_Prev_Block_Hash(),block.Get_TimeStamp()) #Add block to db
        self.add_block_json(block.Get_Block_Hash(),json.dumps(block.Export()))   #Save block
        if self.check_for_rebase(block.Get_Block_Hash(),block.Get_Prev_Block_Hash()):
            self.rebase_chain(block.Get_Block_Hash())
            self._highest_block_hash = block.Get_Block_Hash()  #This block has become the new highest block hash

        if block.Get_Block_Hash() == self._highest_block_hash:  # Only if this block extends the valid chain is the UTXO modified
            rollback_data = block.Update_UTXO()
            self.add_block_rollback(block.Get_Block_Hash(),rollback_data)
        

    def get_block_rollback(self,block_hash):
        with open(os.path.join("blocks","rollback_"+block_hash)) as file_handle:
            rollback_json = file_handle.read()
        return json.loads(rollback_json)

    def add_block_rollback(self,block_hash,rollback_data):
        with open(os.path.join("blocks","rollback_"+block_hash),"w") as file_handle:
            file_handle.write(json.dumps(rollback_data))
        

    #############################################
        
    def get_highest_block_hash(self):
        return self._db_con.Get_Highest_Work_Block()[0][0]

    def check_for_rebase(self,new_block_hash,new_block_hash_prev):
        if self._highest_block_hash == self.get_highest_block_hash(): # added to smaller chain so no height increase
            return False
        elif self._highest_block_hash == new_block_hash_prev: # new block added on top of old highest block, new highest block hash
            self._highest_block_hash = new_block_hash
            return False
        else:
            print("rebasing")
            return True  # new chain has overtaken old best chain so rebase needed

    def rebase_chain(self,new_block_hash):
        common_root = self.establish_common_root_block(self._highest_block_hash,new_block_hash)
        current_hash = self._highest_block_hash  #old highest block hash will be rolled back

        while current_hash != common_root:  #While it has not rolled back to common root node
            block = self.get_block(current_hash)
            block.Rollback_UTXO(self.get_block_rollback(current_hash))  #readd any UTXOs and remove new outputs
            current_hash = self._db_con.Get_Block(current_hash)[0][4] # Move to parent block

        for current_hash in self.find_path_to_block(new_block_hash,common_root)[::-1]: # for new chain ( method returns new->old) add in utxos
            block = self.get_block(current_hash)
            rollback_data = block.Update_UTXO()             #Adds in the UTXOs of the ancestors of the new highest block
            self.add_block_rollback(block.Get_Block_Hash(),rollback_data)
            
            

    def establish_common_root_block(self,hash_a, hash_b):
        hash_a_set = set()
        hash_b_set = set()
        while len(hash_a_set.intersection(hash_b_set)) == 0:
            hash_a,hash_a_set = parent_set_add(self._db_con,hash_a,hash_a_set)
            hash_b,hash_b_set = parent_set_add(self._db_con,hash_b,hash_b_set)

        return list(hash_a_set.intersection(hash_b_set))[0] # common root

    def find_path_to_block(self,current_block_hash,target_block_hash):
        path = []
        while current_block_hash != target_block_hash:
            current_block_hash = self._db_con.Get_Block(current_block_hash)[0][4]
            path.append(current_block_hash)
        return path[:-1]  #This removes the target_block_hash from the list
            
            
def parent_set_add(db_con,hash_item,hash_set):
    hash_item = db_con.Get_Block(hash_item)
    if len(hash_item) > 0:
        hash_item = hash_item[0][4] #prev block hash
        hash_set.add(hash_item)
    return hash_item,hash_set
    
def Generate_Genesis_Block():
    w,t,b = Block_System.test()
    b._db_con.ResetDatabase()
    print(b.Get_Block_Hash())
    c = Chain()
    c.add_block(b)


def sim():
    Generate_Genesis_Block()
    c = Chain()
    b = c.get_block("c18cd9812ae9fce4c9948f66629e4b0b1e89ed56ea1fc4d26cc0091723f55e16")
    for n in range(1,5):
        w,t,b = Block_System.test(bn= n, tim = n,pblk = b.Get_Block_Hash())
        c.add_block(b)

    print("")
    print("Generating side chain")
    
    b = c.get_block("c18cd9812ae9fce4c9948f66629e4b0b1e89ed56ea1fc4d26cc0091723f55e16")
    for n in range(1,6):
        w,t,b = Block_System.test(bn= n, tim = n+100,pblk = b.Get_Block_Hash())
        c.add_block(b)
    return c

    
