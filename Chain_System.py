import Database_System,Block_System,json,os

class Chain:
    def __init__(self,Mempool):
        self._db_con = Database_System.DBConnection()
        self._Mempool = Mempool  #Contains a reference to the Mempool object
        self._difficulty = self.find_difficulty()
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
            rollback_data = block.Update_UTXO(self._Mempool)
            self._db_con.Set_Block_On_Best_Chain(block.Get_Block_Hash(),1)  #Mark this block as part of the best chain
            self.add_block_rollback(block.Get_Block_Hash(),rollback_data)
            if block.Get_Block_Number() % 2016 == 0:
                self._difficulty = self.find_difficulty()
                
        

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

    def has_block(self,block_hash):  #To tell if one has the block or not
        return len(self._db_con.Get_Block(block_hash)) != 0  # If not 0 then has block

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
            block.Rollback_UTXO(self.get_block_rollback(current_hash),self._Mempool)  #readd any UTXOs and remove new outputs, readds transactions to mempool
            self._db_con.Set_Block_On_Best_Chain(block.Get_Block_Hash(),0)            #Mark this block as not on the best chain any longer
            current_hash = self._db_con.Get_Block(current_hash)[0][4]                  # Move to parent block

        for current_hash in self.find_path_to_block(new_block_hash,common_root)[::-1]: # for new chain ( method returns new->old) add in utxos
            block = self.get_block(current_hash)
            rollback_data = block.Update_UTXO(self._Mempool)                             #Adds in the UTXOs of the ancestors of the new highest block, remove from mempool
            self._db_con.Set_Block_On_Best_Chain(block.Get_Block_Hash(),1)             # Mark this block as now on the best chain.
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

    ###################################################

    def get_difficulty(self):
        return self._difficulty

    def find_difficulty(self):
        blocks = []
        current_hash = self.get_highest_block_hash()

        block_number = 1  
        while block_number % 2016 != 0: # Cycles until a section of 2016 blocks could be found, aligns on boundary ?
            block_info = self._db_con.Get_Block(current_hash)
            if len(block_info) == 0:
                break  # No more blocks found to cancel
            block_number = block_info[0][1]
            current_hash = block_info[0][4]  # next hash
            
        for x in range(2016):   #Attempts to get 2016 blocks
            block_info = self._db_con.Get_Block(current_hash)
            if len(block_info) == 0:
                break  # No more blocks found to cancel
            blocks.append(block_info[0])
            current_hash = block_info[0][4]  # next hash

        sum_diff = 0
        for block_info in blocks:
            sum_diff += block_info[2]
        print( blocks[0][5],blocks[-1][5])
        if len(blocks) > 0 and blocks[0][5] != blocks[-1][5]:
            diff = (2*7*24*3600)/(max(blocks[0][5],blocks[-1][5])-min(blocks[0][5],blocks[-1][5])) * sum_diff/len(blocks)   # TargetTime/actualTime * current difficulty, if T < a difficulty is reduced
        else:
            print("Using default difficulty")
            diff = 2**256 - 2**250  #if error then reset difficulty to default. Diff is 2**256 - Target which it must be below

        return diff
            
            
            
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

    
