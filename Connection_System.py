import socket
def Connect(remote_ip,PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((remote_ip, PORT))
    print("Connected to > "+ remote_ip+":"+str(PORT))
    return s

class Incoming_Connection_Listener:
    def __init__(self,Port,Thread_Name = "Incoming_Connection listener"):
        self._Thread_Name = Thread_Name
        HOST = ''
        PORT = Port

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(self._Thread_Name,'Socket created')
        self._s.bind((HOST, PORT))
             
        print(self._Thread_Name, 'Socket bind complete')
        self._s.listen(10)
        print(self._Thread_Name, 'Socket now listening')

    def accept(self):
        Incoming_Con, addr = self._s.accept()
        print(self._Thread_Name, ' Connected with' , addr[0] , ':' ,addr[1])
        return Incoming_Con, addr

    def close(self):
        self._s.close()
        print("ICL",self._Thread_Name," closed")
        

#OPort -> Outgoing connection port, IPort -> Incoming connection port.
def Incoming_Connection_Handler(Thread_Name,Command_Queue,Return_Queue,TPort = 8000):
    Exit = False
    ICL = Incoming_Connection_Listener(TPort,"ICH Listener")
    while not Exit:
        try:
            Incoming_Con, addr = ICL.accept()
##            Outgoing_Con = Connect(addr[0],OPort)  #Form the sending connection
##            Return_Queue.put(((addr[0],OPort),Outgoing_Con,Incoming_Con))
            Return_Queue.put(((addr[0],TPort),Incoming_Con))  # Return the connection to the main controller

            #Check for commands from Command_Queue
            if not Command_Queue.empty():
                data = Command_Queue.get()
                Command,Arguments = data[0],data[1]
                if Command == "Exit":
                    Exit = True
                    
        except Exception as e:
            print("Minor Incoming Connection error for ",Thread_Name,":",e)
    ICL.close()



def Outgoing_Connection_Handler(Thread_Name,Command_Queue,Return_Queue,TPort = 8000):
    Exit = False
##    ICL = Incoming_Connection_Listener(IPort,"OCH Listener")
    while not Exit:
        try:
            data = Command_Queue.get()
            Command,Arguments = data[0],data[1]
            if Command == "Exit":
                Exit = True
            elif Command == "Connect":
                print(Arguments)
                Address = Arguments
                if type(Address[1]) == int:
                    CurrentTPort = Address[1]
                else:
                    CurrentTPort = TPort
                Outgoing_Con = Connect(Address[0],CurrentTPort)
##                Incoming_Con,addr = ICL.accept()
##                Return_Queue.put(((addr[0],CurrentOPort),Outgoing_Con,Incoming_Con))
                Return_Queue.put(((addr[0],CurrentTPort),Outgoing_Con))  # Return the connection to the main controller
                

        except Exception as e:
            print("Outgoing connection error for ",Thread_Name,":",e)
    ICL.close()
