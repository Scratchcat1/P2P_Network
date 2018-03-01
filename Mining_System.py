import Block_System,Threading_System,queue,time,multiprocessing

class Miner:
    def __init__(self,mempool,coinbase_tx, num_proc = 3):
        self._mempool = mempool             #Mempool can be added later
        self._coinbase_tx = coinbase_tx     #Stores the target coinbase_tx
        self._num_proc = num_proc
        THREAD_MODE = "Create_Process"
    
        self._TC_queue = Threading_System.Create_Controller()
        self._json_queue = queue.Queue() if THREAD_MODE == "Create_Thread" else multiprocessing.Queue()

        for i in range(num_proc):
            self._TC_queue.put(("Controller",THREAD_MODE,(i,Miner_Worker,(self._num_proc,self._json_queue,))))

    ##############################################################

    def set_mempool(self,mempool):
        self._mempool = mempool

    def set_coinbase_tx(self,ctx):
        self._coinbase_tx = ctx


    ##############################################################


    def restart_mine(self,Time,difficulty,block_number,parent_block_hash):
        transactions = self._mempool.get_txs()          #Obtain the txs to include
        block = Block_System.Block(difficulty,block_number,parent_block_hash)
        block.Set_TimeStamp(Time)                       #Set the correct timestamps
        self._coinbase_tx.Set_TimeStamp(Time)
        block.Add_Transaction(self._coinbase_tx)        #Add the coinbase transaction
        for tx in transactions:
            block.Add_Transaction(tx)

        block.Set_Merkle_Root(block.Calculate_Merkle_Root())
        self.mine_block_json(block.export_json())
        

    def halt(self):
        for i in range(self._num_proc):
            self._TC_queue.put((i,"Halt",()))           #Pause all mining
    

    def mine_block_json(self,block_json):
        for i in range(self._num_proc):
            self._TC_queue.put((i,"Mine",(block_json,)))    #Mine this block json

    def has_found_block(self):
        return not self._json_queue.empty()             #Detects if mining complete.

    def get_block(self):
        block_json = self._json_queue.get()
        while not self._json_queue.empty():
            _= self._json_queue.get()       #Empty queue to avoid more solutions backing up

        
        block = Block_System.Block()
        block.import_json(block_json)
        self._current_block = None
        return block

    ####################################################
    def close(self):
        self._TC_queue.put(("Controller","Exit",()))












def Miner_Worker(Thread_Name,Thread_Queue,num_proc,json_queue):
    """
    Commands in form (command,(arg1,arg2...))
    (Exit,()) -> Exit
    (Halt,()) -> Halt mining
    (Mine,()) -> Mine this header
    """
    Exit = False
    current_json = None
    block = Block_System.Block()
    while not Exit:
        try:
            while not Thread_Queue.empty():
                Command,Args = Thread_Queue.get()
                if Command == "Exit":
                    Exit = True
                    current_json = None
                    break
                elif Command == "Halt":
                    current_json = None

                elif Command == "Mine":
                    block.import_json(Args[0])
##                    print("MINER",block.Get_Prev_Block_Hash())
                    block.Set_TimeStamp(block.Get_TimeStamp()+Thread_Name)  #Staggers the timestamps over the range of the procs so no duplicate work is done
                    current_json = block.export_json()
                    
            if current_json is not None:
                block.import_json(current_json)
                block_hash = block.Mine()
                if block_hash:
                    json_queue.put(block.export_json())
                    current_json = None
                else:
                    block.Set_TimeStamp(block.Get_TimeStamp()+num_proc)
                    current_json = block.export_json()
            else:
                time.sleep(0.1)

        except Exception as e:
            print("Exception in Miner_Worker",Thread_Name,"Error",e)
            time.sleep(0.1)
                
                    
