import re
from includes import SymTab
from enum import Enum

class stat(Enum):
    LIVE = 1
    DEAD = 2

def isInt(num):
    return re.match('-?\d+', num) != None

def isFloat(num):
    return re.match('-?\d+.\d+', num) != None

## this function extracts variables, converts them into pointer to symbols in symTableDict and also stores them in symlist
def makeVarList(irlist, varlist, symlist, arraylist):
    ## symlist is a mapping from "symbols" in IRcode to the variable it is pointing to
    tmp_varlist = set()

    for ir in irlist:
        if ir[1] in [ 'return', 'label', 'function', 'goto']:
            pass
        elif ir[1]=='call' and len(ir)==4:
            if isinstance(ir[3], SymTab.VarType):
                tmp_varlist.add(ir[3])
        elif ir[1]=='call':
            pass
        elif ir[1] == "ifgoto":
            for i in range(3,5):
                if isinstance(ir[i], SymTab.VarType):
                    tmp_varlist.add(ir[i])
        elif ir[1] == "print":
            if isinstance(ir[2], SymTab.VarType):
                tmp_varlist.add(ir[2])
        else:
            ## statements of the form :: lineno, operator, { var | literal ,}
            for i in range(2,len(ir)):
                if isinstance(ir[i], SymTab.VarType):
                    tmp_varlist.add(ir[i])

    for i in tmp_varlist:
        varlist.append(i)
        symlist.append(i)
