import ply.yacc as yacc
import csv
# import utils as ut
import pprint
from graphviz import Digraph
import os, sys
import lexer as lexer
import logging
tokens = lexer.tokens
import pydot
import textwrap
from symboltable import symbolTable,Unification,Function,Pointer,Array,Struct,Integer,String
import copy
import pickle as pkl

dot = Digraph(comment="DOT for parser")

if os.path.exists(sys.argv[3]):
    os.remove(sys.argv[3])
precedence = (
    ('right','ASSIGN', 'NOT'),
    ('left', 'LOGICAL_OR'),
    ('left', 'LOGICAL_AND'),
    ('left', 'OR'),
    ('left', 'XOR'),
    ('left', 'AND'),
    ('left', 'EQUALS', 'NOT_ASSIGN'),
    ('left', 'LESSER', 'GREATER','LESS_EQUALS','MORE_EQUALS'),
    ('left', 'LSHIFT', 'RSHIFT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'DIVIDE','MOD'),
)

#---------------------Utility Variables--------------------
temp_var = {}
temp_var_count = 0
scope_stack = [symbolTable(None)]
type_inf_engine = Unification()
var_size_map = {}
#---------------------Utility Functions -------------------

def init_code_place():
    return { "place" : None , "code" : []}

def new_temp_var():
    global temp_var_count 
    temp_var_count += 1
    return "temp" + str(temp_var_count )


def add_scope(parent):
    new_sym_table = symbolTable(parent)
    return new_sym_table

def delete_scope(parent, key):
    del parent[key] 

# P[0] is a dict with 2 attr with key place and code.
# Empty means emptyDict
# ------------------------START----------------------------
def p_start(p):
    '''start : SourceFile'''
    # p[0] = ["start", p[1]]
    p[0] = p[1]
    # dot.node('start','start')

def p_empty(p):
    """
    empty : 
    """
    p[0] = "empty"
    
def p_source_file(p):
    '''SourceFile : PackageClause SEMICOLON ImportDeclRep TopLevelDeclRep'''
    p[0] = init_code_place()
    # Package clause returns a dict with code package <name>
    for code in p[1]["code"]:
        p[0]["code"].append(code)
    # A list containing a series of import main,import fmt, etc
    for code in p[3]["code"]:
        p[0]["code"].append(code)
    # Various top level declarations code
    for code in p[4]["code"]:
        p[0]["code"].append(code)
    
    with open(sys.argv[2],"w") as f:
        for code in p[0]["code"]:
            f.write(code)
            f.write("\n")
    with open(sys.argv[3], 'a') as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["{}:".format("global")])

        lines = []
        tmp_dict = scope_stack[-1].__repr__()

        for k in tmp_dict:
            if k == "name":
                pass
            v = tmp_dict[k]
            tmp = [k, str(v["type"]), v["scope"]]
            lines.append(tmp)
        writer.writerows(lines)
    import cPickle as pickle

    with open('var_size.txt', 'w') as file:
             file.write(pickle.dumps(var_size_map))

# PackageClause -> package <string>
def p_package_clause(p):
    '''PackageClause : PACKAGE PackageName'''
    p[0]= init_code_place()
    p[0]["code"].append("package %s"%p[2])

def p_package_name(p):
    '''PackageName : IDENTIFIER'''
    p[0] = p[1]

# ImportDeclRep -> import <string>; or import (<string>);
def p_import_decl_rep(p):
    '''ImportDeclRep : empty
                    | ImportDecl SEMICOLON ImportDeclRep '''
    p[0] = init_code_place()
    if len(p) == 4:
        assert(len(p[1]["code"])==1)
        p[0]["code"].append(p[1]["code"][0])
        # Add all the import declarations
        for code in p[3]["code"]:
            p[0]["code"].append(code)

def p_import_decl(p):
    '''ImportDecl : IMPORT STRING
                  | IMPORT LPAREN STRING RPAREN '''
    p[0] = init_code_place()    
    if len(p) == 3:
        p[0]["code"].append("import "+p[2])
    else:
        p[0]["code"].append("import "+p[3])

def p_toplevel_decl_rep(p):
    '''TopLevelDeclRep : TopLevelDecl SEMICOLON TopLevelDeclRep 
                        | empty'''
    p[0] = init_code_place()
    if len(p) == 4:
        # Add all the meta generated code from the RHS. Those should come before the code for the LHS
        for code in p[1]["code"]+p[3]["code"]:
            p[0]["code"].append(code)

def p_top_level_decl(p):
    """
    TopLevelDecl : Declaration
                 | FunctionDecl
    """
    p[0] = p[1]

# Declarations and Scopes
def p_declaration(p):
    """
    Declaration : ConstDecl
                | VarDecl
    """
    p[0] = p[1]

# --------------------------- Constant Declarations --------------------------------
def p_const_decl(p):
    """
    ConstDecl : CONST ConstSpec
    """
    p[0] = p[2]

