import json,ecdsa,hashlib,codecs,base64_System
import autorepr

class Wallet(autorepr.Base):
    def __init__(self,wallet_file = "wallet.json"):
        self.logger_setup(__name__)
        self._wallet_file = wallet_file
        self._wallet = {}

    def load_wallet(self,wallet_file = None):
        if wallet_file:
            self._wallet_file = wallet_file 
        with open(self._wallet_file) as file:
            self._wallet = json.load(file)
        self._logger.info("Loaded wallet with ",len(self._wallet),"Addresses")

    def save_wallet(self):
        with open(self._wallet_file,"w") as file:
            json.dump(self._wallet,file)


    def generate_new_address(self):
        PrKO = ecdsa.SigningKey.generate()
        PuKO = PrKO.get_verifying_key()
        address = self.to_address(base64_System.str_to_b64(PuKO.to_string(),True))
##        print(Address)
##        print(PrKO.to_pem().decode())
        self._wallet[address] = {
            "Private_Key":base64_System.str_to_b64(PrKO.to_string()),
            "Public_Key":base64_System.str_to_b64(PuKO.to_string()),
            }
        return address

    def sign(self,address,message):
##        message_hash = hashlib.sha256(str(message).encode()).digest()
        PrKO = ecdsa.SigningKey.from_string(base64_System.b64_to_bstr(self._wallet[address]["Private_Key"]))
        signature = base64_System.str_to_b64(PrKO.sign(message.encode()))
        self._logger.debug("Wallet with address %s obtained signature %s from message %s" % (address,signature,message))
        return signature

    def get_public_key(self,address):
        return self._wallet[address]["Public_Key"]

    def get_addresses(self):
        return self._wallet.keys()

    def has_address(self,address):
        return address in self._wallet

    def to_address(self,value):
        if type(value) != bytes:
            value = value.encode()
        return hashlib.sha256(value).hexdigest()


    def __str__(self):
        data = [
            ("Wallet file",self._wallet_file),
            ("Number of addresses",len(self._wallet)),
            ]
        return autorepr.str_repr(self,data)

    
    
    

    

    
        
