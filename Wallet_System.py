import json,ecdsa,hashlib

class Wallet:
    def __init__(self,wallet_file = "wallet.json"):
        self._Wallet_File = wallet_file
        self._Wallet = {}

    def Load_Wallet(self):
        with open(self._Wallet_File) as file:
            self._Wallet = json.load(file)
        print("Loaded wallet with ",len(self._Wallet),"Addresses")

    def Save_Wallet(self):
        with open(self._Wallet_File,"w") as file:
            json.dump(self._Wallet,file)

    def Generate_New_Address(self):
        PrKO = ecdsa.SigningKey.generate()
        PuKO = PrKO.get_verifying_key()
        Address = hashlib.sha256(PuKO.to_string()).hexdigest()
        self._Wallet[Address] = {
            "Private_Key":PrKO.to_pem().decode(),
            "Public_Key":PuKO.to_pem().decode(),
            }
        return Address

    def Get_Addresses(self):
        return self._Wallet.keys()

    def Sign(self,Address,Message):
        message_hash = hashlib.sha256(str(Message).encode()).digest()
        PrKO = ecdsa.SigningKey.from_pem(self._Wallet[Address]["Private_Key"])
        signature = PrKO.sign(message_hash)
        return signature
    

    

    
        