def p_const_spec(p):
    """
    ConstSpec : IdentifierList
              | IdentifierList ASSIGN ExpressionList
              | IdentifierList Type ASSIGN ExpressionList
    """
    # Assuming that the p[2] contains the type of the variable
    # TODO: Handle Types properly
    p[0] = init_code_place()
    # for id in p[1]:
    #     p[0]["code"].append("const "+"%s_%d"%(id,scope_stack[-1].get_scope(id)))
    if len(p) == 4:
        # Add all the meta generated code from the RHS. Those should come before the code for the LHS
        for code in p[3]["code"]:
            p[0]["code"].append(code)
        for id, exp, exp_type in zip(p[1],p[3]["expr"],p[3]["type"]):
            # Declare
            scope_stack[-1].insert(id,exp_type)
            p[0]["code"].append("const %s_%d"%(id,scope_stack[-1].get_scope(id)))
            # Assign
            p[0]["code"].append("%s_%d = %s"%(id,scope_stack[-1].get_scope(id),exp))
    if len(p) == 5:
        # Add all the meta generated code from the RHS. Those should come before the code for the LHS
        for code in p[4]["code"]:
            p[0]["code"].append(code)
        for id,exp,exp_type in zip(p[1],p[4]["expr"],p[4]["type"]):
            # if type(exp_type) is not type(p[2]):
            if exp_type.name != p[2].name:
                raise SystemError("ERROR on Line {}: const ".format(p.lexer.lineno)+id+ " is of type "+p[2].name+" whereas expression is of type "+exp_type.name)
            scope_stack[-1].insert(id,p[2])
            p[0]["code"].append("%s_%d = %s"%(id,scope_stack[-1].get_scope(id),exp))
        
    if len(p) == 2:
        for id in p[1]:
            scope_stack[-1].insert(id,None)
            p[0]["code"].append("const %s_%d"%(id, scope_stack[-1].get_scope(id)))
        
# ---------------------------------------------------------------------------------

# -------------------------------- Variable Declarations ------------------------------
def p_var_decl(p):
    """
    VarDecl : VAR IdentifierList Type ASSIGN ExpressionList 
            | VAR IdentifierList Type
            | VAR IdentifierList ASSIGN ExpressionList
    """
    # TODO: Handle Types properly
    p[0] = init_code_place()

    if len(p) == 5:
        for code in p[4]["code"]:
            p[0]["code"].append(code)        
        for id, exp, exp_type in zip(p[2],p[4]["expr"],p[4]["type"]):
            scope_stack[-1].insert(id,exp_type)
            p[0]["code"].append("var %s_%d"%(id,scope_stack[-1].get_scope(id)))
            p[0]["code"].append("%s_%d = %s"%(id,scope_stack[-1].get_scope(id),exp))


    if len(p) == 6:
        for code in p[5]["code"]:
            p[0]["code"].append(code)
        for id, exp, exp_type in zip(p[2],p[5]["expr"],p[5]["type"]):
            # if type(p[3]) is not type(exp_type):
            if p[3].name != exp_type.name:
                raise SystemError("ERROR on Line {}: var "+id+" has type ".format(p.lexer.lineno)+p[3].name+" whereas expression has type "+exp_type.name)
            scope_stack[-1].insert(id,p[3])
            p[0]["code"].append("var %s_%d"%(id,scope_stack[-1].get_scope(id)))
            p[0]["code"].append("%s_%d = %s"%(id,scope_stack[-1].get_scope(id),exp))

    if len(p) == 4:
        for id in p[2]:
            scope_stack[-1].insert(id,p[3])
            p[0]["code"].append("var %s_%d"%(id,scope_stack[-1].get_scope(id)))


# ---------------------------------------------------------------------------------------
#======================== Types ================================================
def p_type(p):
    """
    Type : TypeName
         | TypeLit
         | LPAREN Type RPAREN
    """
    if len(p) == 2:
        # p[0] = ["Type",p[1]]
        p[0] = p[1]
    else:
        # p[0] = ["Type","(",p[2],")"]
        p[0] = p[2]

def p_type_name(p):
    """
    TypeName : IDENTIFIER
    """
    if p[1] == "int" or p[1] == "str":
        if p[1] == "int":
            p[0] = Integer()
        else:
            p[0] = String()
    else:
        pass
        # raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]+" is not a valid type")

def p_type_lit(p):
    """
    TypeLit : ArrayType
            | StructType
            | PointerType
            | FunctionType
    """
    p[0] = p[1]

# --------------------------- Array Types -----------------------------
def p_array_type(p):
    """
    ArrayType : LSQUARE ArrayLength RSQUARE ElementType
    """
    t = Array()
    t.set_num_elements(p[2])
    t.set_element_type(p[4])
    p[0] = t    

def p_array_length(p):
    """
    ArrayLength :  INTEGER
    """
    #TODO: Expression not of type int but a dict assert(type(p[1])==int)
    p[0] = p[1]
    if int(p[1]) <= 0:
        raise SystemError("ERROR on Line {}: Array length must be positive".format(p.lexer.lineno))


def p_element_type(p):
    """
    ElementType : Type
    """
    p[0] =  p[1]


# ------------------------------------------------------------------------

# --------------------------- Struct Types -------------------------------
def p_struct_types(p):
    """
    StructType : STRUCT LCURL FieldDeclSemiColonRep RCURL
    """
    # Assuming that the p[3] is of the form ["type1 f1","type2 f2","type3 f3",....,"typen fn"]
    t = Struct()
    for field in p[3]:
        t.add_field(field[1],field[0])
    p[0] = t

def p_field_decl_semicolon_rep(p):
    """
    FieldDeclSemiColonRep : FieldDecl SEMICOLON FieldDeclSemiColonRep
                          | empty
    """
    if len(p) == 2:
        p[0] =  []
    else:
        p[0] = []
        for f in p[1]+p[3]:
            p[0].append(f)

