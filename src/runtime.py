from parse_3AC_types import instr_dict, func_dict, globvar, instr_type
import sys,os
from symboltable import Function,Pointer,Array,Struct,Integer,String

# instr_dict : {0:'package string',1:'import string',..}
# func_dict : {<func_name>:{'params','eline','sline','local_var','const'},...}
# globvar : list of global variables
# instr_type: [[instr, type],...]

# takes var_map as input
def _cal_offset_local(func_name,var_type_map):
    """
    Calculate the  offsets for the local variables

    param func_name: Name of the function
    param var_type_map: Type instance of all the variables

    return:
    dict with var_name as key and int as value
    """
    local_vars = func_dict[func_name]["local_var"]
    offset = -4
    var_offset = {}
    for var in local_vars:
        if var in var_offset:
            raise SystemError("ERROR: Same variable "+var+" repeated")
        var_offset[var] = offset
        offset -= var_type_map[var][0].size
    return var_offset

def _cal_offset_params(func_name,var_type_map):
    """
    Calculate the  offsets for the local variables

    param func_name: Name of the function
    param var_type_map: Type instance of all the variables

    return:
    dict with var_name as key and int as value
    """
    params = var_type_map[func_name][0]
    assert(params.name == "function")
    local_vars = params.param_actual_names
    local_vars.reverse()
    offset = 8
    var_offset = {}
    for var in local_vars:
        if var in var_offset:
            raise SystemError("ERROR: Same variable "+var+" repeated")
        var_offset[var] = offset
        offset += var_type_map[var][0].size
    return var_offset

def make_activation_record(func_name,var_map):
    local_vars_offset = _cal_offset_local(func_name, var_map)
    params_offset = _cal_offset_params(func_name,var_map)
    local_vars_offset.update(params_offset)
    return local_vars_offset