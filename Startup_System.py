import Main_System,queue,UI_Main_Connection

if __name__ == "__main__":
    a_queue = queue.Queue()
    b_queue = queue.Queue()
    UI_umc = UI_Main_Connection.UMC(a_queue,b_queue)
    Main_umc = UI_Main_Connection.UMC(b_queue,a_queue)
    