def p_field_decl(p):
    """
    FieldDecl : IdentifierList Type
    """
    p[0] = []
    for id in p[1]:
        p[0].append([p[2],id])

# ------------------------------------------------------------------------------

# ------------------------------ Pointer Types ---------------------------------
def p_pointer_type(p):
    """
    PointerType : STAR BaseType
    """
    t = Pointer()
    t.set_base_type(p[2])
    p[0] = t

def p_base_type(p):
    """
    BaseType : Type
    """
    p[0] = p[1]
# --------------------------------------------------------------------------------
# -------------------------------- Function Types --------------------------------
def p_function_type(p):
    """
    FunctionType : FUNC Signature
    """
    t = Function()
    for param in p[2][0]:
        t.add_param(param[1],param[0])
    for ret in p[2][1]:
        t.add_ret_type(ret)
    p[0] = t

def p_signature(p):
    """
    Signature : Parameters Result
              |  Parameters 
    """
    if len(p) == 2:
        p[0] = [p[1],[],scope_stack[-1].num]
    else:
        p[0] = [p[1],p[2],scope_stack[-1].num]
        for param in p[1]:
            scope_stack[-1].insert(param[1],param[0])

def p_result(p):
    """
    Result : LPAREN TypeList RPAREN
    """
    # Assuming that the p[2] returns the list of types
    p[0] = p[2]

def p_parameters(p):
    """
    Parameters : LPAREN ParamCommaOpt RPAREN
    """
    # Assuming that the p[2] returns the list of parameters in the form ["type1 p1","type2 p2","type3 p3",...]
    p[0] = p[2]

def p_param_comma_opt(p):
    """
    ParamCommaOpt : ParameterList
                 | empty
    """
    if p[1] == "empty":
        p[0] = []
    else:
        p[0] = p[1]

def p_parameter_list(p):
    """
    ParameterList : IdentifierList Type CommaParamDeclRep
    """
    p[0] = []
    for id in p[1]:
        p[0].append([p[2],id])
    for param in p[3]:
        p[0].append(param)

