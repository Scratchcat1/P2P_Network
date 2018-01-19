import threading,multiprocessing,queue,time

class Thread_Handle:
    def __init__(self,Thread_Name,ThreadPointer,Queue):
        self._Thread_Name = Thread_Name
        self._ThreadPointer = ThreadPointer
        self._Queue = Queue

    def Get_Thread_Name(self):
        return self._Thread_Name

    def Get_ThreadPointer(self):
        return self._ThreadPointer

    def Get_Queue(self):
        return self._Queue

def Blank_Function(Thread_Name):
    time.sleep(0.2)





class Thread_Controller:
    def __init__(self,Command_Queue,Name = ""):
        print("Creating Thread Controller",Name)
        self._Name ="TC"+ Name + " >"
        self._Command_Queue = Command_Queue
        self._Threads = {}

    def Create_Thread(self,Thread_Name,TargetCommand = Blank_Function,TargetArgs = (),Process = False):     #If Process is True, will use a Process rather than a thread.
        if Thread_Name in self._Threads: #Close thread if already exists
            self.Close_Thread(Thread_Name)
            
        if Process:
            Thread_Queue = multiprocessing.Queue()
            threadPointer = multiprocessing.Process(target = TargetCommand,args = (Thread_Name,Thread_Queue)+TargetArgs)
        else:
            Thread_Queue = queue.Queue()
            threadPointer = threading.Thread(target = TargetCommand,args = (Thread_Name,Thread_Queue)+TargetArgs)
        self._Threads[Thread_Name] = Thread_Handle(Thread_Name,threadPointer,Thread_Queue)
        threadPointer.start()
        
    def Close_Thread(self,Thread_Name):
        ClosingThreadHandle = self._Threads.pop(Thread_Name)
        Queue = ClosingThreadHandle.Get_Queue()
        Queue.put(("Exit",()))
        print(self._Name,"Thread Controller closed Thread",Thread_Name)
        return ClosingThreadHandle  #Returns Thread_Handle of thread
   

    def PassData(self,Thread_Name,Data):
        Queue = self._Threads[Thread_Name].Get_Queue()
        Queue.put(Data)

    def Main(self):
        Exit = False
        while not Exit:
            try:
                Request = self._Command_Queue.get()   #(Thread_Name/Controller command,"Command",Args)
                self._Command_Queue.task_done()
                
                if Request[0] == "Controller":
                    Command,Args = Request[1],Request[2]
                    if Command == "Create_Thread":               #In total form ("Controller","Create_Thread",(ThreadName,[TargetFunction,TargetArguments]))
                        self.Create_Thread(*Args)
                    elif Command == "Create_Process":
                        self.Create_Thread(*Args, Process = True)
                    elif Command == "Close_Thread":
                        self.Close_Thread(*Args)
                    elif Command == "Exit":  #Shutdown  everything
                        self.Reset(*Args)
                        self._Exit = True
                    elif Command == "Reset":  #Shutdown all threads, not controller
                        self.Reset(*Args)
                        
                else:
                    self.PassData(Request[0],Request[1:])
                        

            except Exception as e:
                print(self._Name,"Error in Thread Controller",e)
        print(self._Name,"Shutting down")


    def Reset(self,Wait_Join = False):
        print(self._Name,"Reseting Thread Threading Controller...")
        Thread_Names = list(self._Threads.keys())
        ThreadHandles = []
        for Thread_Name in Thread_Names:
            ClosingThreadHandle = self.Close_Thread(Thread_Name)
            ThreadHandles.append(ClosingThreadHandle)
            
        if Wait_Join:   #In seperate loop to asyncrously call 'Exit'      
            for ThreadHandle in ThreadHandles:
                ThreadPointer = ThreadHandle.Get_ThreadPointer()
                ThreadPointer.join()
                
        print(self._Name,"Reset Thread Threading Controller")
                
        
        
        
def Create_Controller(process = False, Name = ""):
    if process:
        q = multiprocessing.Queue()
    else:
        q = queue.Queue()
        
    TC = Thread_Controller(q,Name)

    if process:
        t = multiprocessing.Process(target = TC.Main)
    else:   
        t = threading.Thread(target = TC.Main)
    t.start()
    return q


    
