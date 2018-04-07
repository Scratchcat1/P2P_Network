import Database_System,Block_System,json,os,Mempool_System, autorepr, hashlib

class Chain(autorepr.AutoRepr):
    def __init__(self,Mempool):
        self._db_con = Database_System.DBConnection()
        self._Mempool = Mempool  #Contains a reference to the Mempool object
        try:
            self._highest_block_hash = self.get_highest_block_hash()
            self._difficulty = self.find_difficulty()
        except Exception as e:
            print("Error creating chain, may occur on first run without genesis block! Using default attributes. Error:",e)
            self._highest_block_hash = ""
            self._difficulty = 1

    ############################################

    def get_block_json(self,block_hash):
        with get_container_file_object(self._db_con,"block",block_hash) as file_handle:
            block_container = json.loads(file_handle.read())
            block_json = block_container[block_hash]
        return block_json

    def get_block(self,block_hash):
        block_dict = json.loads(self.get_block_json(block_hash))
        block = Block_System.Block()
        block.Import(block_dict)
        return block

    def add_block_json(self,block_hash,block_json):
        with get_container_file_object(self._db_con,"block",block_hash) as file_handle:
            block_container = json.loads(file_handle.read())
        block_container[block_hash] = block_json
        with get_container_file_object(self._db_con,"block",block_hash,mode = "w") as file_handle:
            file_handle.write(block_container)
            
        

    def get_block_rollback_json(self,block_hash):
        with get_container_file_object(self._db_con,"rollback",block_hash) as file_handle:
            rollback_container = json.loads(file_handle.read())
        return json.loads(rollback_container[block_hash])

    def add_block_rollback(self,block_hash,rollback_data):
        with get_container_file_object(self._db_con,"rollback",block_hash) as file_handle:
            rollback_container = json.loads(file_handle.read())
        rollback_container[block_hash] = json.dumps(rollback_data)
        with get_container_file_object(self._db_con,"rollback",block_hash,mode = "w") as file_handle:
            file_handle.write(rollback_container)

            
        with open(os.path.join("blocks","rollback_"+block_hash),"w") as file_handle:
            file_handle.write(json.dumps(rollback_data))






    #############################################
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
            return True  # new chain has overtaken old best chain so rebase needed

    def rebase_chain(self,new_block_hash):
        print("Alternate chain is now longest chain. Rebasing the chain...")
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
        RETARGET_LENGTH = 1000
        current_hash = self.get_highest_block_hash()

        current_block_number = self.Get_Block(current_hash)[0][1]
        start_block_number = ((current_block_number//RETARGET_LENGTH)-2)*RETARGET_LENGTH    #Find the starting block number - shift down RETARGET_LENGTH lengths, then again as the Chain section will move up RETARGET_LENGTH values
        blocks = Database_System.Find_Best_Chain_Section( Database_System.Get_Best_Chain_Block(start_block_number)) #Obtains the list of blocks for the last section of RETARGET_LENGTH blocks

        sum_diff = 0
        for block_info in blocks:
            sum_diff += int(block_info[2])  #Find the sum of the difficulty
            
##        print( blocks[0][5],blocks[-1][5])
        if len(blocks) > 0 and blocks[0][5] != blocks[-1][5]:
            diff = (2*7*24*3600)/(max(blocks[0][5],blocks[-1][5])-min(blocks[0][5],blocks[-1][5])) * sum_diff/len(blocks)   # TargetTime/actualTime * current difficulty, if T < a difficulty is reduced
        else:
            print("Using default difficulty")
            diff = 2**256 - 2**237          #if error then reset difficulty to default. Diff is 2**256 - Target which it must be below

        return diff

    def __str__(self):
        data = [
            ("Highest Block Hash",self._highest_block_hash),
            ("Difficulty",self._difficulty)]
        return autorepr.str_repr(self,data)




            
            
            
def parent_set_add(db_con,hash_item,hash_set):
    hash_item = db_con.Get_Block(hash_item)
    if len(hash_item) > 0:
        hash_item = hash_item[0][4] #prev block hash
        hash_set.add(hash_item)
    return hash_item,hash_set


def get_container_file_object(db_con, target, block_hash, block_container_size = 1000, mode = "r"):
    # target sets if the rollback or block file should be selected
    block_number = db_con.Get_Block(block_hash)[0][1]
    filename = os.path.join("blocks",target+"_"+str(block_number//block_container_size))
    if not os.path.exists(filename):
        with open(filename,"w") as file_handle:
            file_handle.write("{}")             #Create an empty dictionary in the file
    return open(filename,mode)






class HashTableIO:
    """
    An object to abstract storing dictionary values across multiple files
    block_key_function is used to derive the key for the file to be opened. Form -> lambda key,kwargs: ~process function~. Must return a string to be used as the filename.
    key for each component in the dictionary in a file is in the form "target_type_keya_keyb_keyc"...
    """
    def __init__(self,block_key_function = lambda key,kwargs:str(int(hashlib.sha256(key.encode()).hexdigest(),16)%kwargs.get("divisor",1000))):
        self._block_key_function = block_key_function

    def set_block_key_function(self,block_key_function):
        self._block_key_function = block_key_function

    def read(self,key,path = ("blocks",),**kwargs):
        block_key = self._block_key_function(self._merge_key(key),kwargs)               #Derive the block key
        filepath = os.path.join(*path,self._merge_key(("subsection",block_key)))        #Determine the filepath -> merge path + filename ( subsection_block_key)
        
        with open(filepath,"r") as file_handle:                                         #Open the file
            container_json = json.loads(file_handle.read())                             #Load the contents using json
        return container_json[self._merge_key(key)]                                     #Return the contents of the key used
    
        
    def write(self,key,data,path = ("blocks",),**kwargs):
        block_key = self._block_key_function(self._merge_key(key),kwargs)               #Derive the block key
        filepath = os.path.join(*path,self._merge_key(("subsection",block_key)))        #Determine the filepath -> merge path + filename ( subsection_block_key)
        
        if os.path.exists(filepath):
            with open(filepath,"r") as file_handle:                                     #Should the file exist then load the dictionary from it
                file_data = json.loads(file_handle.read())
        else:
            file_data = {}                                                              #If the file does not exist assume the contents were an empty dictionary
        file_data[self._merge_key(key)] = data
        
        with open(filepath,"w") as file_handle:
            file_handle.write(json.dumps(file_data))
            
                

    def _merge_key(self,key,merge_on = "_"):
        return merge_on.join([str(item) for item in key])





def Generate_Genesis_Block():
    db_con = Database_System.DBConnection()
    db_con.ResetDatabase()
    w,t,block = Block_System.test()

    print(block.Get_Block_Hash())
    c = Chain(Mempool_System.Mempool())

    #Add genesis block to db and save file
    c._db_con.Add_Block(block.Get_Block_Hash(),block.Get_Block_Number(),block.Get_Difficulty(),block.Get_Prev_Block_Hash(),block.Get_TimeStamp()) #Add block to db
    c.add_block_json(block.Get_Block_Hash(),json.dumps(block.Export()))   #Save block

    #No rebase as first block
    #No need to check if top block as it is only block
    rollback_data = block.Update_UTXO(c._Mempool)
    c._db_con.Set_Block_On_Best_Chain(block.Get_Block_Hash(),1)  #Mark this block as part of the best chain
    c.add_block_rollback(block.Get_Block_Hash(),rollback_data)
    db_con.Exit()
    print("GENERATED GENESIS BLOCK\n")



def sim():
    Generate_Genesis_Block()
    c = Chain(Mempool_System.Mempool())
    GENESIS_BLOCK_HASH = c.get_highest_block_hash()
    b = c.get_block(GENESIS_BLOCK_HASH)
    for n in range(1,5):
        w,t,b = Block_System.test(bn= n, tim = n,pblk = b.Get_Block_Hash(),dif = c.get_difficulty())
        c.add_block(b)
        print("")

    print("")
    print("Generating side chain")
    
    b = c.get_block(GENESIS_BLOCK_HASH)
    for n in range(1,3000):
        if n% 100 == 0:
            print("\n"*5,"Block",n,"\n")
        w,t,b = Block_System.test(bn= n, tim = n+100,pblk = b.Get_Block_Hash(),dif = c.get_difficulty())
        c.add_block(b)
    return c

    