def p_comma_param_decl_rep(p):
    """
    CommaParamDeclRep : COMMA  IdentifierList Type  CommaParamDeclRep
                      | empty
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = []
        for id in p[2]:
            p[0].append([p[3],id])
        for param in p[4]:
            p[0].append(param)

# ----------------------------------------------------------------------------
# ================================ Type End ======================================

def p_create_new_scope(p):
    """
    CreateNewScope : empty
    """
    scope_stack.append(symbolTable(scope_stack[-1]))

def p_del_scope(p):
    """
    DelScope : empty
    """
    # print("Deleted scope {}".format(scope_stack[-1].num))
    
    with open(sys.argv[3], 'a') as f:
        lines = []
        # header = ["name",   "type",   "scope"]
        # lines.append(header)
        writer = csv.writer(f, delimiter=";")
        tmp_dict = scope_stack[-1].__repr__()

        for k in tmp_dict:
            if k == "name":
                pass
            v = tmp_dict[k]
            tmp = [k, str(v["type"]), v["scope"]]
            lines.append(tmp)
        writer.writerows(lines)
    t = scope_stack[-1]
    for key in t.table:
        if key+"_"+str(t.get_scope(key)) in t.table:
            raise SystemError("ERROR:"+key+"_"+str(t.get_scope(key))+"already declared")
        if t.lookup_full(key)["type"] == None:
            print "###### "+key+" type not found ##########"
            var_size_map[key+"_"+str(t.get_scope(key))] = [ Integer(), t.table[key]["istemp"] ]
        else:
            var_size_map[key+"_"+str(t.get_scope(key))] = [ t.lookup_full(key)["type"] ,t.table[key]["istemp"] ]
    scope_stack.pop()

# Blocks
def p_block(p):
    """
    Block : LCURL CreateNewScope StatementList DelScope RCURL    
    """
    p[0] =  p[3]

def p_statement_list(p):
    """
    StatementList : StSemiColonRep
    """
    p[0] =  p[1]                 

def p_st_semicolon_rep(p):
    """
    StSemiColonRep : Statement SEMICOLON StSemiColonRep
                   | empty
    """
    p[0] = init_code_place()
    if len(p) == 4:
        for code in p[1]["code"]:
            p[0]["code"].append(code)
        for code in p[3]["code"]:
            p[0]["code"].append(code)
        if "return" in p[1] and "return" in p[3]:
            if len(p[1]["return"]) != len(p[3]["return"]):
                raise SystemError("ERROR: Line {} ".format(p.lexer.lineno)+"Number of returns values mismatch")
        if "return" in p[1]:
            p[0]["return"] = p[1]["return"]
        elif "return" in p[3]:
            p[0]["return"] = p[3]["return"]
    

def p_identifier_list(p):
    """
    IdentifierList : IDENTIFIER CommaIdentRep
    """
    if p[2]=="empty":
        p[0] = []
    else:
        p[0] = copy.deepcopy(p[2])
    p[0] = [ p[1] ] + p[0]


def p_comma_ident_rep(p):
    """
    CommaIdentRep : COMMA IDENTIFIER CommaIdentRep 
                   | SEMICOLON
    """
    if len(p) == 2:
        p[0] =  "empty"
    else:
        if isinstance(p[3], list):
            p[0] = copy.deepcopy(p[3])
            p[0] = [p[2]] + p[0]
        else:
            p[0] = [p[2]]

def p_expression_list(p):
    """
    ExpressionList : Expression CommaExpRep
    """
    # Assuming expression returns a valid three address code node

    # The expr field of the Expression contains the expression in string form whereas the 
    # the expr filed of expressionlist contains the list of expressions in string form
    p[0] = init_code_place()
    p[0]["expr"] = []
    p[0]["type"] = []
    for code in p[1]["code"]:
        p[0]["code"].append(code)
    p[0]["expr"].append(p[1]["expr"])
    p[0]["type"].append(p[1]["type"])
    if p[2] != "empty":
        for code in p[2]["code"]:
            p[0]["code"].append(code)
        for exp,exp_type in zip(p[2]["expr"],p[2]["type"]):
            p[0]["expr"].append(exp)
            p[0]["type"].append(exp_type)
    

def p_comma_exp_rep(p):
    """
    CommaExpRep : COMMA Expression CommaExpRep
                | empty
    """
    # The expr field of the Expression contains the expression in string form whereas the 
    # expr filed of commaExpRep contains the list of expressions in string form which is used in expressionlist   
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = init_code_place()
        p[0]["expr"] = [p[2]["expr"]]
        p[0]["type"] = [p[2]["type"]]
        for code in p[2]["code"]:
            p[0]["code"].append(code)
        if p[3] != "empty":
            for code in p[3]["code"]:
                p[0]["code"].append(code)
            for exp,exp_type in zip(p[3]["expr"],p[3]["type"]):
                p[0]["expr"].append(exp)
                p[0]["type"].append(exp_type)

# Function Declarations
def p_function_decl(p):
    """
    FunctionDecl : FUNC FunctionName CreateNewScope Signature FunBodyOpt DelScope
    """
    # Signature returns a nested list [["type1 p1","type2 p2",...,"typen,pn"],[type_r1,type_r2,...,type_rn]]
    # If the number of parameters/return is empty then that place of the list contains "empty"
    with open(sys.argv[3], 'a') as f:
        f.write("\n")
    p[0] = init_code_place()

    t = Function()
    for param in p[4][0]:
        t.add_param(param[1],param[0],p[4][2])
    for ret in p[4][1]:
        t.add_ret_type(ret)

    scope_stack[-1].insert(p[2],t)
    # Add the label with the name of the function and then add the body if given
    if p[5] == "empty":
        p[0]["code"].append("Func %s_%d :"%(p[2],scope_stack[-1].num))
    else:
        p[0]["code"].append("Func %s_%d :"%(p[2],scope_stack[-1].num))
        for code in p[5]["code"]:
            p[0]["code"].append(code)
        if t.n_ret == 0:
            if "return" in p[5]:
                for ret in p[5]["return"]:
                    t.add_ret_type(ret)
        else:
            if ("return" not in p[5]) or t.n_ret != len(p[5]["return"]):
                raise SystemError("ERROR: Number of return types mismatch for function "+p[2])
            for r1,r2 in zip(t.ret_types, p[5]["return"]):
                if r1.name != r2.name:
                    raise SystemError("ERROR: Return types mismatch for function "+p[2])
    p[0]["code"].append("Func End#")

def p_fun_body_opt(p):
    """
    FunBodyOpt : FunctionBody
               | empty
    """
    p[0] =  p[1]

def p_function_name(p):
    """
    FunctionName : IDENTIFIER 
    """
    with open(sys.argv[3], 'a') as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["{}:".format(p[1])])
    p[0] = p[1]

def p_functionbody(p):
    """
    FunctionBody : Block
    """
    p[0] =  p[1]

# # Method Declarations
# def p_method_decl(p):
#     """
#     MethodDecl : FUNC Receiver MethodName Signature FunBodyOpt
#     """
#     p[0] = ["func", p[2], p[3], p[4], p[5]]

# def p_receiver(p):
#     """
#     Receiver : Parameters
#     """
#     p[0] = p[1]

# Expressions
# Operands
def p_operand(p):
    """
    Operand : Literal
            | OperandName
            | LPAREN Expression RPAREN
    """
    if len(p) == 2:
        p[0] =  p[1]
    else:
        p[0] =  p[2]

def p_literal(p):
    """
    Literal : BasicLit
    """
    p[0] = p[1]

def p_basic_lit(p):
    """
    BasicLit : Int INTEGER
             | Str STRING
    """
    # For type inference, it is necessary that we introduce a new variable here and assign its type as integer or string
    id = new_temp_var()
    if p[1]=="int":
        t = Integer()
    else:
        t = String()
    scope_stack[-1].insert(id,t,True)
    p[0] = init_code_place()
    p[0]["code"].append("const %s_%d"%(id, scope_stack[-1].num))
    if p[1]=="int":
        p[0]["code"].append("%s_%d"%(id, scope_stack[-1].num)+" = "+ str(p[2]))
    else:
        p[0]["code"].append("%s_%d"%(id, scope_stack[-1].num)+" = "+ "\""+str(p[2])+"\"")
    p[0]["expr"] = "%s_%d"%(id, scope_stack[-1].num)
    p[0]["type"] = t

def p_int(p):
    """
    Int : empty """
    p[0] = "int"

