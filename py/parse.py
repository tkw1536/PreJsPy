"""
(c) Tom Wiesing 2016, licensed under MIT license
This code is heavily based on the JavaScript version JSEP
The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT
"""
class PreJsPy(object):
    """
    Represents a single instance of a PreJSPyParser
    """
    
    # CONSTANTS -- these should not be fixed
    COMPOUND = 'Compound'
    IDENTIFIER = 'Identifier'
    MEMBER_EXP = 'MemberExpression'
    LITERAL = 'Literal'
    THIS_EXP = 'ThisExpression'
    CALL_EXP = 'CallExpression'
    UNARY_EXP = 'UnaryExpression'
    BINARY_EXP = 'BinaryExpression'
    LOGICAL_EXP = 'LogicalExpression'
    CONDITIONAL_EXP = 'ConditionalExpression'
    ARRAY_EXP = 'ArrayExpression'

    PERIOD_CODE = 46 # '.'
    COMMA_CODE  = 44 # ','
    SQUOTE_CODE = 39 # single quote
    DQUOTE_CODE = 34 # double quotes
    OPAREN_CODE = 40 # (
    CPAREN_CODE = 41 # )
    OBRACK_CODE = 91 # [
    CBRACK_CODE = 93 # ]
    QUMARK_CODE = 63 # ?
    SEMCOL_CODE = 59 # ;
    COLON_CODE  = 58 # :

    @staticmethod
    def __throw_error(msg, index):
        """Private function used to throw an error message"""
        msg = '%s at character %d' % (msg, index)
        raise Error(msg)
    
    def __init__(self):
        """
        Creates a new PreJSPyParser instance. 
        """
        
        # Literals
        # ----------
        # Store the values to return for the various literals we may encounter
        
        # constants
        self.constants = {
            'true': True,
            'false': False,
            'null': None
        }
        
        # Except for `this`, which is special. This could be changed to something like `'self'` as well
        self.this = 'this'
        
        # OPERATORS
            
        # Use a quickly-accessible map to store all of the unary operators
        # Values are set to `true` (it really doesn't matter)
        self.unary_ops = ['-', '!', '~', '+']

        # Also use a map for the binary operations but set their values to their
        # binary precedence for quick reference:
        # see [Order of operations](http://en.wikipedia.org/wiki/Order_of_operations#Programming_language)
        self.binary_ops = {
            '||': 1, '&&': 2, '|': 3,  '^': 4,  '&': 5,
            '==': 6, '!=': 6, '===': 6, '!==': 6,
            '<': 7,  '>': 7,  '<=': 7,  '>=': 7,
            '<<':8,  '>>': 8, '>>>': 8,
            '+': 9, '-': 9,
            '*': 10, '/': 10, '%': 10
        }
    
    # PROPERTY SETTERS / GETTERS
    
    @property
    def unary_ops(self):
        return self.__unary_ops
    
    @unary_ops.setter
    def unary_ops(self, ary):
        self.__unary_ops = ary
        self.__max_uops_len = max(map(len, ary))
        return ary
    
    @property
    def max_unop_len(self):
        return self.__max_uops_len
    
    @property
    def binary_ops(self):
        return self.__binary_ops
    
    @binary_ops.setter
    def binary_ops(self, d):
        self.__binary_ops = d
        self.__max_binop_len = max(map(len, d.keys()))
        return d
    
    @property
    def max_binop_len(self):
        return self.__max_binop_len
    
    @property
    def constants(self):
        return self.__constants
    
    @constants.setter
    def constants(self, d):
        self.__constants = d
        return d
    
    @property
    def this(self):
        return self.__this
    
    @this.setter
    def this(self, s):
        self.__this = s
        return s
    
    #
    # HELPERS
    #
    
    def __binaryPrecedence(self, op_val):
        """ Returns the precedence of a binary operator or `0` if it isn't a binary operator.  """
        if op_val in self.binary_ops.keys():
            return self.binary_ops[op_val]
        else:
            return 0

    
    def __createBinaryExpression(self, operator, left, right):
        """
            Utility function (gets called from multiple places)
            Also note that `a && b` and `a || b` are *logical* expressions, not binary expressions
        """
        tp = PreJsPy.LOGICAL_EXP if (operator == '||' or operator == '&&') else PreJsPy.BINARY_EXP;
        return {
            'type': tp,
            'operator': operator,
            'left': left,
            'right': right
        }
    
    def __isDecimalDigit(self, ch):
        """
        Checks if a character is a decimal digit
        """
        return (ch >= 48 and ch <= 57) # 0...9

    def __isIdentifierStart(self, ch):
        """ Checks if a character is the start of an identifier """
        return (ch == 36) or (ch == 95) or (ch >= 65 and ch <= 90) or  (ch >= 97 and ch <= 122)
        # '$', A..Z and a..z

    def __isIdentifierPart(self, ch):
        """ Checks if a character is part of an identifier """
        return (ch == 36) or (ch == 95) or (ch >= 65 and ch <= 90) or (ch >= 97 and ch <= 122) or (ch >= 48 and ch <= 57)
        # `$`,  `_`, A...Z, a...z and 0...9
    
    def __call__(self, expr):
        return self.parse(expr)
    
    def parse(self, expr):
        """
        Parses an expression expr into a parse tree
        """
        
        # `index` stores the character number we are currently at while `length` is a constant
        # All of the gobbles below will modify `index` as we move along
        state = {'index': 0}
        
        
        def exprI(i):
            try:
                return expr[i]
            except IndexError:
                return None
        
        def exprICode(i):
            try:
                return ord(expr[i])
            except IndexError:
                return float("nan")
        
        length = len(expr)
        
        # Push `index` up to the next non-space character
        def gobbleSpaces():
            ch = exprICode(state['index'])
            #  space or tab
            while (ch == 32 or ch == 9):
                state['index'] += 1
                ch = exprICode(state['index'])
            

        # The main parsing function. Much of this code is dedicated to ternary expressions
        def gobbleExpression():
            test = gobbleBinaryExpression()
            consequent = None
            alternate = None
            gobbleSpaces()
            
            if exprICode(state['index']) == PreJsPy.QUMARK_CODE:
                #  Ternary expression: test ? consequent : alternate
                state['index'] += 1
                consequent = gobbleExpression()
                if not consequent:
                    self.__throw_error('Expected expression', state['index'])
                
                gobbleSpaces()
                
                if exprICode(state['index']) == PreJsPy.COLON_CODE:
                    state['index'] += 1
                    alternate = gobbleExpression()
                    
                    if not alternate:
                        self.__throw_error('Expected expression', state['index'])
                    
                    return {
                        'type': PreJsPy.CONDITIONAL_EXP,
                        'test': test,
                        'consequent': consequent,
                        'alternate': alternate
                    }
                else:
                    self.__throw_error('Expected :', state['index'])
            else:
                return test


        # Search for the operation portion of the string (e.g. `+`, `===`)
        # Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
        # and move down from 3 to 2 to 1 character until a matching binary operation is found
        # then, return that binary operation
        def gobbleBinaryOp():
            gobbleSpaces()
            to_check = expr[state['index']:state['index']+self.max_binop_len]
            tc_len = len(to_check)
            while tc_len > 0:
                if to_check in self.binary_ops.keys():
                    state['index'] += tc_len
                    return to_check
                tc_len -= 1
                to_check = to_check[:tc_len]
            return False


        # This function is responsible for gobbling an individual expression,
        # e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
        def gobbleBinaryExpression():
            ch_i = None
            node = None
            biop = None
            prec = None
            stack = None
            biop_info = None
            left = None
            right = None
            i = None
            
            # First, try to get the leftmost thing
            # Then, check to see if there's a binary operator operating on that leftmost thing
            left = gobbleToken()
            biop = gobbleBinaryOp()

            # If there wasn't a binary operator, just return the leftmost node
            if not biop:
                return left

            # Otherwise, we need to start a stack to properly place the binary operations in their
            # precedence structure
            biop_info = { 'value': biop, 'prec': self.__binaryPrecedence(biop)}

            right = gobbleToken()
            if not right:
                self.__throw_error("Expected expression after " + biop, state['index'])
            
            # create a stack of operators
            stack = [left, biop_info, right];

            # Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
            while True:
                biop = gobbleBinaryOp()
                
                if not biop:
                    break
                
                prec = self.__binaryPrecedence(biop)
                
                if prec == 0:
                    break
                
                biop_info = { 'value': biop, 'prec': prec };

                # Reduce: make a binary expression from the three topmost entries.
                while (len(stack) > 2) and prec < stack[len(stack)-2]['prec']:
                    right = stack.pop()
                    biop = stack.pop()['value']
                    left = stack.pop()
                    node = self.__createBinaryExpression(biop, left, right)
                    
                    stack.append(node)
                
                node = gobbleToken()
                if not node:
                    self.__throw_error("Expected expression after " + biop, state['index'])
                
                stack.append(biop_info)
                stack.append(node)
            
            i = len(stack) - 1
            node = stack[i]
            while i > 1:
                node = self.__createBinaryExpression(stack[i - 1]['value'], stack[i - 2], node)
                i -= 2
            
            return node

        # An individual part of a binary expression:
        # e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
        def gobbleToken():
            ch = None
            to_check = None
            tc_len = None
            
            gobbleSpaces()
            ch = exprICode(state['index'])

            if self.__isDecimalDigit(ch) or ch == PreJsPy.PERIOD_CODE:
                # Char code 46 is a dot `.` which can start off a numeric literal
                return gobbleNumericLiteral()
            elif ch == PreJsPy.SQUOTE_CODE or ch == PreJsPy.DQUOTE_CODE:
                # Single or double quotes
                return gobbleStringLiteral()
            elif ch == PreJsPy.OBRACK_CODE:
                return gobbleArray()
            else:
                to_check = expr[state['index']:state['index']+self.max_unop_len]
                tc_len = len(to_check)
                while tc_len > 0:
                    if to_check in self.unary_ops:
                        state['index'] += tc_len
                        return {
                            'type': PreJsPy.UNARY_EXP,
                            'operator': to_check,
                            'argument': gobbleToken(),
                            'prefix': True
                        };
                    tc_len -= 1
                    to_check = to_check[:tc_len]
                
                if self.__isIdentifierStart(ch) or ch == PreJsPy.OPAREN_CODE: # open parenthesis
                    # `foo`, `bar.baz`
                    return gobbleVariable()
            
            return False

        # Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
        # keep track of everything in the numeric literal and then calling `parseFloat` on that string
        def gobbleNumericLiteral():
            number = ''
            ch = None
            chCode = None
            
            while self.__isDecimalDigit(exprICode(state['index'])):
                number += exprI(state['index'])
                state['index'] += 1
            
            if exprICode(state['index']) == PreJsPy.PERIOD_CODE: # can start with a decimal marker
                number += exprI(state['index'])
                state['index'] += 1
                
                while self.__isDecimalDigit(exprICode(state['index'])):
                    number += exprI(state['index'])
                    state['index'] += 1
            
            ch = exprI(state['index'])
            if ch ==  'e' or ch == 'E': # exponent marker
                number += exprI(state['index'])
                state['index'] += 1
                
                ch = exprI(state['index'])
                if ch == '+' or ch == '-': # exponent sign
                    number += exprI(state['index'])
                    state['index'] += 1
                while self.__isDecimalDigit(exprICode(state['index'])): #exponent itself
                    number += exprI(state['index'])
                    state['index'] += 1
                
                if not self.__isDecimalDigit(exprICode(state['index']-1)):
                    self.__throw_error('Expected exponent (' + number + exprI(state['index']) + ')', state['index'])
                
            
            
            chCode = exprICode(state['index'])
            # Check to make sure this isn't a variable name that start with a number (123abc)
            if self.__isIdentifierStart(chCode):
                self.__throw_error('Variable names cannot start with a number (' + number + exprI(state['index']) + ')', state['index'])
            elif chCode == PreJsPy.PERIOD_CODE:
                self.__throw_error('Unexpected period', state['index'])
            
            return {
                'type': PreJsPy.LITERAL,
                'value': float(number),
                'raw': number
            }


        # Parses a string literal, staring with single or double quotes with basic support for escape codes
        # e.g. `"hello world"`, `'this is\nJSEP'`
        def gobbleStringLiteral():
            s = ''
            
            quote = exprI(state['index'])
            state['index'] += 1
            
            closed = False
            ch = None
            
            while state['index'] < length:
                ch = exprI(state['index'])
                state['index'] += 1
                
                if ch == quote:
                    closed = True
                    break
                elif ch == '\\':
                    # Check for all of the common escape codes
                    ch = exprI(state['index'])
                    state['index'] += 1
                    
                    if ch == 'n':
                        s += '\n'
                    elif ch == 'r':
                        s += '\r'
                    elif ch == 't':
                        s += '\t'
                    elif ch == 'b':
                        s += '\b'
                    elif ch == 'f':
                        s += '\f'
                    elif ch == 'v':
                        s += '\x0B'
                    elif ch == '\\':
                        s += '\\'
                else:
                    s += ch

            if not closed:
                self.__throw_error('Unclosed quote after "'+s+'"', state['index'])
            
            return {
                'type': PreJsPy.LITERAL,
                'value': s,
                'raw': quote + s + quote
            }


        # Gobbles only identifiers
        # e.g.: `foo`, `_value`, `$x1`
        # Also, this function checks if that identifier is a literal:
        # (e.g. `true`, `false`, `null`) or `this`
        def gobbleIdentifier():
            ch = exprICode(state['index'])
            start = state['index']
            identifier = None
            
            if self.__isIdentifierStart(ch):
                state['index'] += 1
            else:
                self.__throw_error('Unexpected ' + exprI(state['index']), state['index'])
            
            while state['index'] < length:
                ch = exprICode(state['index'])
                
                if self.__isIdentifierPart(ch):
                    state['index'] += 1
                else:
                    break
            
            identifier = expr[start:state['index']]
            
            if identifier in self.constants.keys():
                return {
                    'type': PreJsPy.LITERAL,
                    'value': self.constants[identifier],
                    'raw': identifier
                }
            elif identifier == self.this:
                return { 'type': PreJsPy.THIS_EXP }
            else:
                return {
                    'type': PreJsPy.IDENTIFIER,
                    'name': identifier
                }

        #  Gobbles a list of arguments within the context of a function call
        # or array literal. This function also assumes that the opening character
        # `(` or `[` has already been gobbled, and gobbles expressions and commas
        # until the terminator character `)` or `]` is encountered.
        # e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
        def gobbleArguments(termination):
            ch_i = None
            args = []
            node = None
            
            while state['index'] < length:
                gobbleSpaces()
                ch_i = exprICode(state['index'])
                
                if ch_i == termination:
                    state['index'] += 1
                    break
                elif ch_i == PreJsPy.COMMA_CODE: # between expressions
                    state['index'] += 1
                else:
                    node = gobbleExpression()
                    
                    if (not node) or node['type'] == PreJsPy.COMPOUND:
                        self.__throw_error('Expected comma', state['index'])
                    
                    args.append(node)
                
            
            return args


        # Gobble a non-literal variable name. This variable name may include properties
        # e.g. `foo`, `bar.baz`, `foo['bar'].baz`
        # It also gobbles function calls:
        # e.g. `Math.acos(obj.angle)`
        def gobbleVariable():
            ch_i = None
            node = None
            
            ch_i = exprICode(state['index'])

            if ch_i == PreJsPy.OPAREN_CODE:
                node = gobbleGroup()
            else:
                node = gobbleIdentifier()
            
            gobbleSpaces()
            
            ch_i = exprICode(state['index'])
            
            while (ch_i == PreJsPy.PERIOD_CODE or ch_i == PreJsPy.OBRACK_CODE or ch_i == PreJsPy.OPAREN_CODE):
                state['index'] += 1
                
                if ch_i == PreJsPy.PERIOD_CODE:
                    gobbleSpaces()
                    
                    node = {
                        'type': PreJsPy.MEMBER_EXP,
                        'computed': False,
                        'object': node,
                        'property': gobbleIdentifier()
                    }
                elif ch_i == PreJsPy.OBRACK_CODE:
                    node = {
                        'type': PreJsPy.MEMBER_EXP,
                        'computed': true,
                        'object': node,
                        'property': gobbleExpression()
                    }
                    
                    gobbleSpaces()
                    
                    ch_i = exprICode(state['index'])
                    
                    if ch_i != PreJsPy.CBRACK_CODE:
                        self.__throw_error('Unclosed [', state['index'])
                    
                    state['index'] += 1
                elif ch_i == PreJsPy.OPAREN_CODE:
                    # A function call is being made; gobble all the arguments
                    node = {
                        'type': PreJsPy.CALL_EXP,
                        'arguments': gobbleArguments(PreJsPy.CPAREN_CODE),
                        'callee': node
                    }
                
                gobbleSpaces()
                ch_i = exprICode(state['index'])
            
            return node


        # Responsible for parsing a group of things within parentheses `()`
        # This function assumes that it needs to gobble the opening parenthesis
        # and then tries to gobble everything within that parenthesis, assuming
        # that the next thing it should see is the close parenthesis. If not,
        # then the expression probably doesn't have a `)`
        def gobbleGroup():
            state['index'] += 1
            node = gobbleExpression()
            
            gobbleSpaces()
            
            if exprICode(state['index']) == PreJsPy.CPAREN_CODE:
                state['index'] += 1
                return node
            else:
                self.__throw_error('Unclosed (', state['index'])

        # Responsible for parsing Array literals `[1, 2, 3]`
        # This function assumes that it needs to gobble the opening bracket
        # and then tries to gobble the expressions as arguments.
        def gobbleArray():
            state["index"] += 1
            
            return {
                'type': PreJsPy.ARRAY_EXP,
                'elements': gobbleArguments(PreJsPy.CBRACK_CODE)
            }

        nodes = []
        ch_i = None
        node = None

        while state['index'] < length:
            ch_i = exprICode(state['index'])
            
            # Expressions can be separated by semicolons, commas, or just inferred without any
            # separators
            if ch_i == PreJsPy.SEMCOL_CODE or ch_i == PreJsPy.COMMA_CODE:
                state['index'] += 1 # ignore separators
            else:
                # Try to gobble each expression individually
                node = gobbleExpression()
                if node:
                    nodes.append(node)
                # If we weren't able to find a binary expression and are out of room, then
                # the expression passed in probably has too much
                elif state['index'] < length:
                    self.__throw_error('Unexpected "' + exprI(state['index']) + '"', state['index'])

        # If there's only one expression just try returning the expression
        if len(nodes) == 1:
            return nodes[0]
        else:
            return {
                'type': PreJsPy.COMPOUND,
                'body': nodes
            }