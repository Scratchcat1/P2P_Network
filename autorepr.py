import prettytable
import logging
import os
import sys


class Base:
    def logger_setup(self,module_name):
        #Ensure logs folder has been created
        directory_path = "logs"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        #Get logger for a specific module and class
        self._logger = logging.getLogger(name = module_name+"."+self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        if len(self._logger.handlers) == 0: #Create handlers if they have not already been created.
            #Create a file handler to log
            log_file_handler = logging.FileHandler(os.path.join(directory_path,"debug.log"))
            log_file_handler.setLevel(logging.DEBUG)
            #Create a stream handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            #Create a formatter and pass to stream and file handlers
            formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(name)s - %(message)s")
            log_file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            #Add handlers to logger
            self._logger.addHandler(log_file_handler)
            self._logger.addHandler(console_handler)

    def get_logger(self):
        return self._logger
        
    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ', '.join(items))


def str_repr(obj,data):
    table = prettytable.PrettyTable([obj.__class__.__name__,""])
    for item in data:
        table.add_row(item)
    return str(table)
        

##    highest_length = len(max(data, key = lambda x:len(x[0]))[0])
##    str_repr = obj.__class__.__name__+"\n"
##    for i,item in enumerate(data):
##        str_repr += ("{0:"+str(highest_length)+"}: {1}").format(item[0],item[1])
##        if i != len(data)-1:
##            str_repr += "\n"
##    return str_repr
