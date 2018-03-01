import hashlib,copy

class Merkle_Tree:
    def __init__(self):
##        print("Created merkle tree")
        self._contents = []

    def Add_Hash(self,new_hash):
        self._contents.append(Hash_Item(new_hash))

    def Calculate_Layers(self):
        Layers = []
        Layer = Extend_List(sorted(self._contents))  #Ensure at least length 2
        while len(Layer) > 1:
            Layer = Merge_Layer(Layer)
##            print(Layer)
            Layers.append(Layer)
        return Layers
    
    def Calculate_Root(self):
        Root_Layer = self.Calculate_Layers()[-1]
        return Root_Layer[0].Get_Hash()

    def Get_Hash_Path_Alternates(self,hash_value):
        new_index = Calculate_Next_Index(Find_Hash_Item_Index(Extend_List(sorted(self._contents)),hash_value))
        Layers = self.Calculate_Layers()
        path_values =[]
        for layer in Layers:
            parent = layer[new_index]
##            print(hash_value,parent._ChildA,parent._ChildB)
            path_values.append(parent.Find_Alternate(hash_value))
            hash_value = parent.Get_Hash()
            new_index = Calculate_Next_Index(Find_Hash_Item_Index(Extend_List(layer),hash_value))
        return path_values
            

    def Verify(self,Target_Root_Hash):
        return Target_Root_Hash == self.Calculate_Root()

    def Verify_Merkle_Path(self,seed,path):
        current = seed
        for item in path:
            if item[0] == 0:
                current = item[1]+current
            else:
                current = current+item[1]
            current = hashlib.sha256(current.encode()).hexdigest()
        return current
            





def Extend_List(List):
    if len(List) % 2 == 1:
        List.append(List[-1])
    return List

def Merge_Layer(Layer):
    Layer = Extend_List(copy.deepcopy(Layer))
    New_Layer = []
    for p in range(0,len(Layer),2):
        New_Layer.append(Hash_Item(hashlib.sha256((Layer[p].Get_Hash()+Layer[p+1].Get_Hash()).encode()).hexdigest(),Layer[p].Get_Hash(),Layer[p+1].Get_Hash()))
    return New_Layer

def Calculate_Next_Index(num):
    print(num//2 )
    return num//2

def Find_Hash_Item_Index(Layer,Target):
    for i,item in enumerate(Layer):
        if item.Get_Hash() == Target:
            return i
    raise Exception("No such hash target found in this layer")

class Hash_Item:
    def __init__(self,Hash,ChildA = b"",ChildB = b""):
        self._Hash = Hash
        self._ChildA = ChildA
        self._ChildB = ChildB

    def Get_Hash(self):
        return self._Hash

    def Find_Alternate(self,current):
        if self._ChildA == current:
            return 1,self._ChildB
        elif self._ChildB == current:
            return 0,self._ChildA
        else:
            raise Exception("No such current in this hash")

    def __lt__(self,other):
        return self._Hash < other.Get_Hash()
        


def Create_Test_Tree():
    x = [hashlib.sha256(str(n).encode()).hexdigest() for n in range(20)]
    m = Merkle_Tree()
    for item in x:
        m.Add_Hash(item)
    return m
