import Database_System, ecdsa, hashlib,codecs

def Alert_User_Verify(Current_Time,Username,Message,TimeStamp,Signature,Current_Level):
    try:
        if Current_Time -5*60*60 > TimeStamp:
            return False

        db_con = Database_System.DBConnection()
        User_Details = db_con.Get_Alert_User(Username)[0]
        db_con.Exit()

        Public_Key, Max_Level = User_Details[1],User_Details[3]
        if Current_Level > Max_Level:
            return False

        PuKO = ecdsa.VerifyingKey.from_pem(Public_Key)
        Raw_Signature = hashlib.sha256((str(Username)+str(Message)+str(TimeStamp)).encode()).digest()
        print(Raw_Signature)
        return PuKO.verify(codecs.decode(Signature.encode(),"base64"),Raw_Signature)
    except Exception as e:
        print("Signature verification failed",e)
        return False

def Sign_Alert(Username,Message,TimeStamp,Level):
    db_con = Database_System.DBConnection()
    Alert_User = db_con.Get_Alert_User(Username)
    db_con.Exit()
    if len(Alert_User) == 0:
        raise Exception("You do not have the private key for this Alert User")
    Private_Key,Max_Level = Alert_User[0][2],Alert_User[0][3]

    if Level > Max_Level:
        raise Exception("Exceeding max level for this Alert User")
    PrKO = ecdsa.SigningKey.from_pem(Private_Key)
    Raw_Signature = hashlib.sha256((str(Username)+str(Message)+str(TimeStamp)).encode()).digest()
    Signature = PrKO.sign(Raw_Signature)
    return codecs.encode(Signature,"base64").decode()
    
    
    
    
    
    
