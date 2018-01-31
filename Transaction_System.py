import Database_System,Script_System,json,copy,hashlib

def Create_Transaction(Wallet,Input_Transactions,Output_Transactions,Time):
    #Input_Transactions  <- List of transactions in form {Transaction_Hash,Index}
    #Output_Transactions <- list of transactions in form {Value, Locking Script,LockTime}
    transaction = {
        "in":[],
        "out":Output_Transactions,
        "TimeStamp":Time}

    new_inputs,new_inputs_addresses,funds_available = Obtain_Input_Transactions(Wallet,Input_Transactions,Time)
    if Check_Output_Values(Output_Transactions, funds_available):
        raise Exception("Output values are not valid")
    transaction["in"] = new_inputs
    sigs = []
    raw_sig = hashlib.sha256(json.dumps(transaction,sort_keys = True).encode()).hexdigest()
    for address in new_inputs_addresses:
        public_key = Wallet.Get_Public_Key(address)
        signature = Wallet.Sign(address,raw_sig)
        sig = signature + "  " + raw_sig + "  " + public_key
        sigs.append(sig)
    for x in range(len(sigs)):
        transaction["in"][x]["Sig"] = sigs[x]
    return transaction
        

def Obtain_Input_Transactions(Wallet,Input_Transactions,Time):
    db_con = Database_System.DBConnection()
    new_inputs = []
    new_inputs_addresses = []
    funds_available = 0
    for tx_dict in Input_Transactions:
        new_input = {
            "Prev_Tx":tx_dict["Hash"],
            "Sig":"",
            "Index":tx_dict["Index"]}
        utxo = db_con.Get_Transaction(tx_dict["Hash"],tx_dict["Index"])
        if len(utxo) == 0:
            raise Exception("No such transaction "+tx_dict["Hash"])
        utxo = json.loads(utxo[0][1])
        
        if utxo["LockTime"] > Time:
            raise Exception("Transaction output not yet unlocked")
        tx_script = utxo["ScriptPubKey"]
        new_inputs_addresses.append(Find_Address(Wallet,tx_script))
        new_inputs.append(new_input)
        funds_available += utxo["Value"]
    return new_inputs,new_inputs_addresses,funds_available

            

def Find_Address(Wallet,tx_script):
    Sucess = False
    for address in Wallet.Get_Addresses():
        if address in tx_script:
            Sucess = True
            break
    if Sucess:
        return address
    else:
        raise Exception("You do not own the address for this transaction")

def Check_Output_Value(Output_Transactions,funds_available):
    sum_out = 0
    for transaction in Output_Transactions:
        if transaction["Value"] < 0:
            return False
        sum_out += transaction["Value"]
    return sum_out <= funds_available


        
    
            
        
