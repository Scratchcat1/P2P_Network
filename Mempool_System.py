import Transaction_System

class Mempool:
    def __init__(self,max_size = 100000, min_fee = 0):
        self._max_size = max_size
        self._min_fee = min_fee
        self._contents = {}  #Tx_hash,tx_json

    def flush(self):  #Remove all items
        self._contents = {}
    def get_size(self):
        return len(self._contents)
    def purge(self):  #Removes all items below min_fee
        temp_contents = self._contents.copy()
        self.flush()
        for tx_hash,tx_json in temp_contents.items():
            tx = Tranaction_System.Transaction()
            tx.Import(tx_json)
            if tx.Get_Fee() >= self._min_fee:
                self._contents[tx_hash] = tx_json

    def get_txs(self,num = 100):  #returns top 100 fee transactions
        tx_fees = {}
        for tx_hash,tx_json in self._contents.items():
            tx = Tranaction_System.Transaction()
            tx.Import(tx_json)
            tx_fees[tx_hash] = tx.Get_Fee()
            
        tx_hashes = sorted(self._contents,key = lambda x:tx_fees[x])
        txs = []
        for item in tx_hashes:
            tx = Tranaction_System.Transaction()
            tx.Import(self._contents[item])
            txs.append(tx)
        return txs
            
        
    

    def get_min_fee(self):
        return self._min_fee
    def set_min_fee(self,min_fee):
        self._min_fee = min_fee
        
    def has_tx(self,tx_hash):
        return tx_hash in self._contents
    def remove_tx(self,tx_hash):
        self._contents.pop(tx_hash,None)
    def add_transaction_json(self,tx_hash,tx_json,tx_fee):
        if tx_fee >= self._min_fee and len(self._contents) <= self._max_size:
            self._contents[tx_hash] = tx_json
            return True
        else:
            return False

    
            
            
        
        