def p_str(p):
    """
    Str : empty """
    p[0] = "str"

def p_operand_name(p):
    """
    OperandName : IDENTIFIER
    """
    p[0] = init_code_place()
    p[0]["expr"] = "%s_%d"%(p[1],scope_stack[-1].get_scope(p[1]))
    p[0]["type"] = scope_stack[-1].lookup_full(p[1])["type"]

#---------------PRIMARY EXPRESSIONS---------------
def p_prim_expr(p):
    '''PrimaryExpr : Operand
                   | PrimaryExpr Selector
                   | PrimaryExpr LSQUARE Expression RSQUARE
                   | PrimaryExpr Arguments'''
    p[0] = init_code_place()
    p[0]["expr"] = ""
    
    if len(p) == 2:
        for code in p[1]["code"]:
            p[0]["code"].append(code)
        p[0]["expr"] = p[1]["expr"]
        p[0]["type"] = p[1]["type"]
    else:
        for code in p[1]["code"]:
            p[0]["code"].append(code)
        p[0]["expr"] = p[1]["expr"]

        if len(p) == 3:
            if p[2][0]==".":
                p[0]["expr"] += ".%s"%p[2][1]
                # tmp = new_temp_var()
                # tmp_id = "%s_%d"%(tmp,scope_stack[-1].num)
                # scope_stack[-1].insert(tmp)
                # p[0]["code"].append("var "+tmp_id)
                # p[0]["code"].append(tmp_id+" = "+p[0]["expr"])
                # p[0]["expr"] = tmp_id
                t = p[1]["type"]
                if t.name != "struct":
                    raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" is not of a struct")
                if t.is_field(p[2][1]) == False:
                    raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" has no field "+p[2][1])
                p[0]["type"] = t.get_field_type(p[2][1])

            else:
                if p[1]["type"].name != "function":
                    raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" is not a function")
                    
                if p[2][1]!="empty":
                    for code in p[2][1]["code"]:
                        p[0]["code"].append(code)

                    if len(p[2][1]["expr"]) != p[1]["type"].n_params:
                        raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" takes "+str(p[1]["type"].n_params)+" arguments")

                    p[0]["code"].append("paramst %s, %d"%(p[1]["expr"],p[1]["type"].n_params))
                    for arg in p[2][1]["expr"]:
                        p[0]["code"].append("params "+arg)
                    p[0]["expr"] = "call %s"%(p[1]["expr"])
                    p[0]["type"] = p[1]["type"].ret_types

        else:
            for code in p[3]["code"]:
                p[0]["code"].append(code)
            if p[3]["expr"][0] == "-":
                raise SystemError("ERROR on Line {}: Array index must be positive".format(p.lexer.lineno))
            p[0]["expr"] += '[' + p[3]["expr"] + ']'
            # tmp = new_temp_var()
            # tmp_id = "%s_%d"%(tmp,scope_stack[-1].num)
            # scope_stack[-1].insert(tmp)
            # p[0]["code"].append("var "+tmp_id)
            # p[0]["code"].append(tmp_id+" = "+p[0]["expr"])
            # p[0]["expr"] = tmp_id
            try:
                t = p[1]["type"]
                if t.name != "array":
                    raise ValueError
                p[0]["type"] = t.element_type
            except ValueError:
                raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" is of type "+p[1]["type"].name+" which is not an array type")

def p_selector(p):
    '''Selector : DOT IDENTIFIER'''
    p[0] = [ ".", p[2]]

def p_argument(p):
    '''Arguments : LPAREN ExpressionListTypeOpt RPAREN'''
    p[0] =  ["arg",p[2]]

def p_expr_list_type_opt(p):
    '''ExpressionListTypeOpt : ExpressionList
                             | empty'''
    # if len(p) == 3:
        # p[0] = ["ExpressionListTypeOpt", p[1], p[2]]
    # else:
    p[0] =  p[1]

# ---------------------------------------------------------

#----------------------OPERATORS-------------------------
def p_expr(p):
    '''Expression : UnaryExpr
                  | Expression LOGICAL_OR Expression
                  | Expression LOGICAL_AND Expression
                  | Expression EQUALS Expression
                  | Expression NOT_ASSIGN Expression
                  | Expression LESSER Expression
                  | Expression GREATER Expression
                  | Expression LESS_EQUALS Expression
                  | Expression MORE_EQUALS Expression
                  | Expression OR Expression
                  | Expression XOR Expression
                  | Expression DIVIDE Expression
                  | Expression MOD Expression
                  | Expression LSHIFT Expression
                  | Expression RSHIFT Expression
                  | Expression PLUS Expression
                  | Expression MINUS Expression
                  | Expression STAR Expression
                  | Expression AND Expression
    '''
    if len(p) == 4:
        p[0] = init_code_place()
        for code in p[1]["code"]+p[3]["code"]:
            p[0]["code"].append(code)
        tmp = new_temp_var()
        # if type(p[1]["type"]) is not type(p[3]["type"]):
        if p[1]["type"].name != p[3]["type"].name:
            raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" and "+p[3]["expr"]+" are not of same type")
        else:
            if p[1]["type"].name != "int":
                raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[1]["expr"]+" and "+p[3]["expr"]+" are not of int type")

        p[0]["type"] = p[1]["type"]
        p[0]["code"].append("%s_%d"%(tmp,scope_stack[-1].num) + " = " +  p[1]["expr"] + " " + str(p[2]) + " " + p[3]["expr"])
        scope_stack[-1].insert(tmp, p[1]["type"],True)
        p[0]["expr"] = "%s_%d"%(tmp,scope_stack[-1].num)

    else:
        p[0] =  p[1]

