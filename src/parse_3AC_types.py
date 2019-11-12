import sys, os
from itertools import takewhile, imap
import pprint

# Command:  python2 parse_3AC_types.py 3AC_types ../out/ir/out10.ir

# Create dict of instructions
instr_dict = {}
func_dict = {}
globvar = []
instr_type = []
with open(sys.argv[1]) as f:
    instr_file = f.read().splitlines()
    j = 0
    for i in range(len(instr_file)):
        if instr_file[i] != '' and instr_file[i] != '.' and instr_file[i] != 'params pn':
            instr_dict[j] = instr_file[i]
            j += 1
    
print instr_dict

curr_func = 0

def classify(line,line_num):
    # package 
    global curr_func
    global func_dict
    global globvar
    if line.startswith('package'):
        return 0
    elif line.startswith('import'):
        return 1
    elif line.startswith('const'):
        func_dict[curr_func]["const"].append(line.split()[1])
        return 2
    elif "=" in line:
        if "[" in line:
            tmp_list = line.split("=")
            if "[" in tmp_list[0]:
                return 20
            else:
                return 19
        elif "*" in line:
            tmp_list = line.split("=")
            if "*" in tmp_list[0]:
                return 22
            else:
                return 21
        
        elif "&" in line:
            return 23

        elif "." in line:    
            tmp_list = line.split("=")
            if "*" in tmp_list[0]:
                return 25
            else:
                return 24
        elif "==" in line:
            return 15
        elif any(op in line for op in ["&&", "||", "+", "/", "*", "-", ">=", "<=", "^", ">>", "<<"]):
            return 4
        elif "temp" in line.split("=")[1]:
            return 3
        else:
            return 5
    elif line.startswith('var'):
        if line.endswith('_0\n'):
            globvar.append(line.split()[1])
        else:
            func_dict[curr_func]["local_var"].append(line.split()[1])
        return 6
    elif line.startswith('paramst'):
        return 7
    elif line.startswith('params'):
        func_dict[curr_func]["params"].append(line.split()[1])
        return 8
    elif line.startswith('call'):
        return 9
    elif "++" in line:
        return 10
    elif "--" in line:
        return 11
    elif line.startswith('if'):
        return 12
    elif line.startswith('goto'):
        return 13
    elif line.startswith('return'):
        return 14
    elif "Func End#" in line:
        func_dict[curr_func]["eline"] = line_num
        return 16
    elif "Func" in line:
        curr_func = line.split()[1]
        func_dict[curr_func] = { "sline" : line_num , "eline": 0 , "local_var": [], "params": [], "const":[] }
        return 17
    elif ':' in line:
        return 18
    else:
        raise Exception("Something is wrong in {}".format(line))

#Now read ir file and classify each instruction
with open(sys.argv[2]) as f:
    line_num=1
    for line in f:
        # print line
        tmp = classify(line,line_num)
        print "{} {} {}".format(line_num, line.rstrip(), tmp)
        line_num+=1
        instr_type.append([line, tmp])
print func_dict
print globvar
