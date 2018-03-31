#!/usr/bin/env python

from sys import path
import os
path.extend(['.','..'])

import ply.lex as lex
import ply.yacc as yacc
from src import myLexer

MyLexer = myLexer.MyLexer

from sys import argv
from includes import SymTab

## GLOBALS
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class TypeSystem(object):
    def __init__(self):
        pass

    def isTypeConvertible(self, t1, t2):
        if (t1 == 'int' and t2 == 'real') or (t1 == 'real' and t2 == 'int'):
            return 'real'
        return None

    def typeHandler(self, p1, p2, token):
        mapX = expTypeMap[token]
        t1, v1 = p1['type'], p1['place']

        if p2 != None:
            t2, v2 = p2['type'], p2['place']

            if t1 in mapX[:len(mapX)-1] and t2 in mapX[:len(mapX)-1]:
                if t1 == t2:
                    return {
                         'type': t1 if mapX[len(mapX)-1] == None else mapX[len(mapX)-1]
                        ,'value1': v1
                        ,'value2': v2
                        }
                else:
                    t3 = self.isTypeConvertible(t1, t2)
                    if t3 != None:
                        return {
                             'type': t3
                            ,'value1': v1
                            ,'value2': v2
                            }
                    # TODO :: make error more informative
                    raise TypeError("Types Cannot be converted.")
            else:
                # TODO :: make error more informative
                raise TypeError("Type Mismatch")

        else:
            ## case of unaryop
            if t1 in mapX[:len(mapX)-1]:
                return p1
            # TODO :: make error more informative
            raise TypeError("Invalid Type")

    def returnTypeCheck(self, pType, table):
        ## get to the table corresponding to the enclosing function
        ## search based on Category :: used the fact that function cannot
        ## contain function inside them
        if table.category == SymTab.Category.Function:
            if table.attr['type'] != pType:
                return False
            return True
        else:
            return self.returnTypeCheck(pType, table.parent)