def p_unary_expr(p):
    '''UnaryExpr : PrimaryExpr
                 | UnaryOp UnaryExpr
                 | NOT UnaryExpr'''
    if len(p) == 2:
        p[0] =  p[1]
    elif p[1] == "!":
        p[0] = init_code_place()
        for code in p[2]["code"]:
            p[0]["code"].append(code)
        p[0]["expr"] = "! "+p[2]["expr"]
        if p[2]["type"].name != "int":
            raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[2]["expr"]+" is not of type int and hence ! operator not applicable")
    else:
        p[0] = init_code_place()
        for code in p[2]["code"]:
            p[0]["code"].append(code)
        # if p[1] == "&":
            # tmp = new_temp_var()
            # tmp_id = "%s_%d"%(tmp,scope_stack[-1].num)
            # scope_stack[-1].insert(tmp)
            # p[0]["code"].append( "var " + tmp_id  )
            # p[0]["code"].append(tmp_id + " = & " + p[2]["expr"]  )
            # p[0]["expr"] = tmp_id
            # p[0]["type"] = Pointer()
            # p[0]["type"].set_base_type(p[2]["type"])
        # elif p[1] == "*":
            # tmp = new_temp_var()
            # tmp_id = "%s_%d"%(tmp,scope_stack[-1].num)
            # scope_stack[-1].insert(tmp)
            # p[0]["code"].append( "var " + tmp_id  )
            # p[0]["code"].append(tmp_id + " = * " + p[2]["expr"]  )
            # if p[2]["type"].name!= "pointer":
                # raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[2]["expr"]+" is not of type pointer and hence * operator not applicable")
            # p[0]["expr"] = tmp_id
            # p[0]["type"] = p[2]["type"].get_base_type()
        # else:
        p[0]["expr"] = p[1] + " " +p[2]["expr"]
        p[0]["type"] = p[2]["type"]
        
        if (p[1] in ['+','-']) and (p[2]["type"].name != "int"):
            raise SystemError("ERROR on Line {}: ".format(p.lexer.lineno)+p[2]["expr"]+" should be of type int with operator "+p[1])

def p_unary_op(p):
    '''UnaryOp : PLUS
               | MINUS
               | STAR
               | AND '''
    if p[1] == '+':
        p[0] =  "+"
    elif p[1] == '-':
        p[0] = "-"
    elif p[1] == '*':
        p[0] =  "*"
    elif p[1] == '&':
        p[0] =  "&"
# -------------------------------------------------------

# ---------------- STATEMENTS -----------------------
def p_statement(p):
    '''Statement : Declaration
                 | SimpleStmt
                 | ReturnStmt
                 | BreakStmt
                 | ContinueStmt
                 | Block
                 | IfStmt
                 | PrintStmt
                 | ScanStmt
                 | SwitchStmt
                 | ForStmt '''
    # p[0] =  ["Statement", p[1]]
    # print "Statement:",p[1]
    p[0] = p[1]

def p_print_stmt(p):
    '''PrintStmt : PRINTF LPAREN PERCD COMMA Expression RPAREN
                 | PRINTF LPAREN PERCS COMMA STRING RPAREN
    '''
    p[0] = init_code_place()
    if p[3] == '%d':
        for code in p[5]['code']:
            p[0]["code"].append(code)
        p[0]["code"].append( "printint " + p[5]['expr'] )
    else:
        p[0]['code'].append( "printstr " + p[5] )


#def p_scan_stmt(p):
#    '''ScanStmt : SCANF LPAREN STRING RPAREN
#    '''
#    p[0] = init_code_place()
#    p[0]["code"].append( "scanf " + p[3] )


def p_simple_stmt(p):
    '''SimpleStmt : empty SEMICOLON
                  | ExpressionStmt SEMICOLON
                  | IncDecStmt SEMICOLON
                  | Assignment SEMICOLON
    '''

    if p[1] != "empty":
        p[0] = p[1]
    else:
        p[0] = init_code_place()

def p_expression_stmt(p):
    ''' ExpressionStmt : Expression'''
    # print "ExpressionStmt: ",p[1]
    p[0] = p[1]

def p_inc_dec(p):
    """
    IncDecStmt : IDENTIFIER INCR
               | IDENTIFIER DECR
    """ 
    # Set type to int
    p[0] = init_code_place()
    t = scope_stack[-1].get_scope(p[1])
    if scope_stack[-1].lookup_full(p[1])["type"].name != "int":
        raise SystemError("ERROR on line {}: ".format(p.lexer.lineno)+p[1]+" should be of type int")
    if p[2] == '++':
        p[0]["code"].append( p[1] + "_" + str(scope_stack[-1].get_scope(p[1])) + " ++" )
    else:
        p[0]["code"].append( p[1]  + "_" + str(scope_stack[-1].get_scope(p[1])) + " --" )

def p_assignment(p):
    ''' Assignment : ExpressionList AssignOp ExpressionList
                    '''
    # print "ExprList : ",p[1]
