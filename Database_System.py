import MySQLdb as sql

class DBConnection:
    def __init__(self):
        print("Initializing database connection ")
        self._db_con = sql.connect("localhost","P2P_Network","password","P2P_Database")
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
    def Add_Peer(self,IP,Port,Type,Flags,Last_Contact,Last_Ping):
        self._cur.execute("SELECT 1 FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
        if len(self._cur.fetchall) == 0:
            self._cur.execute("INSERT INTO Peers VALUES(%s,%s,%s,%s,%s,%s)",(IP,Port,Type,Flags,Last_Contact,Last_Ping))
        else:
            self._cur.execute("UPDATE Peers SET Type = %s, Flags = %s, Last_Contact = %s, Last_Ping = %s WHERE IP = %s AND Port = %s",(Type,Flags,Last_Contact,Last_Ping,IP,Port))

    def Get_Peer(self,IP,Port):
        self._cur.execute("SELECT * FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
        return self._cur.fetchall()

    def Get_Peers(self,Limit = 15):
        self._cur.execute("SELECT * FROM Peers Limit = %s",(Limit,))
        return self._cur.fetchall()

    def Remove_Peer(self,IP,Port):
        self._cur.execute("DELETE FROM Peers WHERE IP = %s AND Port = %s",(IP,Port))
                

    ###### Alert_Users #######

    def Add_Alert_User(self,Username,Public_Key,Max_Level):
        self._cur.execute("INSERT INTO Alert_Users VALUES(%s,%s,%s)",(Username,Public_Key,Max_Level))

    def Remove_Alert_User(self,Username):
        self._cur.execute("DELETE FROM Alert_Users WHERE = %s",(Username,))

    def Get_Alert_User(self,Username):
        self._cur.execute("SELECT * FROM Alert_Users WHERE = %s",(Username,))
        return self._cur.fetchall()













    def ResetDatabase(self):
        self._cur.execute("SET FOREIGN_KEY_CHECKS = 0")  #Otherwise dropping tables will raise errors.
        TABLES = []
        for item in TABLES:  # Drops all tables
            self._cur.execute("DROP TABLE IF EXISTS {0}".format(item))
        
        self._cur.execute("CREATE TABLE Blocks(Block_Hash TEXT PRIMARY KEY, Block_Number INT, Work INT, Previous_Block_Hash TEXT)")
        self._cur.execute("CREATE TABLE Leaf_Blocks(Block_Hash TEXT PRIMARY KEY, Block_Number INT, Sum_Work INT)")
        self._cur.execute("CREATE TABLE UTXO(Transaction_Hash TEXT PRIMARY KEY, Index INT, Output INT, Block_Hash TEXT)")
        self._cur.execute("CREATE TABLE Peers(IP TEXT ,Port INT, Type TEXT, Flags TEXT, Last_Contact INT, Last_Ping INT, PRIMARY KEY(IP,Port))")
        self._cur.execute("CREATE TABLE Alert_Users(Username TEXT PRIMARY KEY, Public_Key TEXT, Max_Level INT)")
        
        self._cur.execute("SET FOREIGN_KEY_CHECKS = 1")  # Reenables checks
        self._db_con.commit()