class MyParser(TypeSystem):

    tokens = MyLexer.tokens

    # Precedence and associativity of operators
    precedence = (
        ('right', 'EQ'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'BIT_OR'),
        ('left', 'BIT_XOR'),
        ('left', 'BIT_AND'),
        ('left', 'EQEQ', 'NTEQ'),
        ('nonassoc', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'RSHIFT', 'LSHIFT'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'MULTIPLY', 'DIVIDE', 'MODULUS'),
        ('right', 'NOT'),
        ('left', 'DOT') ## member access
    )

    def __init__(self, lexer):
        TypeSystem.__init__(self)
        self.lexer = lex.lex(module=MyLexer())
        self.stManager = SymTab.TableManager()
        self.recentType = None ## for handling the case int a, b = a;

    ## Helper functions =========================================================
    def gen(self, *argv):
        strx = ''
        for arg in argv:
            strx += str(arg) + ', '
        return strx[:-2] + '\n'

    def printParseTree(self, p):
        flag = False
        if flag:
            print(p.slice)

    def mallocInLoop(self, arr, plist, alloc_size):
        malloc_code=""
        tmp=SymTab.newTemp(str(arr.type)[:len(str(arr.type))-2])
        i=SymTab.newTemp('int')
        loop_block=self.stManager.newLabel()
        after_block=self.stManager.newLabel()

        size = SymTab.newTemp('int')
        malloc_code += self.gen("*",size,plist[0],alloc_size)

        malloc_code += self.gen("=",i,'0')
        malloc_code += self.gen(loop_block+":")
        malloc_code += self.gen("ifgoto",">=",i,plist[0],after_block)
        malloc_code += self.gen("malloc",tmp,size)
        malloc_code += self.gen("writearray",arr,i,tmp)

        if len(plist)>1:
            malloc_code += self.mallocInLoop(tmp,plist[1:],alloc_size)

        malloc_code += self.gen("+",i,i,"1")
        malloc_code += self.gen("goto",loop_block)
        malloc_code += self.gen(after_block+":")

        return malloc_code

    ## Helper functions =========================================================

    ## program and class=========================================================
    def p_program(self, p):
        '''
            program : program class_declaration
                    | program interface_declaration
                    | program STMT_TERMINATOR
                    | empty
        '''
        self.printParseTree(p)
        if len(p)==3:
            p[0]={'code':p[1]['code']}
            if str(p.slice[2])=='class_declaration' or str(p.slice[2])=='interface_declaration':
                p[0]['code']=p[0]['code']+p[2]['code']
                print(p[2]['code'])
        else:
            p[0]={'code':''}


    def p_class_declaration(self, p):
        '''
            class_declaration : CLASS IDENTIFIER IMPLEMENTS interface_type_list seen_class_decl1 BEGIN class_body_declarations END
                              | CLASS IDENTIFIER seen_class_decl2 BEGIN class_body_declarations END
        '''
        self.printParseTree(p)
        self.stManager.endScope()
        ## TODO: OOP CONCEPT TO BE IMPLEMENTED:
        if len(p)==9:
            p[0]=p[7]
        else:
            p[0]=p[5]

    def p_seen_class_decl1(self,p):
        '''
            seen_class_decl1 :
        '''
        self.printParseTree(p)
        cattr = {
              'name':p[-3]
            , 'interfaces':p[-1]
        }
        self.stManager.beginScope(SymTab.Category.Class, cattr)

    def p_seen_class_decl2(self,p):
        '''
            seen_class_decl2 :
        '''
        self.printParseTree(p)
        cattr = {
              'name':p[-1]
            , 'interfaces':[]
        }
        self.stManager.beginScope(SymTab.Category.Class, cattr)


    def p_interface_type_list(self, p):
        '''
            interface_type_list : interface_type_list COMMA interface_type
                                | interface_type
        '''
        self.printParseTree(p)
        if len(p)==4:
            p[1].append(p[3])
            p[0]=p[1]
        else:
            p[0]=[p[1]]


    def p_class_body_declarations(self, p):
        '''
            class_body_declarations : class_body_declarations class_member_declaration
                                    | class_body_declarations constructor_declaration
                                    | empty
        '''
        self.printParseTree(p)
        p[0] = {'code': ''}
        if len(p) == 2:
            ## TODO :: should I assign place attr
            pass
        else:
            xRule = str(p.slice[2])
            if xRule == 'class_member_declaration':
                p[0]['code']=p[1]['code']+p[2]['code']
                ## TODO :: how the different member code be organised
                pass
            else:
                ## TODO :: constructor case THIS IS AN OOP CONECPT HANDLE later
                p[0]['code']=p[1]['code']+p[2]['code']
                pass


    def p_class_member_declaration(self, p):
        '''
            class_member_declaration : field_declaration
                                     | method_declaration
        '''
        self.printParseTree(p)
        p[0] = p[1]

    ## constructor=========================================================
    def p_constructor_declaration(self, p):
        '''
            constructor_declaration : FUNCTION constructor_declarator constructor_body
        '''
        self.printParseTree(p)
        self.stManager.endScope()
        ## TODO: THIS IS AN OOP CONCEPT HANDLER IT, WHILE MAKING OBJECT
        p[0]={'code':p[3]['code']}

    def p_constructor_declarator(self, p):
        '''
            constructor_declarator : type_name seen_cons_name LPAREN formal_parameter_list RPAREN
                                   | type_name seen_cons_name LPAREN RPAREN
        '''
        self.printParseTree(p)
        if len(p) == 6:
            self.stManager.currentTable.attr['args_types'] = p[4]

    def p_seen_cons_name(self, p):
        '''
            seen_cons_name :
        '''
        ## check if the constructor name matches the class name
        if p[-1] != self.stManager.currentTable.attr['name']:
            raise NameError("Constructor name should be same as that of class")
        mAttr = {
              'name': p[-1]
            , 'args_types': []
        }
        self.stManager.beginScope(SymTab.Category.Function, mAttr)


    def p_constructor_body(self, p):
        '''
            constructor_body : BEGIN block_statement END
                             | BEGIN END
        '''
        self.printParseTree(p)
        p[0] = {'code': ''}
        if len(p) == 4:
            p[0]['code'] = p[2]['code']

    def p_formal_parameter_list(self, p):
        '''
            formal_parameter_list : formal_parameter_list COMMA type variable_declarator_id
                                  | type variable_declarator_id
        '''
        self.printParseTree(p)
        #NOTE p[0] contains the list of types of parameters
        if len(p)==5:
            p[1].append(p[3])
            p[0]=p[1]
        else:
            p[0]=[p[1]]

    def p_field_declaration(self, p):
        '''
            field_declaration : type variable_declarators STMT_TERMINATOR
        '''
        self.printParseTree(p)
        p[0]={'code':''}
        for var in p[2]:
            p[0]['code'] += var['code']

    ## variables
    def p_variable_declarators(self, p):
        '''
            variable_declarators : variable_declarators COMMA variable_declarator
                                 | variable_declarator
        '''
        self.printParseTree(p)
        if len(p) == 2:
            p[0]=[]
            p[0].append(p[1])
        else:
            p[0]=p[1]
            p[0].append(p[3])

    def p_variable_declarator(self, p):
        '''
            variable_declarator : variable_declarator_id
                                | variable_declarator_id EQ variable_initializer
        '''
        self.printParseTree(p)
        if len(p) == 2:
            p[0] = {
                  'place':p[1]
                , 'code':''
            }
        else:
            #TODO TYPE CHECK
            if p[1].type != p[3]['type']:
                ## TODO :: more expressive message
                raise TypeError("Assignments Type Mismatch")
            if p[3]['place']==None or isinstance(p[3]['place'],SymTab.VarType):
                p[0] = {
                      'place':p[1]
                    , 'code':p[3]['code']
                }
            else:
                p[0] = {
                      'place':p[1]
                    , 'code':p[3]['code']+self.gen('=',p[1],p[3]['place'])
                }

    def p_variable_declarator_id(self, p):
        '''
            variable_declarator_id : variable_declarator_id LSQUARE RSQUARE
                                   | IDENTIFIER
        '''
        #NOTE :: p[0] contains symbol table entry of newly inserted IDENTIFIER,
        #        without type and size which will be added later
        #        print("168"+str(p.slice))
        self.printParseTree(p)
        if str(p.slice[1]) == 'variable_declarator_id':
            #TODO
            symEntry = self.stManager.currentTable.lookup(p[1].lexeme) ## would return a varType
            symEntry.updateCategory('ARRAY')
            symEntry.updateType(symEntry.type + "[]")
            p[0] = symEntry
        else:
            ## check for re-declaration of a variable
            idVal = p.slice[1].value
            checkReInitial = self.stManager.currentTable.lookup(idVal)
            if checkReInitial != None:
                raise NameError("Re-declaration of variable.")
            p[0] = self.stManager.insert(idVal, self.recentType, 'SIMPLE')

    def p_variable_initializer(self, p):
        '''
            variable_initializer : expression
                                 | array_initializer_with_curly
                                 | input
        '''
        #TODO check
        self.printParseTree(p)
        xRule = str(p.slice[1])
        if xRule == 'expression':
            p[0] = p[1]
            if(p[1]==None):
                assert(False)
        elif xRule == 'array_initializer_with_curly':
            pass
        elif xRule == 'input':
            xType = p[1][4:].lower()
            temp = SymTab.newTemp(xType)
            p[0] = {
                  'place': temp
                , 'type': xType
                , 'code': self.gen(p[1], temp)
            }

    def p_input(self, p):
        '''
            input : READINT LPAREN RPAREN
                  | READREAL LPAREN RPAREN
                  | READSTRING LPAREN RPAREN
        '''
        self.printParseTree(p)
        p[0] = self.gen(p.slice[1].value)

    def p_array_initializer_with_curly(self, p):
        '''
            array_initializer_with_curly : LCURLY array_initializer_without_curly RCURLY
                                         | LCURLY RCURLY

        '''
        self.printParseTree(p)

    def p_array_initializer_without_curly(self, p):
        '''
            array_initializer_without_curly : array_initializer_without_curly COMMA variable_initializer
                                            | variable_initializer
        '''
        self.printParseTree(p)

    ## methods=========================================================
    def p_method_declaration(self, p):
        '''
            method_declaration : method_header method_body
        '''
        self.printParseTree(p)
        curFunction = self.stManager.currentTable.attr['name']
        xCode = p[2]['code']

        ## return statement check
        hasReturnEnd = xCode.rfind('\n')
        if hasReturnEnd != -1:
            hasReturnStart = xCode.rfind('\n',0,hasReturnEnd)
            hasReturnStart += 1
            parts = xCode[hasReturnStart:hasReturnEnd].split(',')
            if parts[0] == 'return':
                ## we are fine
                pass
            else:
                #  user is missing specifying the return type
                raise TypeError("End return statement for the function missing")
        else:
            raise TypeError("End return statement for the function missing")

        p[0] = {
            'code' : self.gen("function", curFunction) +
                     xCode + "\n"
        }
        self.stManager.endScope()

    def p_method_header(self, p):
        '''
            method_header : FUNCTION DCOLON result_type method_declarator
        '''
        self.printParseTree(p)

    def p_result_type(self, p):
        '''
            result_type : type
                        | VOID
        '''
        self.printParseTree(p)
        if str(p.slice[1]) == 'type':
            p[0] = p[1]
        else:
            p[0] = p.slice[1].value

    def p_method_declarator(self, p):
        '''
            method_declarator : IDENTIFIER seen_method_name LPAREN formal_parameter_list RPAREN
                              | IDENTIFIER seen_method_name LPAREN RPAREN
        '''
        self.printParseTree(p)
        if len(p) == 6:
            self.stManager.currentTable.attr['args_types'] = p[4]

    def p_seen_method_name(self, p):
        '''
            seen_method_name :
        '''
        symEntry = self.stManager.currentTable.lookup(p[-1])
        if symEntry != None:
            raise NameError("Duplicate Function name")

        mAttr = {
            'type':p[-2]
            ,'name':p[-1]
            ,'args_types':[]
        }
        self.stManager.beginScope(SymTab.Category.Function, mAttr)


    def p_method_body(self, p):
        '''
            method_body : block
                        | STMT_TERMINATOR
        '''
        self.printParseTree(p)
        if str(p.slice[1]) == 'block':
            p[0] = {
                'code': p[1]['code']
            }
        else:
            p[0] = { 'code': ''}

    ## interfaces=========================================================
    def p_interface_declaration(self, p):
        '''
            interface_declaration : INTERFACE IDENTIFIER seen_interface_name interface_body
        '''
        self.stManager.endScope()
        self.printParseTree(p)

    def p_seen_interface_name(self, p):
        '''
            seen_interface_name :
        '''
        symEntry = self.stManager.currentTable.lookup(p[-1])
        if symEntry != None:
            raise NameError("Duplicate Interface name")
        iAttr = {
              'name': p[-1]
        }
        self.stManager.beginScope(SymTab.Category.Interface, iAttr)

    def p_interface_body(self, p):
        '''
            interface_body : BEGIN interface_member_declarations END
                           | BEGIN END
        '''
        self.printParseTree(p)

    def p_interface_member_declarations(self, p):
        '''
            interface_member_declarations : interface_member_declarations interface_member_declaration
                                          | interface_member_declaration
        '''
        self.printParseTree(p)

    def p_interface_member_declaration(self, p):
        '''
            interface_member_declaration : method_header STMT_TERMINATOR
        '''
        self.printParseTree(p)

    ## types=========================================================
    def p_type(self, p):
        '''
            type : primitive_type
                 | reference_type
        '''
        self.printParseTree(p)
        self.recentType = p[1]
        if str(p.slice[1])=='primitive_type':
           p[0]=p[1]
        elif str(p.slice[1])=='reference_type':
            #TODO
            pass

    def p_primitive_type(self, p):
        '''
            primitive_type : INT
                           | REAL
                           | BOOLEAN
                           | STRING
        '''
        self.printParseTree(p)
        p[0] = p.slice[1].value

    def p_reference_type(self, p):
        '''
            reference_type : class_type
                           | array_type
        '''
        self.printParseTree(p)
        p[0] = p[1]

    def p_class_type(self, p):
        '''
            class_type : type_name
        '''
        self.printParseTree(p)
        p[0] = p[1]

    def p_interface_type(self, p):
        '''
            interface_type : type_name
        '''
        self.printParseTree(p)
        p[0] = p[1]

    def p_array_type(self, p):
        '''
            array_type : type LSQUARE RSQUARE
        '''
        self.printParseTree(p)

    ## block statements=========================================================
    def p_block(self, p):
        '''
            block : BEGIN block_statements END
                  | BEGIN END
        '''
        self.printParseTree(p)
        if len(p)==4:
            p[0]={'code':p[2]['code']}
        else:
            p[0]={'code':''}

    def p_block_statements(self, p):
        '''
            block_statements : block_statements block_statement
                             | block_statement
        '''
        self.printParseTree(p)
        if len(p)==3:
            p[1]['code'] += p[2]['code']
            p[0] = p[1]
        else:
            p[0]={
                'code':p[1]['code']
            }

    def p_block_statement(self, p):
        '''
            block_statement : local_variable_declaration STMT_TERMINATOR
                            | statement
        '''
        self.printParseTree(p)
        p[0]={
            'code': p[1]['code']
        }

    def p_local_variable_declaration(self, p):
        '''
            local_variable_declaration : type variable_declarators
        '''
        self.printParseTree(p)
        p[0] = {'code': ''}
        for i in p[2]:
           p[0]['code'] += i['code']

    def p_statement(self, p):
        '''
            statement : block
                      | statement_expression STMT_TERMINATOR
                      | break_statement
                      | continue_statement
                      | return_statement
                      | if_then_else_statement
                      | while_statement
                      | for_statement
                      | print_statement
        '''
        self.printParseTree(p)
        p[0] = {
            'code': p[1]['code']
        }

    def p_print_statement(self, p):
        '''
            print_statement : PRINT LPAREN expression RPAREN STMT_TERMINATOR
        '''
        self.printParseTree(p)
        p[0] = {
            'code': p[3]['code'] + self.gen("print", p[3]['place'])
        }

    def p_statement_expression(self, p):
        '''
            statement_expression : assignment
                                 | method_invocation
                                 | class_instance_creation_expression
        '''
        self.printParseTree(p)
        #TODO check
        p[0] = p[1]

    def p_seenif_for_while(self,p):
        '''
            seenif_for_while :
        '''
        self.stManager.beginScope(SymTab.Category.Block, {'name':p[-1]})
        if str(p[-1])!='if':
            update_block=self.stManager.newLabel()
            after_block=self.stManager.newLabel()
            self.stManager.insert('`update_block',update_block,None)
            self.stManager.insert('`after_block',after_block,None)

    def p_if_then_else_statement(self, p):
        '''
            if_then_else_statement : IF seenif_for_while LPAREN expression RPAREN THEN block_statements ELSE block_statements END
                                   | IF seenif_for_while LPAREN expression RPAREN THEN block_statements END
        '''
        self.printParseTree(p)
        p[0] = {
            'code':''
        }
        tstr=''
        if p[4]['type'] != 'boolean':
            raise TypeError("Error at line No. %d :: Expression inside if must be of type boolean !!! \n"%(p.lexer.lineno,))
        if len(p) == 11:
            false_block=self.stManager.newLabel()
            after_block=self.stManager.newLabel()
            tstr += p[4]['code']
            tstr += self.gen('ifgoto','==',p[4]['place'],'false',false_block)
            tstr += p[7]['code']
            tstr += self.gen('goto',after_block)
            tstr += self.gen(false_block+":")
            tstr += p[9]['code']
            tstr += self.gen(after_block+":")
        else:
            after_block=self.stManager.newLabel()
            tstr += p[4]['code']
            tstr += self.gen('ifgoto','==',p[4]['place'],'false',after_block)
            tstr += p[7]['code']
            tstr += self.gen(after_block+":")

        p[0]['code']=p[0]['code']+tstr
        self.stManager.endScope()

    def p_while_statement(self, p):
        '''
            while_statement : WHILE seenif_for_while LPAREN expression RPAREN block
        '''
        #TODO, IMPLEMENTATION OF BREAK OR CONTINUE:???? WE NEED TO STORE after_block and loop_block labels in SymTabl entry for for loop
        self.printParseTree(p)
        update_block = self.stManager.lookup('`lookup_block').type
        loop_block = update_block
        after_block = self.stManager.lookup('`after_block').type
        if p[4]['type']!='boolean':
            raise TypeError("Error at line No. %d :: while expression must be of type boolean !!! \n"%(p.lexer.lineno,))
        tstr += p[4]['code']
        tstr += self.gen(loop_block+":")
        tstr += self.gen('ifgoto','==',p[4]['place'],'false',after_block)
        tstr += p[6]['code']
        tstr += self.gen('goto',loop_block)
        tstr += self.gen(after_block+":")
        self.stManager.endScope()

    def p_for_statement(self, p):
        '''
            for_statement : FOR seenif_for_while LPAREN for_init STMT_TERMINATOR expression STMT_TERMINATOR for_update RPAREN block
                          | FOR seenif_for_while LPAREN for_init STMT_TERMINATOR STMT_TERMINATOR for_update RPAREN block
        '''
        self.printParseTree(p)
        update_block = self.stManager.lookup('`update_block').type
        after_block = self.stManager.lookup('`after_block').type
        loop_block = self.stManager.newLabel()
        p[0]={'code':''}
        tstr=''
        #TODO, IMPLEMENTATION OF BREAK OR CONTINUE:???? WE NEED TO STORE after_block and loop_block labels in SymTabl entry for for loop
        if len(p)==11:
            #TODO, BELOW CHECK IS TEMPORARY COMMENTED, COMPLETE THE TYPE CHECKING EXPRESSION RULE, THEN UNCOMMENT THIS
            #if p[5]['type']!='boolean':
            #    raise TypeError("Error at line No. %d :: for expression must be of type boolean !!! \n"%(p.lexer.lineno,))
            tstr += p[4]['code']
            tstr += self.gen(loop_block+":")
            tstr += p[6]['code']
            tstr += self.gen('ifgoto','==',p[6]['place'],'false',after_block)
            tstr += p[10]['code']
            tstr += self.gen(update_block+":")
            tstr += p[8]['code']
            tstr += self.gen('goto',loop_block)
            tstr += self.gen(after_block+":")
        else:
            after_block=self.stManager.newLabel()
            loop_block=self.stManager.newLabel()
            tstr += p[4]['code']
            tstr += self.gen(loop_block+":")
            tstr += p[9]['code']
            tstr += self.gen(update_block+":")
            tstr += p[7]['code']
            tstr += self.gen('goto',loop_block)
            tstr += self.gen(after_block+":")
        p[0]['code']=tstr
        self.stManager.endScope()

    def p_statement_expressions(self, p):
        '''
            statement_expressions : statement_expressions COMMA statement_expression
                                  | statement_expression
        '''
        #NOTE p[1]['code'] or p[3]['code'] MUST NOT HAVE A MEANINGFUL SEMICOLON
        self.printParseTree(p)
        p[0]={'code':''}
        if len(p)==4:
            p[0]['code']=p[1]['code']+p[3]['code']
        else:
            p[0]['code']=p[1]['code']

    def p_for_init(self, p):
        '''
            for_init : statement_expressions
                     | local_variable_declaration
                     | empty
        '''
        self.printParseTree(p)
        p[0] = {'code':''}
        p[0]['code'] = p[1]['code']

    def p_for_update(self, p):
        '''
            for_update : statement_expressions
                       | empty
        '''
        self.printParseTree(p)
        p[0] = {'code':''}
        p[0]['code'] = p[1]['code']

    def p_break_statement(self, p):
        '''
            break_statement : BREAK STMT_TERMINATOR
        '''
        self.printParseTree(p)
        #TODO LOOK AT #TODO OF FOR LOOP
        p[0]={
            'code':self.gen('goto',self.stManager.lookup('`after_block').type)
        }

    def p_continue_statement(self, p):
        '''
            continue_statement : CONTINUE STMT_TERMINATOR
        '''
        self.printParseTree(p)
        p[0] = {
            'code':self.gen('goto',self.stManager.lookup('`update_block').type)
        }
        #TODO LOOK AT #TODO OF FOR LOOP

    def p_return_statement(self, p):
        '''
            return_statement : RETURN expression STMT_TERMINATOR
                             | RETURN STMT_TERMINATOR
        '''
        self.printParseTree(p)
        ## check for return type of the statement to be same as the
        ## the method return type
        if len(p) == 3:
            retX = self.returnTypeCheck('void', self.stManager.currentTable)
            ## TODO :: Print more expressiv error msg
            assert (retX),"Invalid return type"
            p[0] = {
                'code' : self.gen("return")
            }
        else:
            retX = self.returnTypeCheck(p[2]['type'], self.stManager.currentTable)
            ## TODO :: Print more expressiv error msg
            assert (retX),"Invalid return type"
            p[0] = {
                'code' : p[2]['code'] + self.gen("return", str(p[2]['place']))
            }

    def p_expression(self, p):
        '''
            expression : expression MULTIPLY expression
                       | expression PLUS expression
                       | expression MINUS expression
                       | expression DIVIDE expression
                       | expression MODULUS expression
                       | expression LSHIFT expression
                       | expression RSHIFT expression
                       | expression LT expression
                       | expression LE expression
                       | expression GT expression
                       | expression GE expression
                       | expression EQEQ expression
                       | expression NTEQ expression
                       | expression AND expression
                       | expression OR expression
                       | expression BIT_XOR expression
                       | expression BIT_OR expression
                       | expression BIT_AND expression
                       | unaryop expression
                       | assignment
                       | primary
                       | identifier_name_with_dot
                       | IDENTIFIER

        '''
        #NOTE, FOR EVERY CASE check if p[-1] is NOT NOne, if so, then choose p[-2] as E['place']
        self.printParseTree(p)
        p1 = str(p.slice[1])

        if p1 == 'primary':
            p[0] = p[1]
            if p[1]==None:
                assert(False)

        elif len(p) == 4:
            res = self.typeHandler(p[1], p[3], p.slice[2].type)
            ## TODO :: SHORT CIRCUIT BOOLEAN 'AND' AND 'OR'
            if p[-1] != '=':
                temp = SymTab.newTemp(res['type'])
                p[0] = {
                     'place': temp
                    ,'type': res['type']
                    ,'code': p[1]['code'] + p[3]['code'] +
                             self.gen(p.slice[2].value, temp, res['value1'], res['value2'])
                }
            else:
                p[0] = {
                     'place': p[-2]
                    ,'type': p[-2].type
                    ,'code': p[1]['code'] + p[3]['code'] +
                             self.gen(p.slice[2].value, p[-2], res['value1'], res['value2'])
                }

        elif len(p) == 3:
            ## case of unaryop
            res = self.typeHandler(p[2], None, p.slice[1].type)
            temp = SymTab.newTemp(res['type'])
            if p[-1]!='=':
                temp = SymTab.newTemp(res['type'])
                p[0] = {
                     'place': temp
                    ,'type': res['type']
                    ,'code': p[2]['code'] + self.gen(p[1], temp, p[2]['place'])
                }
            else:
                p[0] = {
                     'place': p[-2]
                    ,'type': p[-2].type
                    ,'code': p[2]['code'] + self.gen(p[1], p[-2], p[2]['place'])
                }

        elif p1 == 'assignment':
            if str(type(p[1]))=="<class 'dict'>":
                if 'specialForArrayWrite' in p[1].keys():
                    p[0] = p[1]
                    xKey = p[1]['specialForArrayWrite']
                    tmpk = SymTab.newTemp(str(xKey['place'].type)[:len(str(xKey['place'].type))-2])
                    p[0]['code'] = p[0]['code'] + self.gen("readarray"
                                            ,p[1]['specialForArrayWrite']['place']
                                            ,p[1]['specialForArrayWrite']['index']
                                            ,tmpk)
                    p[0]['place'] = tmpk
                else:
                    p[0] = p[1]
            else:
                p[0] = p[1]

        elif p1 == 'identifier_name_with_dot':
            #TODO AS A OOP CONCEPT
            pass

        else:
            ## case of IDENTIFIER
            #TODO for below do I need to separate expression and IDENTIFIER?   yesss
            #TODO Remove below dummy values
            symEntry = self.stManager.lookup(p.slice[1].value)
            if symEntry == None:
                ## TODO, make the error more expressive
                raise NameError('Undefined variable %s at line %d\n' %(p.slice[1].value, p.lexer.lineno))
            p[0] = {
                 'place': symEntry
                ,'code' : ''
                ,'type' : symEntry.type
            }
        #NOTE THIS IS IMPORTANT DO NOT REMOVE This
        # print("--------00000000000000000000")

    def p_unaryop(self, p):
        '''
            unaryop : MINUS
                    | NOT
        '''
        self.printParseTree(p)
        p[0]=p.slice[1].value;

    def p_assignment(self, p):
        '''
            assignment : left_hand_side EQ expression
        '''
        ## TODO DO TYPE CHECK HERE
        self.printParseTree(p)
        if isinstance(p[1],SymTab.VarType):
            if p[1].type != p[3]['type']:
                raise TypeError("Type Mismatch on Assignments")
            p[0] = {
                  'place': p[1]
                , 'type': p[1].type
                , 'code': p[3]['code']+self.gen("=",p[1],p[3]['place'])
            }
        else:
            ## TODO, THIS MUST ONLY BE FOR ARRAYS
            p[0] = {
                  'place': p[1]['place']
                , 'type': p[1]['place'].type
                , 'code': p[1]['specialForArrayWrite']['code'] + 
                          p[3]['code'] + 
                          self.gen('writearray'
                                   ,p[1]['specialForArrayWrite']['place']
                                   ,p[1]['specialForArrayWrite']['index']
                                   ,p[3]['place'])
                , 'specialForArrayWrite': p[1]['specialForArrayWrite']
            }

    def p_left_hand_side(self, p):
        '''
            left_hand_side : identifier_name_with_dot
                           | IDENTIFIER
                           | field_access
                           | array_access
        '''
        ## ASSUMPTION, IF P[0] is not null, then it should be symbol table entry
        ## TODO REMOVE REDUDANT EXPRESSIONS OF THE FORM , `t0 = x,  y = `t0   for expression like y=x, particularly in header of for loop
        ## NOTE p[0] is a symbol table entry
        self.printParseTree(p)
        x = str(p.slice[1])
        if x == 'identifier_name_with_dot':
            pass
        elif x == 'field_access':
            pass
        elif x == 'array_access':
            p[0]=p[1]
            pass
        else:
            symEntry = self.stManager.lookup(p.slice[1].value)
            p[0] = symEntry

    def p_method_invocation(self, p):
        '''
            method_invocation : identifier_name_with_dot LPAREN argument_list RPAREN
                              | IDENTIFIER LPAREN argument_list RPAREN
                              | identifier_name_with_dot LPAREN RPAREN
                              | IDENTIFIER LPAREN RPAREN
                              | field_access LPAREN argument_list RPAREN
                              | field_access LPAREN RPAREN

        '''
        self.printParseTree(p)
        xRule = str(p.slice[1])
        if xRule == "identifier_name_with_dot":
            pass
        elif xRule == "field_access":
            pass
        else:
            funcID = p.slice[1].value
            symEntry = self.stManager.lookup(funcID)
            if symEntry == None:
                raise NameError("Function not defined")
            temp = SymTab.newTemp(symEntry.attr['type'])
            param_code=''
            if len(p)==5:
                param_code=p[3]['code']
                for k in p[3]['place']:
                    param_code+=self.gen("param",k)
            p[0] = {
                  'place': temp
                , 'type': temp.type
                , 'code': param_code+self.gen('call', funcID, temp)
            }

    def p_field_access(self, p):
        '''
            field_access : primary DOT IDENTIFIER
        '''
        ## TODO: comes under domain of oops
        self.printParseTree(p)

    def p_primary(self, p):
        '''
            primary : primary_no_new_array
                    | array_creation_expression
        '''
        self.printParseTree(p)
        p[0] = p[1]
        if p[1]==None:
            assert(False)

    def p_primary_no_new_array(self, p):
        '''
            primary_no_new_array : literal
                                 | LPAREN expression RPAREN
                                 | class_instance_creation_expression
                                 | field_access
                                 | method_invocation
                                 | array_access
        '''
        self.printParseTree(p)
        #CONTINUE FROM HERE
        if str(p.slice[1]) in ['literal', 'method_invocation','array_access']:
            p[0] = p[1]
        elif len(p) == 4:
            p[0] = p[2]
        else:
            ## TODO ::COMES INSDIDE DOMAINS OF OOP
            pass

    def p_class_instance_creation_expression(self, p):
        '''
            class_instance_creation_expression : NEW class_type LPAREN argument_list RPAREN
                                               | NEW class_type LPAREN RPAREN
        '''
        self.printParseTree(p)

    def p_argument_list(self, p):
        '''
            argument_list : argument_list COMMA expression
                          | expression
        '''
        self.printParseTree(p)
        if len(p)==4:
            p[1]['place'].append(p[3]['place'])
            p[0] = {
                'code':p[1]['code']+p[3]['code']
                ,'place':p[1]['place']
            }
        else:
            p[0] = {
                'code':p[1]['code']
                ,'place':[p[1]['place']]
            }


    def p_array_creation_expression(self, p):
        '''
            array_creation_expression : NEW primitive_type dim_exprs dims
                                      | NEW class_type dim_exprs dims
        '''
        self.printParseTree(p)
        p[0] = {'type':''}

        if str(p[-1]) == '=':
            ## TODO type match checking and dimension match checking
            if isinstance(p[-2], SymTab.VarType):
                access_code = ''
                a = p[-2] # for type int a[]=new int[];
            elif isinstance(p[-2], dict):
                ## lhs is an array access
                a = p[-2]['specialForArrayWrite']['place']
                access_code = p[-2]['specialForArrayWrite']['code']
                index = p[-2]['specialForArrayWrite']['index']
            else:
                assert(False)

            pos = str(a.type).find("[]")
            if pos == -1:
                ndims=0
            else:
                ndims=(len(a.type)-pos)/2

            if access_code != '':
                ndims-=1

            if p[3]['count'] + p[4] != ndims:
                raise ValueError("Array Dimension Mismatch at array initilization at line %d"%(p.lexer.lineno))

            ## TODO, GENERATE IR MEM ALLOCATION FOR ARRAYS' like "malloc, a, <size in bytes>"
            if str(p.slice[2]) == "primitive_type":
                if (a.type)[:pos] != p.slice[2].value:
                    raise TypeError("Type Mismatch at at array initilization line %d"%(p.lexer.lineno))
                else:
                    ## NOTE, ARRAY IS IMPLEMENTED AS LINKED LIST
                    ## EX. int a[][][]=new int [2][3][]; 
                    ## then Malloc has reserved 2*3=6 space for elements of type int[],
                    ## TODO CHANGE OTHER THINGS TO BE CONSISTENT WITH THIS DEFINITION OF SIZE FOR ARRAYS
                    a.size = {
                        'valuedDimensions':p[3]['place']
                        ,'numUnvaluedDimensions':p[4]
                    }
                    malloc_code = ''
                    tmp = None
                    if (a.type)[:pos] != "String":
                            size = SymTab.newTemp('int')
                            malloc_code += self.gen("*", size, p[3]['place'][0], SymTab.typeSizeMap[str(a.type[:pos])])
                            if access_code=='':
                                malloc_code += self.gen("malloc",a,size)
                            else:
                                tmp = SymTab.newTemp(str(a.type)[:len(str(a.type))-2])
                                malloc_code += self.gen("malloc", tmp, size)
                            if len(p[3]['place'])>1:
                                malloc_code += self.mallocInLoop(a, p[3]['place'][1:], SymTab.typeSizeMap[str(a.type[:pos])])
                    else:
                        #TODO handle the case for String separately
                        pass

                    p[0]['type'] = str(a.type)
                    p[0]['code'] = p[3]['code'] + malloc_code
                    p[0]['place'] = tmp
            else:
                ## TODO: class instance array creation
                pass

    def p_dim_exprs(self, p):
        '''
            dim_exprs : dim_exprs dim_expr
                      | empty
        '''
        self.printParseTree(p)
        if len(p)==3:
            p[1]['place'].append(p[2]['place'])
            p[0] = {
                'count': 1 + p[1]['count']
                ,'place': p[1]['place']
                ,'code': p[1]['code'] + p[2]['code']
            }
        else:
            p[0] = {
                'count':0
                ,'place':[]
                ,'code':''
            }

    def p_dim_expr(self, p):
        '''
            dim_expr : LSQUARE expression RSQUARE
        '''
        self.printParseTree(p)
        p[0] = {
            'count':1
            ,'place':p[2]['place']
            ,'code':p[2]['code']
        }

    def p_dims(self, p):
        '''
            dims : LSQUARE RSQUARE dims
                 | empty
        '''
        self.printParseTree(p)
        # STORE COUNT
        if len(p)==2:
            p[0] = 0
        else:
            p[0] = p[3] + 1

    def p_array_access(self, p):
        '''
            array_access : identifier_name_with_dot LSQUARE expression RSQUARE
                         | IDENTIFIER LSQUARE expression RSQUARE
                         | primary_no_new_array LSQUARE expression RSQUARE
        '''
        #NOTE NOTE NOTE STRICT ASSUMPTION #RULE
        #IF ARRAY DELCLARATION IF OF TYPE
        self.printParseTree(p)
        xRule = str(p.slice[1])

        if xRule == 'identifier_name_with_dot':
            pass

        elif xRule == 'primary_no_new_array':
            arr=p[1]['place']
            tmp=SymTab.newTemp(str(arr.type)[:len(str(arr.type))-2])
            p[0]={
                'type':str(arr.type)[:len(str(arr.type))-2]
                ,'place':tmp
                ,'code':p[1]['code']+p[3]['code'] + 
                        self.gen("readarray",arr,p[3]['place'],tmp)
                ,'specialForArrayWrite':{
                    'code': p[1]['code']+p[3]['code']
                    ,'place':arr
                    ,'index':p[3]['place']
                }
            }

        else:
            ## IDENTIFIER [exp] case
            ## TODO WORKOUT IN CODEGEN AS NOW INDEX CAN ALSO BE SYMBOL TALBE ENTRIES
            arr=self.stManager.lookup(p[1])
            typ = str(arr.type)[:len(str(arr.type))-2]
            tmp=SymTab.newTemp(typ)
            p[0]={
                'type':typ
                ,'place':tmp
                ,'code':p[3]['code'] +
                        self.gen("readarray",arr,p[3]['place'],tmp)
                ,'specialForArrayWrite':{
                    'code':p[3]['code']
                    ,'place':arr
                    ,'index':p[3]['place']
                }
            }

    def p_type_name(self, p):
        '''
            type_name : IDENTIFIER
        '''
        self.printParseTree(p)
        p[0] = p.slice[1].value

    def p_identifier_name_with_dot(self, p):
        '''
            identifier_name_with_dot : identifier_name_with_dot DOT IDENTIFIER
                                     | IDENTIFIER DOT identifier_one_step
        '''
        self.printParseTree(p)
        if str(p.slice[1]) == "identifier_name_with_dot":
            p[0] = p[1] + '.' + p.slice[3].value
        else:
            p[0] = p.slice[1].value + '.' + p[3]


    def p_identifier_one_step(self,p):
        '''
            identifier_one_step : IDENTIFIER
        '''
        self.printParseTree(p)
        p[0] = p.slice[1].value

    def p_literal(self, p):
        '''
            literal : INTEGER_LITERAL
                    | FLOAT_LITERAL
                    | BOOLEAN_LITERAL
                    | STRING_LITERAL
                    | NIL
        '''
        self.printParseTree(p)
        tp = str(p.slice[1].type)
        if tp == 'INTEGER_LITERAL':
            p[0]={
                  'type': 'int'
                , 'place': p.slice[1].value
                , 'code': ''
            }

        elif tp == 'FLOAT_LITERAL':
            p[0]={
                  'type': 'real'
                , 'place': p.slice[1].value
                , 'code': ''
            }

        elif tp == 'BOOLEAN_LITERAL':
            p[0]={
                  'type': 'boolean'
                , 'place': p.slice[1].value
                , 'code': ''
            }

        elif tp == 'STRING_LITERAL':
            p[0]={
                  'type': 'String'
                , 'place': p.slice[1].value
                , 'code': ''
            }

        elif tp == 'NIL':
            #FIXME what to do of this case
            # -- Follow up --
            # Nil is not a type but a value which is not initialized yet
            # Similar to Java's null
            # https://stackoverflow.com/questions/2707322/what-is-null-in-java
            p[0]={
                  'type': 'nil'
                , 'place': p.slice[1].value
                , 'code': ''
            }

    ## empty
    def p_empty(self, p):
        '''
            empty :
        '''
        p[0]={'code':''}

    def p_error(self, p):
        print('\n-------------------------------------------------------')
        print('Error: \'{}\' at line no: {}'.format(p.value, p.lineno))

        if len(argv) == 2:
            filename = argv[1]
        elif len(argv) == 3:
            filename = argv[2]

        with open(filename,'r') as fp:
            for i, line in enumerate(fp):
                if i+1 == p.lineno:
                    print("\t\t\tin {}".format(line.strip(),))
        print('-------------------------------------------------------\n')
        exit(EXIT_FAILURE)