#   p[0] = [ "RepStmt", p[1], p[2], p[3]]
    assert( len(p[1]["expr"]) == len(p[3]["expr"] )  )
    p[0] = init_code_place()
    for code in p[3]["code"]+p[1]["code"]:
        p[0]["code"].append(code)
    for idn, exp, typ1, typ2 in zip( p[1]["expr"], p[3]["expr"],p[1]["type"],p[3]["type"]):
        if p[2] != "=":
            t_op = p[2][:-1]
            tmp_id = new_temp_var()
            scope_stack[-1].insert(tmp_id,typ1,True)
            p[0]["code"].append("var %s_%d"%(tmp_id,scope_stack[-1].get_scope(tmp_id)))
            p[0]["code"].append( "%s_%d"%(tmp_id,scope_stack[-1].get_scope(tmp_id)) + " = " + exp )
            p[0]["code"].append(idn + " = " + idn + " " + t_op + " " + "%s_%d"%(tmp_id,scope_stack[-1].get_scope(tmp_id)))
        else:
            p[0]["code"].append(idn + " = " + exp)
    # for typ1,typ2 in zip(p[1]["type"],p[3]["type"]):
        # if type(typ1) is not type(typ2):
        if typ1.name != typ2.name:
            raise SystemError("ERROR on line {}: Assignment operation with different types: ".format(p.lexer.lineno)+idn+" of type "+typ1.name+" and "+exp+" of type "+typ2.name)


def p_AssignOp(p):
    ''' AssignOp : PLUS_ASSIGN
               | MINUS_ASSIGN
               | STAR_ASSIGN
               | DIVIDE_ASSIGN
               | MOD_ASSIGN
               | AND_ASSIGN
               | OR_ASSIGN
               | XOR_ASSIGN
               | LSHIFT_ASSIGN
               | RSHIFT_ASSIGN
               | ASSIGN '''
    p[0] =  p[1]

if_global_label = 0
def p_if_statement(p):
    ''' IfStmt : IF  Expression Block ElseOpt '''
    p[0] = init_code_place()
    for code in p[2]["code"]:
        p[0]["code"].append(code)
    p[0]["code"].append( "if ! " + p[2]["expr"] + " goto " + p[4]["startlabel"])
    for code in p[3]["code"]:
        p[0]["code"].append(code)
    # if len(p[4]["code"]) > 1: # its length is atleast 1
    p[0]["code"].append( "goto " + p[4]["endlabel"] )
    for code in p[4]["code"]:
        p[0]["code"].append(code)
    if ("return" in p[3]) and ("return" in p[4]):
        if len(p[3]["return"]) != len(p[4]["return"]):
            raise SystemError("ERROR: Line {} ".format(p.lexer.lineno)+"Number of return values mismatch")
    if "return" in p[3]:
        p[0]["return"] = p[3]["return"]
    if "return" in p[4]:
        p[0]["return"] = p[4]["return"]
    if p[2]["type"].name != "int":
        raise SystemError("ERROR on line {}: condition in if stmt should be int but ".format(p.lexer.lineno)+p[1]["expr"]+" is not")

def p_else_opt(p):
    ''' ElseOpt : ELSE IfStmt
              | ELSE Block
              | empty'''
    p[0] = init_code_place()
    global if_global_label
    p[0]["startlabel"] = "else_start_" + str(if_global_label)
    p[0]["endlabel"] = "else_end_" + str(if_global_label)
    if_global_label += 1
    p[0]["code"].append(p[0]["startlabel"]+" :")
    if len(p) == 3:
        for code in p[2]["code"]:
            p[0]["code"].append(code)
        if "return" in p[2]:
            p[0]["return"] = p[2]["return"]
    p[0]["code"].append(p[0]["endlabel"]+" :")


###########################################

########### SWITCH STATEMENTS #############

def p_switch_statement(p):
    '''SwitchStmt : CreateNewScope ExprSwitchStmt DelScope
                   '''
    p[0] =  p[2]

switch_glob_label = 0
def p_expr_switch_stmt(p):
    ''' ExprSwitchStmt : SWITCH Expression LCURL ExprCaseClauseRep RCURL'''
    p[0] = init_code_place()
    default = init_code_place()
    for code in p[2]["code"]:
        p[0]["code"].append(code)
    global switch_glob_label
    switch_glob_label+=1
    start_num = "label_switch_end_" + str(switch_glob_label)
    for el in p[4]:
        if el[0][0] == "default":
            default = el[1]
            continue
        switch_glob_label += 1
        p[0]["code"].append( "label_case_"+ str(switch_glob_label)+" :")
        tmp_id = new_temp_var()
        tmp = tmp_id + '_' + str(scope_stack[-1].num)
        scope_stack[-1].insert(tmp_id, Integer(), True)
        for code in el[0][2]:
            p[0]["code"].append(code)
        p[0]["code"].append("var " + tmp)
        p[0]["code"].append( tmp+" = "+el[0][1]+" == "+p[2]["expr"] )
        p[0]["code"].append( "if ! " + tmp+ " goto label_case_"+str(switch_glob_label+1))
        for code in el[1]["code"]:
            p[0]["code"].append(code)
        if "return" in el[1]:
            if "return" in p[0] and len(p[0]["return"])!=len(el[1]["return"]):
                raise SystemError("ERROR: Line {} ".format(p.lexer.lineno)+"Number of return values mismatch")
            p[0]["return"] = el[1]["return"]
        p[0]["code"].append("goto " + start_num )
    switch_glob_label += 1
    p[0]["code"].append("label_case_"+str(switch_glob_label)+" :")
    for code in default["code"]:
        p[0]["code"].append(code)
    p[0]["code"].append(start_num + " :")
    if "return" in default:
        if ("return" in p[0]) and len(p[0]["return"])!=len(default[1]["return"]):
            raise SystemError("ERROR: Line {} ".format(p.lexer.lineno)+"Number of return values mismatch")
        p[0]["return"] = default["return"]

