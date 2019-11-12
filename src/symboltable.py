import csv
class Type:
    def __init__(self):
        pass
    
class Pointer(Type):
    def __init__(self):
        self.name = "pointer"
        self.base_type = None
    
    def set_base_type(self, btype):
        if self.base_type != None:
            raise SystemExit("ERROR: Base type of pointer cannot be reassigned")
        self.base_type = btype

    def get_size(self):
        return 8

    def get_base_type(self):
        if self.base_type == None:
            raise SystemError("ERROR: BaseType not set")
    
class Array(Type):
    def __init__(self):
        self.name = "array"
        self.n_elements = 0
        self.element_type = None
    
    def set_element_type(self, etype):
        if self.element_type != None:
            raise SystemExit("ERROR: Element Type of the array cannot be reassigned")
        self.element_type = etype
    
    def set_num_elements(self, n):
        if self.n_elements != 0:
            raise SystemExit("ERROR: Number of elements in the array cannot be reassigned")
        if n <= 0:
            raise SystemExit("ERROR: Number of elements in the array should be positive")
        self.n_elements = n

    def get_size(self):
        return self.element_type.get_size() * self.n_elements
        
class Integer(Type):
    def __init__(self):
        self.name = "int"

    def get_size(self):
        return 4

class Float(Type):
    def __init__(self):
        self.name = "float"

    def get_size(self):
        #TODO: Size of float is 8??
        return 8

class String(Type):
    def __init__(self):
        self.name = "str"

    def get_size(self):
        return 8 

class Struct(Type):
    def __init__(self):
        self.name = "struct"
        self.n_fields = 0
        self.fields = []
        self.field_types = []
        self.size = 0
    def add_field(self,field,ftype):
        if field in self.fields:
            raise SystemExit("ERROR: Struct field "+field+" repeated")
        self.n_fields += 1
        self.fields.append(field)
        self.field_types.append(ftype)
        self.size += ftype.get_size()
    
    def get_field_type(self,field):
        if field not in self.fields:
            raise SystemExit("ERROR: "+field+" not present in the struct")
        index = self.fields.index(field)
        return self.field_types[index]
    
    def is_field(self, field):
        return (field in self.fields)
    
    def get_size(self):
        return self.size
    
class Function(Type):
    def __init__(self):
        self.name = "function"
        self.n_params = 0
        self.n_ret = 0
        self.parameters = []
        self.param_type = []
        self.ret_types = []
        self.param_actual_names = []

    def add_param(self,param, ptype, scope):
        if param in self.parameters:
            raise SystemExit("ERROR: Function argument "+param+" repeated")
        self.n_params += 1
        self.parameters.append(param)
        self.param_type.append(ptype)
        self.param_actual_names.append(param+"_"+str(scope))

    def add_ret_type(self, rtype):
        self.n_ret += 1
        self.ret_types.append(rtype)

    def get_param_type(self, param):
        try:
            index = self.parameters.index(param)
        except ValueError:
            raise SystemExit("ERROR: "+param+" not present in function definition as an argument")
        return self.param_type[index]
    
    def is_param(self, param):
        return (param in self.parameters)

class Unification:
    def __init__(self):
        self.type_num = 0
        self.type_map = []
    
    def get_new_type(self):
        self.type_map.append(None)
        self.type_num += 1
        return self.type_num-1

    def get_root(self,type_num):
        if type_num >= self.type_num:
            raise SystemExit("ERROR: Type not declared")
        if (self.type_map[type_num] == None) or (isinstance(self.type_map[type_num],Type)):
            return type_num
        t = self.get_root(self.type_map[type_num])
        self.type_map[type_num] = t
        return t

    def get_type(self, type_num):
        t = self.get_root(type_num)
        return self.type_map[t]

    def bind(self, type_num, base_type):
        if isinstance(base_type, Type):
            raise SystemExit("ERROR: Not a valid type")
        if type_num >= self.type_num:
            raise SystemExit("ERROR: Type not declared")
        t = self.get_root(type_num)
        if self.type_map[t] == None:
            self.type_map[t] = base_type
        else:
            if type(self.type_map[t]) is not type(base_type):
                raise SystemExit("UNIFICATION ERROR: "+type(self.type_map[t])+" can't be merged with "+type(base_type))

    def unify(self, type1, type2):
        if max(type1,type2) >= self.type_num:
            raise SystemExit("ERROR: Type not declared")
        t1 = self.get_root(type1)
        t2 = self.get_root(type2)
        if t1==t2:
            return
        m = min(t1,t2)
        M = max(t1,t2)
        if self.type_map[m] == None and self.type_map[M] == None:
            self.type_map[M] = m
        elif self.type_map[m] == None:
            self.type_map[m] = self.type_map[M]
        elif self.type_map[M] == None:
            self.type_map[M] = self.type_map[m]
        else:
            if type(self.type_map[m]) is not type(self.type_map[M]):
                raise SystemExit("UNIFICATION ERROR: "+type(self.type_map[m])+" can't be merged with "+type(self.type_map[M]))

class symbolTable:
    symbolTable_num = 0
    def __init__(self, parent):
        self.table = {}
        self.parent = parent
        self.end_label = None # Required for break statement
        self.condition_label = None # Required for continue statement
        self.num = symbolTable.symbolTable_num
        symbolTable.symbolTable_num += 1

    def lookup_present(self, name):
        if name in self.table:
            return True
        else:
            return False
    
    def _lookup(self,current,name):
        if current is None:
            return -1
        # print "lookup:",name," table:\n",current.table
        # print "current.lookup_present(name):",current.lookup_present(name)
        if current.lookup_present(name):
            return current.table[name]
        else:
            return current._lookup(current.parent,name)

    def lookup_full(self, name):
        return self._lookup(self,name)

    def get_scope(self, name):
        t = self.lookup_full(name)
        if t==-1:
            raise SystemError("ERROR: "+name+" not declared")
            return -1
        else:
            return t["scope"]

    def _end_label(self,current):
        if current is None:
            return -1
        if current.end_label is not None:
            return current.end_label
        else:
            return current._end_label(current.parent)

    def get_end_label(self):
        t = self._end_label(self)
        if t==-1:
            raise SystemExit("ERROR: break must be inside for loop")
        else:
            return t
    
    def _condition_label(self,current):
        if current is None:
            return -1
        if current.condition_label is not None:
            return current.condition_label
        else:
            return current._condition_label(current.parent)

    def get_condition_label(self):
        t = self._condition_label(self)
        if t==-1:
            raise SystemExit("ERROR: continue must be inside for loop")
        else:
            return t

    def lookup(self, name):
        try :
            return (name in self.table)
        except KeyError as e:
            print ("{} not found in symboltable".format(name))

    def insert(self, name, typevar, istemp=False ):
        if self.lookup(name):
            raise SystemExit("ERROR: "+name+" already declared in the present scope")
            print("{} already exist in symboltable".format(name))
        else:
            self.table[name] = {"type": typevar, "scope":self.num, "istemp":istemp }

    def update(self, name, typevar):
        if not self.lookup(name):
            print("{} does not exist in symboltable".format(name))
        else:
            self.table[name] = {"type": typevar}

    def __repr__(self):
        
        return self.table
            # print("{:5}  {:5}  {:5}".format(k, v["type"], v["scope"]))