class Parser(object):

    def __init__(self):
        self.lexer = lex.lex(module=MyLexer())
        self.parserObj = MyParser(self.lexer)
        self.parser = yacc.yacc(module=self.parserObj, start='program')

    def read_file(self, _file):
        if type(_file) == str:
            _file = open(_file)
        content = _file.read()
        _file.close()
        return content

    def tokenize_string(self, code):
        self.lexer.input(code)
        for token in self.lexer:
            print(token)

    def tokenize_file(self, _file):
        content = self.read_file(_file)
        return self.tokenize_string(content)

    def parse_string(self, code, debug=False, lineno=1):
        return self.parser.parse(code, lexer=self.lexer, debug=debug)

    def parse_file(self, _file, debug=False):
        content = self.read_file(_file)
        parse_ret = self.parse_string(content, debug=debug)
        return parse_ret


def handle_errors(argv):
    fileIndex = -1

    if len(argv) == 2:
        fileIndex = 1
    elif len(argv) == 3:
        fileIndex = 2

    if fileIndex > -1:

        if fileIndex == 2:
            if argv[1] not in ['-l', '-p']:
                print('No such option \'{}\''.format(argv[1]))
                exit(EXIT_FAILURE)

        if argv[fileIndex].find('.lua') == -1:
            print('\'{}\' is not a .lua file'.format(argv[fileIndex]))
            exit(EXIT_FAILURE)

        elif not os.path.isfile(argv[fileIndex]):
            print('file \'{}\' does not exists'.format(argv[fileIndex]))
            exit(EXIT_FAILURE)

    else:
        print('To run script: src/parser.py [mode] <path_to_file> ')
        exit(EXIT_FAILURE)