def p_expr_case_clause_rep(p):
    ''' ExprCaseClauseRep : ExprCaseClause ExprCaseClauseRep 
                            | empty'''
    if len(p) == 3:
        p[0] = [ p[1] ] +  p[2]
    else:
        p[0] =  []

def p_expr_case_clause(p):
    ''' ExprCaseClause : ExprSwitchCase COLON StatementList'''
    p[0] = [p[1] , p[3]]

def p_expr_switch_case(p):
    ''' ExprSwitchCase : CASE BasicLit
                        | DEFAULT '''

    if len(p) == 3:
        p[0] = [ "case", p[2]["expr"], p[2]["code"] ]
    else:
        p[0] =  [ p[1] ]

def p_type_list(p):
    ''' TypeList : Type TypeRep'''
    p[0] = []
    p[0].append(p[1])
    for typ in p[2]:
        p[0].append(typ)

def p_type_rep(p):
    ''' TypeRep : COMMA Type TypeRep 
                | empty'''
    p[0] = []
    if len(p) == 4:
        p[0].append(p[2])
        for typ in p[3]:
            p[0].append(typ)

for_glob_label = 0

def p_for(p):
    '''ForStmt : CreateNewScope FOR ForClause Block DelScope'''
    p[0] = init_code_place()
    for code in p[3]["code"]:
        p[0]["code"].append(code)
    for code in p[4]["code"]:
        p[0]["code"].append(code)
    for code in p[3]["cond_code"]:
        p[0]["code"].append(code)
    if "return" in p[4]:
        p[0]["return"] = p[4]["return"]


def p_forclause(p):
    '''ForClause : SimpleStmt ConditionOpt SEMICOLON SimpleStmt'''
    p[0] = init_code_place()
    global for_glob_label
    for code in p[1]["code"]:
        p[0]["code"].append(code)
    
    tmp_cond = "label_for_"+str(for_glob_label+1)
    p[0]["code"].append("label_for_"+str(for_glob_label+1)+" :")
    for_glob_label += 1

    for code in p[2]["code"]:
        p[0]["code"].append(code)
    
    tmp_end = "endFor_"+str(for_glob_label)
    p[0]["code"].append("if ! "+p[2]["expr"]+ " goto endFor_"+str(for_glob_label))
    for_glob_label += 1
    # required for break statement
    scope_stack[-1].end_label = tmp_end
    # required for continue statement

    tmp_cond_update = "cond_update_"+str(for_glob_label-1)
    p[0]["cond_code"] = []
    scope_stack[-1].condition_label = tmp_cond_update
    p[0]["cond_code"].append(tmp_cond_update+" :")
    for code in p[4]["code"]:
        p[0]["cond_code"].append(code)
    p[0]["cond_code"].append("goto "+tmp_cond)
    p[0]["cond_code"].append(tmp_end+" :")

def p_conditionopt(p):
    '''ConditionOpt : empty
            | Condition '''
    p[0] = init_code_place()
    if p[1]!="empty":
        p[0] =  p[1]
    else:
        p[0]["expr"] = "true"

def p_condition(p):
    '''Condition : Expression '''
    p[0] =  p[1]

def p_return(p):
    '''ReturnStmt : RETURN ExpressionListPureOpt'''
    p[0] = init_code_place()
    for code in p[2]["code"]:
        p[0]["code"].append(code)
    for exp in p[2]["expr"]:
        p[0]["code"].append("return "+exp)
    p[0]["return"] = []
    for typ in p[2]["type"]:
        p[0]["return"].append(typ)    

def p_expressionlist_pure_opt(p):
    '''ExpressionListPureOpt : ExpressionList
                | empty'''
    p[0] = init_code_place()
    if p[1] != "empty":
        p[0] =  p[1]

def p_break(p):
    '''BreakStmt : BREAK '''
    p[0] = init_code_place()
    t = scope_stack[-1].get_end_label()
    p[0]["code"].append("goto "+t)

def p_continue(p):
    '''ContinueStmt : CONTINUE '''
    p[0] =  init_code_place()
    t = scope_stack[-1].get_condition_label()
    p[0]["code"].append("goto "+t)

def p_error(p):
    print("Syntax error in input!")
    print(p)
 
log = logging.getLogger()
parser = yacc.yacc()

try:
    with open(sys.argv[1],"r") as f:
        s = f.read()
except EOFError:
    pass 
result = parser.parse(s)
with open(sys.argv[4],"wb") as pkl_file:
    pkl.dump(var_size_map,pkl_file)
# print result

# root_node = ut.get_parse_tree(result)
# ut.convert_parse_tree_to_ast(root_node)
# dot_obj = ut.ASTVisualizer(root_node)
# with open(sys.argv[2],"w") as f:
#     f.write(dot_obj.gendot())
