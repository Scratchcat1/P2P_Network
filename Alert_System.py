import Database_System, ecdsa, hashlib

def Alert_User_Verify(Current_Time,Username,Message,TimeStamp,Signature,Level,Current_Level):
    if Current_Time -5*60*60 > TimeStamp:
        return False
    if Current_Level > Level:
        return False

    User_Details = Database_System.Get_Alert_User(Username)
    Public_Key, Max_Level = User_Details[1],User_Details[2]
    if Current_Level > Max_Level:
        return False
    
    PuKO = ecdsa.VerifyingKey.from_string(Public_Key)
    Raw_Signature = str(Username)+str(Message)+str(TimeStamp)
    return PuKO.verify(Signature,hashlib.sha256(Raw_Signature))

def Sign_Alert(Current_Time,Username,Message,Level):
    pass
    
    
    
    
