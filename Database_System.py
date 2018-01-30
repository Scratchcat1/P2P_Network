import MySQLdb as sql

class DBConnection:
    def __init__(self):
        print("Initializing database connection ")
        self._db_con = sql.connect("localhost","P2P_Network_DB","ll82yq75bv93q","P2P_Network_Database")
        self._cur = self._db_con.cursor()
        self._cur_header = self._db_con.cursor()

    def Exit(self):
        self._db_con.close()

    def Table_Headers(self,TableName):
        self._cur_header.execute("SHOW COLUMNS FROM "+ TableName)  # Cannot use placeholders when referencing the table name , syntax error
        result = self._cur_header.fetchall()
        Headers = []
        for item in result:
            Headers.append(item[0])  #Gets Column header
        return Headers

    ######## Peers  #########
    def Add_Peer(self,IP,Port,Type,Flags,Last_Contact,Last_Ping,Update_If_Need = True):
        self._cur.execute("SELECT 1 FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
        if len(self._cur.fetchall) == 0:
            self._cur.execute("INSERT INTO Peers VALUES(%s,%s,%s,%s,%s,%s)",(IP,Port,Type,Flags,Last_Contact,Last_Ping))
        elif Update_If_Need:
            self._cur.execute("UPDATE Peers SET Type = %s, Flags = %s, Last_Contact = %s, Last_Ping = %s WHERE IP = %s AND Port = %s",(Type,Flags,Last_Contact,Last_Ping,IP,Port))
        self._db_con.commit()

    def Get_Peer(self,IP,Port):
        self._cur.execute("SELECT * FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
        return self._cur.fetchall()

    def Get_Peers(self,Limit = 15):
        self._cur.execute("SELECT * FROM Peers Limit = %s",(Limit,))
        return self._cur.fetchall()

    def Remove_Peer(self,IP,Port):
        self._cur.execute("DELETE FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
        self._db_con.commit()
                

    ###### Alert_Users #######

    def Add_Alert_User(self,Username,Public_Key,Private_Key,Max_Level):
        self._cur.execute("INSERT INTO Alert_Users VALUES(%s,%s,%s,%s)",(Username,Public_Key,Private_Key,Max_Level))
        self._db_con.commit()

    def Remove_Alert_User(self,Username):
        self._cur.execute("DELETE FROM Alert_Users WHERE Username = %s",(Username,))
        self._db_con.commit()

    def Get_Alert_User(self,Username):
        self._cur.execute("SELECT * FROM Alert_Users WHERE Username = %s",(Username,))
        return self._cur.fetchall()

    ##### UTXO #####

    def Add_Transaction(self,Transaction_Hash,Transaction_Text,Index,Output,Block_Hash):
        self._cur.execute("INSERT INTO UTXO VALUES(%s,%s,%s,%s,%s)",(Transaction_Hash,Transaction_Text,Index,Output,Block_Hash))
        self._db_con.commit()

    def Get_Transaction(self,Transaction_Hash):
        self._cur.execute("SELECT * FROM UTXO WHERE Transaction_Hash = %s",(Transaction_Hash,))
        return self._cur.fetchall()

    def Remove_Transaction(self,Transaction_Hash):
        self._cur.execute("DELETE FROM UTXO WHERE Transaction_Hash = %s",(Transaction_Hash,))
        self._db_con.commit()


    ##### Blocks ######

    def Add_Block(self,Block_Hash,Block_Number,Work,Previous_Block_Hash):
        self._cur.execute("SELECT Sum_Work FROM Blocks WHERE Block_Hash = %s",(Previous_Block_Hash,))
        Sum_Work = self._cur.fetchall()
        if len(Sum_Work) == 0:
            Sum_Work = 0
        else:
            Sum_Work = Sum_Work[0][0]
        self._cur.execute("INSERT INTO Blocks VALUES(%s,%s,%s,%s,%s)",(Block_Hash,Block_Number,Work,Sum_Work+Work,Previous_Block_Hash))
        self._db_con.commit()

    def Remove_Block(self,Block_Hash):
        self._cur.execute("DELETE FROM Blocks WHERE Block_Hash = %s",(Block_Hash,))
        self._db_con.commit()

    def Get_Block(self,Block_Hash):
        self._cur.execute("SELECT * FROM Blocks WHERE Block_Hash = %s",(Block_Hash,))
        return self._cur.fetchall()

    def Count_Previous_Block_Neighbours(self,Previous_Block_Hash):
        self._cur.execute("SELECT COUNT(*) FROM Blocks WHERE Previous_Block_Hash = %s",(Previous_Block_Hash,))
        return self._cur.fetchall()

    def Get_Highest_Work_Block(self):
        self._cur.execute("SELECT MAX(Sum_Work) FROM Blocks")
        Sum_Work = self._cur.fetchall()[0][0]
        self._cur.execute("SELECT * FROM Blocks WHERE Sum_Work = %s ORDER BY Block_Number DESC",(Sum_Work,))
        return self._cur.fetchall()
    

##    ##### Leaf Blocks  ######
##
##    def Get_Highest_Leaf_Block_Hash(self):
##        self._cur.execute("SELECT MAX(Block_Hash) FROM Leaf_Blocks")
##        result = self._cur.fetchall()[0][0]
##        if result == None:
##            result = ""
##        return result
##
##    def Add_Leaf_Block(self,Block_Hash,Block_Number,Sum_Work, Previous_Block_Hash):
##        self._cur.execute("SELECT * FROM Leaf_Blocks WHERE Block_Hash = %s",(Previous_Block_Hash,))
        
        












    def ResetDatabase(self):
        self._cur.execute("SET FOREIGN_KEY_CHECKS = 0")  #Otherwise dropping tables will raise errors.
        TABLES = ["Blocks","Leaf_Blocks","UTXO","Peers","Alert_Users"]
        for item in TABLES:  # Drops all tables
            self._cur.execute("DROP TABLE IF EXISTS {0}".format(item))
        
        self._cur.execute("CREATE TABLE Blocks(Block_Hash VARCHAR(32) PRIMARY KEY, Block_Number INT, Work INT, Sum_Work INT, Previous_Block_Hash VARCHAR(32))")
        #self._cur.execute("CREATE TABLE Leaf_Blocks(Block_Hash VARCHAR(32) PRIMARY KEY, Block_Number INT, Sum_Work INT)")
        self._cur.execute("CREATE TABLE UTXO(Transaction_Hash VARCHAR(32) PRIMARY KEY, Transaction TEXT, Transaction_Index INT, Output INT, Block_Hash VARCHAR(32))")
        self._cur.execute("CREATE TABLE Peers(IP VARCHAR(15) ,Port INT, Type TEXT, Flags TEXT, Last_Contact INT, Last_Ping INT, PRIMARY KEY(IP,Port))")
        self._cur.execute("CREATE TABLE Alert_Users(Username VARCHAR(16) PRIMARY KEY, Public_Key VARCHAR(200), Private_Key VARCHAR(200), Max_Level INT)")
        
        self._cur.execute("SET FOREIGN_KEY_CHECKS = 1")  # Reenables checks
        self._db_con.commit()
