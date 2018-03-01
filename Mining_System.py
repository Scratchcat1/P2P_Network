import Block_System,Threading_System,queue,time

class Miner:
    def __init__(self,mempool, num_proc = 3):
        self._mempool = mempool
        self._num_proc = num_proc

        self._TC_queue = Threading_System.Create_Controller()
        self._hash_queue = queue.Queue()

        for i in range(num_proc):
            self._TC_queue.put(("Controller","Create_Process",(i,Miner_Worker,(self._num_proc,self._hash_queue,))))










    def close(self):
        self._TC_queue.put(("Controller","Exit",()))

    def start_mine(self,block_json):
        for i in range(self._num_proc):
            self._TC_queue.put((i,"Mine",(block_json,)))

    def halt(self):
        for i in range(self._num_proc):
            self._TC_queue.put((i,"Halt",()))

    def has_block_hash(self):
        return not self._hash_queue.empty()

    def get_block_hash(self):
        block_hash = self._hash_queue.get()
        while not self._hash_queue.empty():
            _= self._hash_queue.get()       #Empty queue to avoid more solutions backing up
        return block_hash











def Miner_Worker(Thread_Name,Thread_Queue,num_proc,hash_queue):
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
                    block.Set_TimeStamp(block.Get_TimeStamp()+Thread_Name)  #Staggers the timestamps over the range of the procs so no duplicate work is done
                    current_json = block.export_json()
                    
            if current_json is not None:
                block.import_json(current_json)
                block_hash = block.Mine()
                if block_hash:
                    hash_queue.put(block_hash)
                    current_json = None
                else:
                    block.Set_TimeStamp(block.Get_TimeStamp()+num_proc)
                    current_json = block.export_json()
            else:
                time.sleep(0.1)

        except Exception as e:
            print("Exception in Miner_Worker",Thread_Name,"Error",e)
            time.sleep(0.1)
                
                    

