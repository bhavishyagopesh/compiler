import sys
import re
import ply.lex as lex
import argparse

keywords = {'BREAK', 'CASE', 'CONST', 'CONTINUE', 'DEFAULT', 'ELSE', 'FOR', 'FUNC', 'GOTO', 'IF', 'IMPORT', 'PACKAGE', 'RANGE', 'RETURN', 'STRUCT', 'SWITCH', 'TYPE', 'VAR','PRINTF','SCANF'}

operators = { 'AND', 'AND_ASSIGN', 'AND_XOR_ASSIGN', 'ASSIGN', 'COLON', 'COMMA', 'DECR', 'DIVIDE', 'DIVIDE_ASSIGN', 'DOT', 'EQUALS', 'GREATER', 'INCR', 'LCURL', 'LESSER', 'LESS_EQUALS', 'LOGICAL_AND', 'LOGICAL_OR', 'LPAREN', 'LSHIFT', 'LSHIFT_ASSIGN', 'LSQUARE', 'MINUS', 'MINUS_ASSIGN', 'MOD', 'MOD_ASSIGN', 'MORE_EQUALS', 'NOT', 'NOT_ASSIGN', 'OR', 'OR_ASSIGN', 'PLUS', 'PLUS_ASSIGN', 'QUICK_ASSIGN', 'RCURL', 'RPAREN', 'RSHIFT', 'RSHIFT_ASSIGN', 'RSQUARE', 'SEMICOLON', 'STAR', 'STAR_ASSIGN', 'XOR', 'XOR_ASSIGN', 'PERCD', 'PERCS'}
types = {'INTEGER', 'HEX', 'FLOAT', 'STRING', 'IMAGINARY', 'RUNE'}
identity = {'IDENTIFIER'}
# tertiary_keywords = {'Println'}
comments = {'COMMENT'}

reserved = {}
for r in keywords:
	reserved[r.lower()] = r

# for r in tertiary_keywords:
# 	reserved[r] = r

tokens = list(operators) + list(types) + \
              list(identity) + list(reserved.values()) + list(comments)

# Token definitions

t_ignore_COMMENT = r'(/\*([^*]|\n|(\*+([^*/]|\n])))*\*+/)|(//.*)'
t_ignore = ' \t'
t_PLUS = r'\+'
t_MINUS = r'-'
t_STAR = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
t_ASSIGN = r'='
t_AND = r'&'
t_LOGICAL_AND = r'&&'
t_INCR = r'\+\+'
t_DECR = r'--'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_OR = r'\|'
t_XOR = r'\^'
t_LSHIFT = r'<<'
t_RSHIFT = r'>>'
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_STAR_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MOD_ASSIGN = r'%='
t_AND_ASSIGN = r'&='
t_OR_ASSIGN = r'\|='
t_XOR_ASSIGN = r'\^='
t_LSHIFT_ASSIGN = r'<<='
t_RSHIFT_ASSIGN = r'>>='
t_AND_XOR_ASSIGN = r'&\^='
t_LOGICAL_OR = r'\|\|'
t_EQUALS = r'=='
t_LESSER = r'<'
t_GREATER = r'>'
t_NOT = r'!'
t_NOT_ASSIGN = r'!='
t_LESS_EQUALS = r'<='
t_MORE_EQUALS = r'>='
t_QUICK_ASSIGN = r':='
t_LSQUARE = r'\['
t_RSQUARE = r'\]'
t_LCURL = r'\{'
t_RCURL = r'\}'
t_COMMA = r','
t_DOT = r'\.'
t_SEMICOLON = r';'
t_COLON = r':'
t_PERCD = r'%d'
t_PERCS = r'%s'

decimal_lit = "(0|([1-9][0-9]*))"
hex_lit = "(0x|0X)[0-9a-fA-F]+"

float_lit = "([0-9]*\.[0-9]+([eE][-+]?[0-9]+)? | [0-9]+[eE][-+]?[0-9]+)"
# float_lit = "[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?"
string_lit = """("[^"]*")"""
imaginary_lit = "(" + decimal_lit + "|" + float_lit + ")i"

rune_lit = "\'(.|(\\[abfnrtv]))\'"

identifier_lit = "[_a-zA-Z]+[a-zA-Z0-9_]*"


@lex.TOKEN(identifier_lit)
def t_IDENTIFIER(t):
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t


@lex.TOKEN(rune_lit)
def t_RUNE(t):
    t.value = ord(t.value[1:-1])
    return t


@lex.TOKEN(string_lit)
def t_STRING(t):
    t.value = t.value[1:-1]
    return t


@lex.TOKEN(imaginary_lit)
def t_IMAGINARY(t):
    t.value = complex(t.value.replace('i','j'))
    return t


@lex.TOKEN(float_lit)
def t_FLOAT(t):
    t.value = float(t.value)
    return t


@lex.TOKEN(hex_lit)
def t_HEX(t):
    t.value = int(t.value, 16)
    return t


@lex.TOKEN(decimal_lit)
def t_INTEGER(t):
    t.value = int(t.value)
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print("Illegal Character")
    t.lexer.skip(1)


lexer = lex.lex()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg')
    parser.add_argument('--input')
    parser.add_argument('--output')

    args = parser.parse_args()

    color_dict = {}

    with open(args.cfg) as f:
        cfgs = f.readlines()

        for cfg in cfgs:
            token_name = cfg.split()[0]
            color = cfg.split()[1]
            color_dict[token_name] = color

    with open(args.input) as f:
        chars = f.read()
        chars += '\n'
        lexer = lex.lex()
        lexer.input(chars)
    
        line_no =  1
        line_pos = 0
        print "[DEBUG] color_dict:",color_dict
        with open(args.output, "w") as g:
            g.write("""<!DOCTYPE html>
<html>
<head>
<title>Page Title</title>
</head>
<body text="black">\n""")
            while True:
                tok = lexer.token()
                print(tok)
                
                if not tok:
                    break

                # Adjust line
                for i in range(tok.lineno-line_no):
                    g.write("\n<br>")
                    line_pos+= 1
                line_no = tok.lineno

                for i in range(tok.lexpos-line_pos):
                    g.write("&nbsp;")
                line_pos = tok.lexpos

                if tok.type in keywords:
                    color_html = "<font color="
                    g.write(color_html+"\""+color_dict["keywords"]+"\">" + str(tok.value)+"</font>")
                
                elif tok.type in operators:
                    color_html = "<font color="
                    g.write(color_html+"\""+color_dict["operators"]+"\">" + str(tok.value)+"</font>")
                
                elif tok.type in types:
                     
                    if tok.type == 'STRING':
                        color_html = "<font color="
                        g.write(color_html+"\""+color_dict["types"]+"\">" + "\"" +str(tok.value)+ "\"" +"</font>")
                        line_pos+=2
                    else:
                        color_html = "<font color="
                        g.write(color_html+"\""+color_dict["types"]+"\">" + str(tok.value)+"</font>")

                elif tok.type in comments:
                    color_html = "<font color="
                    g.write(color_html+"\""+color_dict["comments"]+"\">" + str(tok.value)+"</font>")
                elif tok.type in identity:
                    color_html = "<font color="
                    g.write(color_html+"\""+color_dict["identity"]+"\">" + str(tok.value)+"</font>")
                else:
                    print "Error type token {}".format(tok)
                    exit()
                line_pos += len(str(tok.value))
            
            g.write("""
</body>
</html>""")