if __name__=="__main__":
    # initialize Parser
    parser = Parser()
    handle_errors(argv)
    ## NOTE :: expTypeMap entry has value
    ##         (possible types input, ..., expected return type)
    ##         if return type is None, return the most closet input type
    expTypeMap = {
          'MULTIPLY': ('int', 'real', None)
        , 'PLUS': ('int', 'real', None)
        , 'MINUS': ('int', 'real', None)
        , 'DIVIDE': ('int', 'real', None)
        , 'LSHIFT': ('int', 'int')
        , 'RSHIFT': ('int', 'int')
        , 'LT': ('int', 'boolean')
        , 'LE': ('int', 'boolean')
        , 'GT': ('int', 'boolean')
        , 'GE': ('int', 'boolean')
        , 'EQEQ': ('int', 'real', 'boolean')
        , 'NTEQ': ('int', 'real', 'boolean')
        , 'AND': ('boolean', 'boolean')
        , 'OR': ('boolean', 'boolean')
        , 'BIT_OR': ('int', 'int')
        , 'BIT_AND': ('int', 'int')
        , 'BIT_XOR': ('int', 'int')
        , 'NOT' : ('boolean', 'boolean')
    }

    # for Tokenizing a file
    if argv[1] == '-l':
        parser.tokenize_file(argv[2])
        exit()

    else:
        if argv[1] == '-p':
            filename = argv[2]
        else:
            filename = argv[1]

        result = parser.parse_file(filename, debug = False)
