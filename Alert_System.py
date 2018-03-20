import Database_System, ecdsa, hashlib,codecs, base64_System

def Alert_User_Verify(db_con,Current_Time,Username,Message,TimeStamp,Signature,Current_Level):
    try:
        if Current_Time -5*60*60 > TimeStamp:
            return False

        User_Details = db_con.Get_Alert_User(Username)[0]
        db_con.Exit()

        Public_Key, Max_Level = User_Details[1],User_Details[3]
        if Current_Level > Max_Level:
            return False

        PuKO = ecdsa.VerifyingKey.from_string(base64_System.b64_to_bstr(Public_Key))
        Raw_Signature = hashlib.sha256((str(Username)+str(Message)+str(TimeStamp)).encode()).digest()
        print(Raw_Signature)
        return PuKO.verify(codecs.decode(Signature.encode(),"base64"),Raw_Signature)
    except Exception as e:
        print("Signature verification failed",e)
        return False

def Sign_Alert(db_con,Username,Message,TimeStamp,Level):
    Alert_User = db_con.Get_Alert_User(Username)
    db_con.Exit()
    if len(Alert_User) == 0:
        return False,"You do not have the private key for this Alert User"
    Private_Key,Max_Level = Alert_User[0][2],Alert_User[0][3]

    if Level > Max_Level:
        return False,"Exceeding max level for this Alert User"
    PrKO = ecdsa.SigningKey.from_string(base64_System.b64_to_bstr(Private_Key))
    Raw_Signature = hashlib.sha256((str(Username)+str(Message)+str(TimeStamp)).encode()).digest()
    Signature = PrKO.sign(Raw_Signature)
    return True,codecs.encode(Signature,"base64").decode()
    
    
    
    
    
    
def Generate_Alert_User(Username = "ALERT",Level = 100):
    DB = Database_System.DBConnection()
    PrKO = ecdsa.SigningKey.generate()
    PuKO = PrKO.get_verifying_key()

    DB.Add_Alert_User(Username,base64_System.str_to_b64(PuKO.to_string()),
                      base64_System.str_to_b64(PrKO.to_string()),Level)
    
    
    
    
