"""
    (c) Tom Wiesing 2016-20, licensed under MIT license
    This code is heavily based on the JavaScript version JSEP
    The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and
    licensed under MIT
"""


class PreJsPy(object):
    """Represents a single instance of the PreJSPy Parser."""

    # A list of node types that can be returned.
    COMPOUND = "Compound"
    IDENTIFIER = "Identifier"
    MEMBER_EXP = "MemberExpression"
    LITERAL = "Literal"
    CALL_EXP = "CallExpression"
    UNARY_EXP = "UnaryExpression"
    BINARY_EXP = "BinaryExpression"
    CONDITIONAL_EXP = "ConditionalExpression"
    ARRAY_EXP = "ArrayExpression"

    # List of char codes.
    PERIOD_CODE = 46  # '.'
    COMMA_CODE = 44  # ','
    SQUOTE_CODE = 39  # single quote
    DQUOTE_CODE = 34  # double quotes
    OPAREN_CODE = 40  # (
    CPAREN_CODE = 41  # )
    OBRACK_CODE = 91  # [
    CBRACK_CODE = 93  # ]
    QUMARK_CODE = 63  # ?
    SEMCOL_CODE = 59  # ;
    COLON_CODE = 58  # :

    # =======================
    # STATIC HELPER FUNCTIONS
    # =======================
    @staticmethod
    def __throw_error(msg, index):
        """Throws a parser error with a given message and a given index.

        :param msg: Message of error to throw.
        :param index: Character index at which the error should be thrown.
        """
        msg = "%s at character %d" % (msg, index)
        raise Exception(msg)

    @staticmethod
    def __createBinaryExpression(operator, left, right):
        """Utility function that creates a binary expression to be returned.

        :param operator: Operator to use for binary expression.
        :param left: Left expression to use for the binary expression.
        :param right: Right expression to use for the binary expression.
        """

        return {
            "type": PreJsPy.BINARY_EXP,
            "operator": operator,
            "left": left,
            "right": right,
        }

    @staticmethod
    def __getMaxKeyLen(o):
        """Gets the longest key length of an object

        :param o: Object to iterate over
        """

        if len(o.keys()) == 0:
            return 0
        return max(map(len, o.keys()))

    @staticmethod
    def __getMaxMemLen(ary):
        """Gets the maximum length of the member of any members of an array.

        :param ary: Array to iterate over.
        """
        if len(ary) == 0:
            return 0
        return max(map(len, ary))

    @staticmethod
    def __isDecimalDigit(ch):
        """Checks if a character is a decimal digit.

        :param ch: Code of character to check.
        """

        return ch >= 48 and ch <= 57  # 0...9

    @staticmethod
    def __isIdentifierStart(ch):
        """Checks if a character is the start of an identifier.

        :param ch: Code of character to check.
        """

        # '$', A..Z and a..z and non-ascii
        return (
            (ch == 36)
            or (ch == 95)
            or (ch >= 65 and ch <= 90)
            or (ch >= 97 and ch <= 122)
            or (ch >= 128)
        )

    @staticmethod
    def __isIdentifierPart(ch):
        """Checks if a character is part of an identifier.

        :param ch: Code of character to check.
        """

        # `$`,  `_`, A...Z, a...z and 0...9 and non-ascii
        return (
            (ch == 36)
            or (ch == 95)
            or (ch >= 65 and ch <= 90)
            or (ch >= 97 and ch <= 122)
            or (ch >= 48 and ch <= 57)
            or (ch > 128)
        )

    # =======
    # CONFIG
    # =======

    def getConfig(self):
        """Gets the current config used by this parser."""
        return {
            "Operators": {
                "Literals": PreJsPy.__copyDict(self.__config["Operators"]["Literals"]),
                "Unary": PreJsPy.__copyList(self.__config["Operators"]["Unary"]),
                "Binary": PreJsPy.__copyDict(self.__config["Operators"]["Binary"]),
            },
            "Features": {
                "Tertiary": self.__config["Features"]["Tertiary"],  # dones
                "Identifiers": self.__config["Features"]["Identifiers"],
                "Calls": self.__config["Features"]["Calls"],
                "Members": PreJsPy.__copyDict(self.__config["Features"]["Members"]),
                "Literals": PreJsPy.__copyDict(self.__config["Features"]["Literals"]),
            },
        }

    def setConfig(self, config):
        """Sets the config used by this parser.

        :param config: (Possibly partial) configuration to use.
        """

        if "Operators" in config:
            if "Literals" in config["Operators"]:
                self.__config["Operators"]["Literals"] = PreJsPy.__copyDict(
                    config["Operators"]["Literals"]
                )
            if "Unary" in config["Operators"]:
                self.__config["Operators"]["Unary"] = PreJsPy.__copyDict(
                    config["Operators"]["Unary"]
                )
                self.__max_uops_len = PreJsPy.__getMaxMemLen(
                    self.__config["Operators"]["Unary"]
                )
            if "Binary" in config["Operators"]:
                self.__config["Operators"]["Binary"] = PreJsPy.__copyDict(
                    config["Operators"]["Binary"]
                )
                self.__max_binop_len = PreJsPy.__getMaxKeyLen(
                    self.__config["Operators"]["Binary"]
                )
        if "Features" in config:
            if "Tertiary" in config["Features"]:
                self.__config["Features"]["Tertiary"] = config["Features"]["Tertiary"]
            if "Identifiers" in config["Features"]:
                self.__config["Features"]["Identifiers"] = config["Features"][
                    "Identifiers"
                ]
            if "Calls" in config["Features"]:
                self.__config["Features"]["Calls"] = config["Features"]["Calls"]

            if "Members" in config["Features"]:
                if "Computed" in config["Features"]["Members"]:
                    self.__config["Features"]["Members"]["Computed"] = config[
                        "Features"
                    ]["Members"]["Computed"]
                if "Static" in config["Features"]["Members"]:
                    self.__config["Features"]["Members"]["Static"] = config["Features"][
                        "Members"
                    ]["Static"]
            if "Literals" in config["Features"]:
                if "Array" in config["Features"]["Literals"]:
                    self.__config["Features"]["Literals"]["Array"] = config["Features"][
                        "Literals"
                    ]["Array"]
                if "Numeric" in config["Features"]["Literals"]:
                    self.__config["Features"]["Literals"]["Numeric"] = config[
                        "Features"
                    ]["Literals"]["Numeric"]
                if "String" in config["Features"]["Literals"]:
                    self.__config["Features"]["Literals"]["String"] = config[
                        "Features"
                    ]["Literals"]["String"]

        return self.getConfig()

    # =======
    # LEGACY CONFIG
    # =======

    def getConstants(self):
        """Gets the constants to be used by this parser."""

        return self.getConfig()["Operators"]["Literals"]

    def setConstants(self, d):
        """Sets the constants to be used by this parser.

        :param d: Constants to set.
        """

        return self.setConfig({"Operators": {"Literals": d}})["Operators"]["Literals"]

    def getUnaryOperators(self):
        """Gets the unary operators known to this parser."""

        return self.getConfig()["Operators"]["Unary"]

    def getMaxUnaryOperatorsLength(self):
        """Gets the length of the maximal unary operator."""

        return self.__max_uops_len

    def setUnaryOperators(self, ary):
        """Sets the unary operators known to this parser.

        :param ary: List of unary operators to set.
        """

        return self.setConfig({"Operators": {"Unary": ary}})["Operators"]["Unary"]

    def getBinaryOperators(self):
        """Gets the binary operators known to this parser."""

        return self.getConfig()["Operators"]["Binary"]

    def getMaxBinaryOperatorsLength(self):
        """Gets the length of the maximal binary operator."""

        return self.__max_binop_len

    def setBinaryOperators(self, d):
        """Sets the  binary operators known to this parser.

        :param d: Dictionary of binary operators to set.
        """

        return self.setConfig({"Operators": {"Binary": d}})["Operators"]["Binary"]

    def getTertiaryOperatorEnabled(self):
        """Gets a boolean indicating if the tertiary operator is enabled or
        not."""

        return self.getConfig()["Features"]["Tertiary"]

    def setTertiaryOperatorEnabled(self, e):
        """Enables or disables the tertiary operator.

        :param e: State of the tertiary operator to set.
        """

        return self.setConfig({"Features": {"Tertirary": e}})["Features"]["Tertiary"]

    # =========
    # INIT CODE
    # =========

    def __init__(self):
        """Creates a new PreJSPyParser instance."""

        self.__config = self.__class__.defaultConfig()
        self.setConfig(self.__config)

    # ============
    # MISC HELPERS
    # ============

    def __binaryPrecedence(self, op_val):
        """
        Returns the precedence of a binary operator or `0` if it isn't a binary operator.
        :param op_val: Value of operator to lookup.
        """

        if op_val in self.__config["Operators"]["Binary"]:
            return self.__config["Operators"]["Binary"][op_val]
        else:
            return 0

    @staticmethod
    def __copyDict(dict):
        return dict.copy()

    @staticmethod
    def __copyList(lst):
        return lst.copy()

    # =======
    # PARSING
    # =======

    def parse(self, expr):
        """Parses an expression expr into a parse tree.

        :param expr: Expression to parse.
        """

        # `index` stores the character number we are currently at while `length` is a constant
        # All of the gobbles below will modify `index` as we move along
        state = {"index": 0}

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
            ch = exprICode(state["index"])
            #  space or tab
            while ch == 32 or ch == 9:
                state["index"] += 1
                ch = exprICode(state["index"])

        # The main parsing function. Much of this code is dedicated to ternary expressions
        def gobbleExpression():
            test = gobbleBinaryExpression()
            consequent = None
            alternate = None
            gobbleSpaces()

            if exprICode(state["index"]) == PreJsPy.QUMARK_CODE:
                #  Ternary expression: test ? consequent : alternate
                state["index"] += 1
                consequent = gobbleExpression()
                if not consequent:
                    PreJsPy.__throw_error("Expected expression", state["index"])

                gobbleSpaces()

                if exprICode(state["index"]) == PreJsPy.COLON_CODE:
                    state["index"] += 1
                    alternate = gobbleExpression()

                    if not alternate:
                        PreJsPy.__throw_error("Expected expression", state["index"])

                    if not self.__config["Features"]["Tertiary"]:
                        PreJsPy.__throw_error(
                            "Unexpected tertiary operator", state["index"]
                        )

                    return {
                        "type": PreJsPy.CONDITIONAL_EXP,
                        "test": test,
                        "consequent": consequent,
                        "alternate": alternate,
                    }
                else:
                    PreJsPy.__throw_error("Expected :", state["index"])
            else:
                return test

        # Search for the operation portion of the string (e.g. `+`, `===`)
        # Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
        # and move down from 3 to 2 to 1 character until a matching binary operation is found
        # then, return that binary operation
        def gobbleBinaryOp():
            gobbleSpaces()
            to_check = expr[state["index"] : state["index"] + self.__max_binop_len]
            tc_len = len(to_check)
            while tc_len > 0:
                if to_check in self.__config["Operators"]["Binary"]:
                    state["index"] += tc_len
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
            biop_info = {"value": biop, "prec": self.__binaryPrecedence(biop)}

            right = gobbleToken()
            if not right:
                PreJsPy.__throw_error(
                    "Expected expression after " + biop, state["index"]
                )

            # create a stack of operators
            stack = [left, biop_info, right]

            # Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
            while True:
                biop = gobbleBinaryOp()

                if not biop:
                    break

                prec = self.__binaryPrecedence(biop)

                if prec == 0:
                    break

                biop_info = {"value": biop, "prec": prec}

                # Reduce: make a binary expression from the three topmost entries.
                while (len(stack) > 2) and prec < stack[len(stack) - 2]["prec"]:
                    right = stack.pop()
                    biop = stack.pop()["value"]
                    left = stack.pop()
                    node = PreJsPy.__createBinaryExpression(biop, left, right)

                    stack.append(node)

                node = gobbleToken()
                if not node:
                    PreJsPy.__throw_error(
                        "Expected expression after " + biop, state["index"]
                    )

                stack.append(biop_info)
                stack.append(node)

            i = len(stack) - 1
            node = stack[i]
            while i > 1:
                node = PreJsPy.__createBinaryExpression(
                    stack[i - 1]["value"], stack[i - 2], node
                )
                i -= 2

            return node

        # An individual part of a binary expression:
        # e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
        def gobbleToken():
            ch = None
            to_check = None
            tc_len = None

            gobbleSpaces()
            ch = exprICode(state["index"])

            if self.__isDecimalDigit(ch) or ch == PreJsPy.PERIOD_CODE:
                # Char code 46 is a dot `.` which can start off a numeric literal
                return gobbleNumericLiteral()
            elif ch == PreJsPy.SQUOTE_CODE or ch == PreJsPy.DQUOTE_CODE:
                # Single or double quotes
                return gobbleStringLiteral()
            elif ch == PreJsPy.OBRACK_CODE:
                return gobbleArray()
            else:
                to_check = expr[state["index"] : state["index"] + self.__max_uops_len]
                tc_len = len(to_check)
                while tc_len > 0:
                    if to_check in self.__config["Operators"]["Unary"]:
                        state["index"] += tc_len
                        return {
                            "type": PreJsPy.UNARY_EXP,
                            "operator": to_check,
                            "argument": gobbleToken(),
                        }
                    tc_len -= 1
                    to_check = to_check[:tc_len]

                if (
                    PreJsPy.__isIdentifierStart(ch) or ch == PreJsPy.OPAREN_CODE
                ):  # open parenthesis
                    # `foo`, `bar.baz`
                    return gobbleVariable()

            return False

        # Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
        # keep track of everything in the numeric literal and then calling `parseFloat` on that string
        def gobbleNumericLiteral():
            number = ""
            ch = None
            chCode = None

            while self.__isDecimalDigit(exprICode(state["index"])):
                number += exprI(state["index"])
                state["index"] += 1

            if (
                exprICode(state["index"]) == PreJsPy.PERIOD_CODE
            ):  # can start with a decimal marker
                number += exprI(state["index"])
                state["index"] += 1

                while self.__isDecimalDigit(exprICode(state["index"])):
                    number += exprI(state["index"])
                    state["index"] += 1

            ch = exprI(state["index"])
            if ch == "e" or ch == "E":  # exponent marker
                number += exprI(state["index"])
                state["index"] += 1

                ch = exprI(state["index"])
                if ch == "+" or ch == "-":  # exponent sign
                    number += exprI(state["index"])
                    state["index"] += 1
                while self.__isDecimalDigit(
                    exprICode(state["index"])
                ):  # exponent itself
                    number += exprI(state["index"])
                    state["index"] += 1

                if not self.__isDecimalDigit(exprICode(state["index"] - 1)):
                    PreJsPy.__throw_error(
                        "Expected exponent (" + number + exprI(state["index"]) + ")",
                        state["index"],
                    )

            chCode = exprICode(state["index"])
            # Check to make sure this isn't a variable name that start with a number (123abc)
            if PreJsPy.__isIdentifierStart(chCode):
                PreJsPy.__throw_error(
                    "Variable names cannot start with a number ("
                    + number
                    + exprI(state["index"])
                    + ")",
                    state["index"],
                )
            elif chCode == PreJsPy.PERIOD_CODE:
                PreJsPy.__throw_error("Unexpected period", state["index"])

            if not self.__config["Features"]["Literals"]["Numeric"]:
                PreJsPy.__throwError(
                    "Unexpected numeric literal", state["index"] - number.length
                )

            return {"type": PreJsPy.LITERAL, "value": float(number), "raw": number}

        # Parses a string literal, staring with single or double quotes with basic support for escape codes
        # e.g. `"hello world"`, `'this is\nJSEP'`
        def gobbleStringLiteral():
            s = ""

            index_start = state["index"]

            quote = exprI(state["index"])
            state["index"] += 1

            closed = False
            ch = None

            while state["index"] < length:
                ch = exprI(state["index"])
                state["index"] += 1

                if ch == quote:
                    closed = True
                    break
                elif ch == "\\":
                    # Check for all of the common escape codes
                    ch = exprI(state["index"])
                    state["index"] += 1

                    if ch == "n":
                        s += "\n"
                    elif ch == "r":
                        s += "\r"
                    elif ch == "t":
                        s += "\t"
                    elif ch == "b":
                        s += "\b"
                    elif ch == "f":
                        s += "\f"
                    elif ch == "v":
                        s += "\x0B"
                    elif ch == "\\":
                        s += "\\"

                    # default: just add the character literally.
                    else:
                        s += ch
                else:
                    s += ch

            if not closed:
                PreJsPy.__throw_error(
                    'Unclosed quote after "' + s + '"', state["index"]
                )
            if not self.__config["Features"]["Literals"]["String"]:
                PreJsPy.__throw_error("Unexpected string literal", index_start)

            return {"type": PreJsPy.LITERAL, "value": s, "raw": quote + s + quote}

        # Gobbles only identifiers
        # e.g.: `foo`, `_value`, `$x1`
        # Also, this function checks if that identifier is a literal:
        # (e.g. `true`, `false`, `null`)
        def gobbleIdentifier():
            ch = exprICode(state["index"])
            start = state["index"]
            identifier = None

            if PreJsPy.__isIdentifierStart(ch):
                state["index"] += 1
            else:
                PreJsPy.__throw_error(
                    "Unexpected " + exprI(state["index"]), state["index"]
                )

            while state["index"] < length:
                ch = exprICode(state["index"])

                if PreJsPy.__isIdentifierPart(ch):
                    state["index"] += 1
                else:
                    break

            identifier = expr[start : state["index"]]

            if identifier in self.__config["Operators"]["Literals"]:
                return {
                    "type": PreJsPy.LITERAL,
                    "value": self.__config["Operators"]["Literals"][identifier],
                    "raw": identifier,
                }
            else:
                if not self.__config["Features"]["Identifiers"]:
                    PreJsPy.__throw_error(
                        'Unknown literal "' + identifier + '"', state["index"]
                    )
                return {"type": PreJsPy.IDENTIFIER, "name": identifier}

        # Gobbles a list of arguments within the context of a function call
        # or array literal. This function also assumes that the opening character
        # `(` or `[` has already been gobbled, and gobbles expressions and commas
        # until the terminator character `)` or `]` is encountered.
        # e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
        def gobbleArguments(termination):
            ch_i = None
            args = []
            node = None

            while state["index"] < length:
                gobbleSpaces()
                ch_i = exprICode(state["index"])

                if ch_i == termination:
                    state["index"] += 1
                    break
                elif ch_i == PreJsPy.COMMA_CODE:  # between expressions
                    state["index"] += 1
                else:
                    node = gobbleExpression()

                    if (not node) or node["type"] == PreJsPy.COMPOUND:
                        PreJsPy.__throw_error("Expected comma", state["index"])

                    args.append(node)

            return args

        # Gobble a non-literal variable name. This variable name may include properties
        # e.g. `foo`, `bar.baz`, `foo['bar'].baz`
        # It also gobbles function calls:
        # e.g. `Math.acos(obj.angle)`
        def gobbleVariable():
            ch_i = None
            node = None

            ch_i = exprICode(state["index"])

            if ch_i == PreJsPy.OPAREN_CODE:
                node = gobbleGroup()
            else:
                node = gobbleIdentifier()

            gobbleSpaces()

            ch_i = exprICode(state["index"])

            while (
                ch_i == PreJsPy.PERIOD_CODE
                or ch_i == PreJsPy.OBRACK_CODE
                or ch_i == PreJsPy.OPAREN_CODE
            ):
                state["index"] += 1

                if ch_i == PreJsPy.PERIOD_CODE:
                    if not self.__config["Features"]["Members"]["Static"]:
                        PreJsPy.__throwError(
                            "Unexpected static MemberExpression", state["index"]
                        )

                    gobbleSpaces()

                    node = {
                        "type": PreJsPy.MEMBER_EXP,
                        "computed": False,
                        "object": node,
                        "property": gobbleIdentifier(),
                    }
                elif ch_i == PreJsPy.OBRACK_CODE:
                    if not self.__config["Features"]["Members"]["Computed"]:
                        PreJsPy.__throwError(
                            "Unexpected computed MemberExpression", state["index"]
                        )

                    node = {
                        "type": PreJsPy.MEMBER_EXP,
                        "computed": True,
                        "object": node,
                        "property": gobbleExpression(),
                    }

                    gobbleSpaces()

                    ch_i = exprICode(state["index"])

                    if ch_i != PreJsPy.CBRACK_CODE:
                        PreJsPy.__throw_error("Unclosed [", state["index"])

                    state["index"] += 1
                elif ch_i == PreJsPy.OPAREN_CODE:
                    if not self.__config["Features"]["Calls"]:
                        PreJsPy.__throw_error(
                            "Unexpected function call", state["index"]
                        )
                    # A function call is being made; gobble all the arguments
                    node = {
                        "type": PreJsPy.CALL_EXP,
                        "arguments": gobbleArguments(PreJsPy.CPAREN_CODE),
                        "callee": node,
                    }

                gobbleSpaces()
                ch_i = exprICode(state["index"])

            return node

        # Responsible for parsing a group of things within parentheses `()`
        # This function assumes that it needs to gobble the opening parenthesis
        # and then tries to gobble everything within that parenthesis, assuming
        # that the next thing it should see is the close parenthesis. If not,
        # then the expression probably doesn't have a `)`
        def gobbleGroup():
            state["index"] += 1
            node = gobbleExpression()

            gobbleSpaces()

            if exprICode(state["index"]) == PreJsPy.CPAREN_CODE:
                state["index"] += 1
                return node
            else:
                PreJsPy.__throw_error("Unclosed (", state["index"])

        # Responsible for parsing Array literals `[1, 2, 3]`
        # This function assumes that it needs to gobble the opening bracket
        # and then tries to gobble the expressions as arguments.
        def gobbleArray():
            if not self.__config["Features"]["Literals"]["Array"]:
                PreJsPy.__throwError("Unexpected array literal", state["index"])

            state["index"] += 1

            return {
                "type": PreJsPy.ARRAY_EXP,
                "elements": gobbleArguments(PreJsPy.CBRACK_CODE),
            }

        nodes = []
        ch_i = None
        node = None

        while state["index"] < length:
            ch_i = exprICode(state["index"])

            # Expressions can be separated by semicolons, commas, or just inferred without any
            # separators
            if ch_i == PreJsPy.SEMCOL_CODE or ch_i == PreJsPy.COMMA_CODE:
                state["index"] += 1  # ignore separators
            else:
                # Try to gobble each expression individually
                node = gobbleExpression()
                if node:
                    nodes.append(node)
                # If we weren't able to find a binary expression and are out of room, then
                # the expression passed in probably has too much
                elif state["index"] < length:
                    PreJsPy.__throw_error(
                        'Unexpected "' + exprI(state["index"]) + '"', state["index"]
                    )

        # If there's only one expression just try returning the expression
        if len(nodes) == 1:
            return nodes[0]
        else:
            return {"type": PreJsPy.COMPOUND, "body": nodes}

    @staticmethod
    def defaultConfig():
        """Returns the default configuration"""
        return {
            "Operators": {
                "Literals": {
                    "true": True,
                    "false": False,
                    "null": None,
                },
                "Unary": ["-", "!", "~", "+"],
                "Binary": {
                    "||": 1,
                    "&&": 2,
                    "|": 3,
                    "^": 4,
                    "&": 5,
                    "==": 6,
                    "!=": 6,
                    "===": 6,
                    "!==": 6,
                    "<": 7,
                    ">": 7,
                    "<=": 7,
                    ">=": 7,
                    "<<": 8,
                    ">>": 8,
                    ">>>": 8,
                    "+": 9,
                    "-": 9,
                    "*": 10,
                    "/": 10,
                    "%": 10,
                },
            },
            "Features": {
                "Tertiary": True,
                "Identifiers": True,
                "Calls": True,
                "Members": {
                    "Static": True,
                    "Computed": True,
                },
                "Literals": {
                    "Numeric": True,
                    "String": True,
                    "Array": True,
                },
            },
        }
