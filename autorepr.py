import prettytable

class AutoRepr:
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
