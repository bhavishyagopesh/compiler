import symboltable

# 'x' is multiply and '*' is dereferencing
type_3 = ['+', '-', 'x', '/', '%', '&', '|', '^', '==', '<', '>', '!=', '<=', '>=']

type_2 = ['=', '+=', '-=', 'x=', '&=',
          '|=', '^=', '<<=', '>>=',
           'ifgoto', 'callint', 'load', 'store', 'array', 'pload', 'addr']

type_1 = ['++', '!', '--', 'label', 'printint', 'printstr', 'scan', 'callvoid', 'goto', 'retint', 'push', 'pop']

type_0 = ['retvoid']

instr_types = type_3 + type_2 + type_1 + type_0

# Symbol Table object
ST = symboltable.symbolTable()
