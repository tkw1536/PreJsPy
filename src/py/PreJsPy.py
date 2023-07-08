"""
    (c) Tom Wiesing 2016-20, licensed under MIT license
    This code is heavily based on the JavaScript version JSEP
    The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and
    licensed under MIT
"""

from typing import (
    Any,
    Generic,
    Dict,
    List,
    Union,
    Final,
    Literal as tLiteral,
    Optional,
    cast,
    TypeAlias,
    TypedDict,
    TypeVar,
    NoReturn,
)

L = TypeVar("L")
U = TypeVar("U", bound=str)
B = TypeVar("B", bound=str)


COMPOUND: Final = "Compound"
IDENTIFIER: Final = "Identifier"
MEMBER_EXP: Final = "MemberExpression"
LITERAL: Final = "Literal"
CALL_EXP: Final = "CallExpression"
UNARY_EXP: Final = "UnaryExpression"
BINARY_EXP: Final = "BinaryExpression"
CONDITIONAL_EXP: Final = "ConditionalExpression"
ARRAY_EXP: Final = "ArrayExpression"


Expression: TypeAlias = Union[
    "Compound[L,U,B]",
    "Identifier[L,U,B]",
    "Member[L,U,B]",
    "Literal[L,U,B]",
    "Call[L,U,B]",
    "Unary[L,U,B]",
    "Binary[L,U,B]",
    "Condition[L,U,B]",
    "Ary[L,U,B]",
]


class Compound(TypedDict, Generic[L, U, B]):
    type: tLiteral["Compound"]
    body: List["Expression[L,U,B]"]


class Identifier(TypedDict, Generic[L, U, B]):
    type: tLiteral["Identifier"]
    name: str


class Member(TypedDict, Generic[L, U, B]):
    type: tLiteral["MemberExpression"]
    computed: bool
    object: "Expression[L,U,B]"
    property: "Expression[L,U,B]"


class Literal(TypedDict, Generic[L, U, B]):
    type: tLiteral["Literal"]
    value: L | float | str
    raw: str


class Call(TypedDict, Generic[L, U, B]):
    type: tLiteral["CallExpression"]
    arguments: List["Expression[L,U,B]"]
    callee: "Expression[L,U,B]"


class Unary(TypedDict, Generic[L, U, B]):
    type: tLiteral["UnaryExpression"]
    operator: U
    argument: "Expression[L,U,B]"


class Binary(TypedDict, Generic[L, U, B]):
    type: tLiteral["BinaryExpression"]
    operator: B
    left: "Expression[L,U,B]"
    right: "Expression[L,U,B]"


class Condition(TypedDict, Generic[L, U, B]):
    type: tLiteral["ConditionalExpression"]
    test: "Expression[L,U,B]"
    consequent: "Expression[L,U,B]"
    alternate: "Expression[L,U,B]"


class Ary(TypedDict, Generic[L, U, B]):
    type: tLiteral["ArrayExpression"]
    elements: List["Expression[L,U,B]"]


class _BiopInfo(TypedDict, Generic[B]):
    value: B
    prec: int


class _OperatorsConfig(TypedDict, Generic[L, U, B]):
    Literals: Dict[str, L]
    Unary: List[U]
    Binary: Dict[B, int]


class _PartialOperatorsConfig(TypedDict, Generic[L, U, B], total=False):
    Literals: Dict[str, L]
    Unary: List[U]
    Binary: Dict[B, int]


class _Members(TypedDict):
    Static: bool
    Computed: bool


class _PartialMembers(TypedDict, total=False):
    Static: bool
    Computed: bool


class _Literals(TypedDict):
    Numeric: bool
    String: bool
    Array: bool


class _PartialLiterals(TypedDict, total=False):
    Numeric: bool
    String: bool
    Array: bool


class _Features(TypedDict):
    Compound: bool
    Tertiary: bool
    Identifiers: bool
    Calls: bool
    Members: _Members
    Literals: _Literals


class _PartialFeatures(TypedDict, total=False):
    Compound: bool
    Tertiary: bool
    Identifiers: bool
    Calls: bool
    Members: _PartialMembers
    Literals: _PartialLiterals


class Config(TypedDict, Generic[L, U, B]):
    """Configuration represents the configuration of a PreJsPy instance"""

    Operators: _OperatorsConfig[L, U, B]
    Features: _Features


class PartialConfig(TypedDict, Generic[L, U, B], total=False):
    Operators: _PartialOperatorsConfig[L, U, B]
    Features: _PartialFeatures


class PreJsPy(Generic[L, U, B]):
    """Represents a single instance of the PreJSPy Parser."""

    # List of char codes.
    PERIOD_CODE: Final = ord(".")
    COMMA_CODE: Final = ord(",")  # ','
    SQUOTE_CODE: Final = ord("'")  # single quote
    DQUOTE_CODE: Final = ord('"')  # double quotes
    OPAREN_CODE: Final = ord("(")  # (
    CPAREN_CODE: Final = ord(")")  # )
    OBRACK_CODE: Final = ord("[")  # [
    CBRACK_CODE: Final = ord("]")  # ]
    QUMARK_CODE: Final = ord("?")  # ?
    SEMCOL_CODE: Final = ord(";")  # ;
    COLON_CODE: Final = ord(":")  # :
    SPACE_CODE: Final = ord(" ")
    TAB_CODE: Final = ord("\t")

    # =======================
    # STATIC HELPER FUNCTIONS
    # =======================
    def __throw_error(self, msg: str) -> NoReturn:
        """Throws a parser error with a given message and a given index.

        :param msg: Message of error to throw.
        :param index: Character index at which the error should be thrown.
        """
        msg = "{} at character {}".format(msg, self.__index)
        raise Exception(msg)

    @staticmethod
    def __getMaxKeyLen(o: Dict[B, int]) -> int:
        """Gets the longest key length of an object

        :param o: Object to iterate over
        """

        if len(o.keys()) == 0:
            return 0
        return max(map(len, o.keys()))

    @staticmethod
    def __getMaxMemLen(ary: List[U]) -> int:
        """Gets the maximum length of the member of any members of an array.

        :param ary: Array to iterate over.
        """
        if len(ary) == 0:
            return 0
        return max(map(len, ary))

    @staticmethod
    def __isDecimalDigit(ch: int) -> bool:
        """Checks if a character is a decimal digit.

        :param ch: Code of character to check.
        """

        return ch >= 48 and ch <= 57  # 0...9

    @staticmethod
    def __isIdentifierStart(ch: int) -> bool:
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
    def __isIdentifierPart(ch: int) -> bool:
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

    def GetConfig(self) -> Config[L, U, B]:
        """Gets the current config used by this parser."""
        return {
            "Operators": {
                "Literals": self.__config["Operators"]["Literals"].copy(),
                "Unary": self.__config["Operators"]["Unary"].copy(),
                "Binary": self.__config["Operators"]["Binary"].copy(),
            },
            "Features": {
                "Compound": self.__config["Features"]["Compound"],
                "Tertiary": self.__config["Features"]["Tertiary"],
                "Identifiers": self.__config["Features"]["Identifiers"],
                "Calls": self.__config["Features"]["Calls"],
                "Members": self.__config["Features"]["Members"].copy(),
                "Literals": self.__config["Features"]["Literals"].copy(),
            },
        }

    def SetConfig(self, config: Optional[PartialConfig[L, U, B]]) -> Config[L, U, B]:
        """Sets the config used by this parser.

        :param config: (Possibly partial) configuration to use.
        """

        if config is not None:
            if "Operators" in config:
                if "Literals" in config["Operators"]:
                    self.__config["Operators"]["Literals"] = config["Operators"][
                        "Literals"
                    ].copy()
                if "Unary" in config["Operators"]:
                    self.__config["Operators"]["Unary"] = config["Operators"][
                        "Unary"
                    ].copy()
                    self.__max_uops_len = PreJsPy.__getMaxMemLen(
                        self.__config["Operators"]["Unary"]
                    )
                if "Binary" in config["Operators"]:
                    self.__config["Operators"]["Binary"] = config["Operators"][
                        "Binary"
                    ].copy()
                    self.__max_binop_len = PreJsPy.__getMaxKeyLen(
                        self.__config["Operators"]["Binary"]
                    )
            if "Features" in config:
                if "Compound" in config["Features"]:
                    self.__config["Features"]["Compound"] = config["Features"][
                        "Compound"
                    ]
                if "Tertiary" in config["Features"]:
                    self.__config["Features"]["Tertiary"] = config["Features"][
                        "Tertiary"
                    ]
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
                        self.__config["Features"]["Members"]["Static"] = config[
                            "Features"
                        ]["Members"]["Static"]
                if "Literals" in config["Features"]:
                    if "Array" in config["Features"]["Literals"]:
                        self.__config["Features"]["Literals"]["Array"] = config[
                            "Features"
                        ]["Literals"]["Array"]
                    if "Numeric" in config["Features"]["Literals"]:
                        self.__config["Features"]["Literals"]["Numeric"] = config[
                            "Features"
                        ]["Literals"]["Numeric"]
                    if "String" in config["Features"]["Literals"]:
                        self.__config["Features"]["Literals"]["String"] = config[
                            "Features"
                        ]["Literals"]["String"]

        return self.GetConfig()

    # =========
    # INIT CODE
    # =========

    __config: Config[L, U, B]

    def __init__(self) -> None:
        """Creates a new PreJSPyParser instance."""

        self.__config = cast(Config[L, U, B], self.__class__.GetDefaultConfig())
        self.SetConfig(cast(PartialConfig[L, U, B], self.__config))

    # ============
    # MISC HELPERS
    # ============

    def __binaryPrecedence(self, op_val: str) -> int:
        """
        Returns the precedence of a binary operator or `0` if it isn't a binary operator.
        :param op_val: Value of operator to lookup.
        """

        if op_val not in self.__config["Operators"]["Binary"]:
            return 0

        return self.__config["Operators"]["Binary"][cast(B, op_val)]

    # =======
    # PARSING
    # =======

    __index: int = 0
    __length: int = 0
    __expr: str = ""

    def __exprI(self) -> str:
        if self.__index >= self.__length:
            return ""

        return self.__expr[self.__index]

    def __exprICode(self) -> int:
        if self.__index >= self.__length:
            return -1

        return ord(self.__expr[self.__index])

    def Parse(self, expr: str) -> "Expression[L, U, B]":
        """Parses an expression expr into a parse tree.

        :param expr: Expression to parse.
        """

        try:
            self.__index = 0
            self.__expr = expr
            self.__length = len(expr)

            return self.__gobbleCompound()
        finally:
            # to avoid leaks of the state
            self.__index = 0
            self.__expr = ""
            self.__length = 0

    def __gobbleCompound(self) -> "Expression[L,U,B]":
        """Gobbles a single or compound expression"""
        nodes = []
        ch_i = None
        node = None

        while self.__index < self.__length:
            ch_i = self.__exprICode()

            # Expressions can be separated by semicolons, commas, or just inferred without any separators
            if ch_i == PreJsPy.SEMCOL_CODE or ch_i == PreJsPy.COMMA_CODE:
                self.__index += 1  # ignore separators
                continue

            # Try to gobble each expression individually
            node = self.__gobbleExpression()
            if node:
                nodes.append(node)

            # didn't find an expression => something went wrong
            elif self.__index < self.__length:
                self.__throw_error('Unexpected "' + (self.__exprI()) + '"')

        # If there is only one expression, return it as is
        if len(nodes) == 1:
            return nodes[0]

        # do not allow compound expressions if they are not enabled
        if not self.__config["Features"]["Compound"]:
            self.__throw_error('Unexpected compound expression')

        return {"type": COMPOUND, "body": nodes}

    def __gobbleSpaces(self) -> None:
        """Push `index` up to the next non-space character"""
        ch = self.__exprICode()
        while ch == PreJsPy.SPACE_CODE or ch == PreJsPy.TAB_CODE:
            self.__index += 1
            ch = self.__exprICode()

    def __gobbleExpression(self) -> Optional["Expression[L,U,B]"]:
        """Main parsing function to parse any kind of expression"""

        # This function attempts to parse a tertiary expression or a binary expression.
        # But if the tertiary is turned of, we can go right into binary expressions.
        if not self.__config["Features"]["Tertiary"]:
            return self.__gobbleBinaryExpression()

        test = self.__gobbleBinaryExpression()
        consequent = None
        alternate = None
        self.__gobbleSpaces()

        # not a ternary expression => return immediately
        if self.__exprICode() != PreJsPy.QUMARK_CODE or test is None:
            return test

        if not self.__config["Features"]["Tertiary"]:
            self.__throw_error("Unexpected tertiary operator")

        #  Ternary expression: test ? consequent : alternate
        self.__index += 1
        consequent = self.__gobbleExpression()
        if not consequent:
            self.__throw_error("Expected expression")

        self.__gobbleSpaces()

        # need a ':' for the second part of the alternate
        if self.__exprICode() != PreJsPy.COLON_CODE:
            self.__throw_error("Expected :")

        self.__index += 1
        alternate = self.__gobbleExpression()

        if not alternate:
            self.__throw_error("Expected expression")

        return {
            "type": CONDITIONAL_EXP,
            "test": test,
            "consequent": consequent,
            "alternate": alternate,
        }

    # Search for the operation portion of the string (e.g. `+`, `===`)
    # Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
    # and move down from 3 to 2 to 1 character until a matching binary operation is found
    # then, return that binary operation
    def __gobbleBinaryOp(self) -> Optional[B]:
        self.__gobbleSpaces()
        to_check = self.__expr[self.__index : self.__index + self.__max_binop_len]
        tc_len = len(to_check)
        while tc_len > 0:
            if to_check in self.__config["Operators"]["Binary"]:
                self.__index += tc_len
                return cast(B, to_check)
            tc_len -= 1
            to_check = to_check[:tc_len]
        return None

    # This function is responsible for gobbling an individual expression,
    # e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
    def __gobbleBinaryExpression(self) -> Optional["Expression[L,U,B]"]:
        # First, try to get the leftmost thing
        # Then, check to see if there's a binary operator operating on that leftmost thing
        left = self.__gobbleToken()
        biop = self.__gobbleBinaryOp()

        # If there wasn't a binary operator, just return the leftmost node
        if biop is None or left is None:
            return left

        right = self.__gobbleToken()
        if not right:
            self.__throw_error("Expected expression after " + biop)

        # create a stack of expressions and information about the operators between them
        exprs = [left, right]
        ops = [
            {"value": biop, "prec": self.__binaryPrecedence(biop)}
        ]  # type: List[_BiopInfo[B]]

        # Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
        while True:
            biop = self.__gobbleBinaryOp()
            if biop is None:
                break

            prec = self.__binaryPrecedence(biop)
            if prec == 0:
                break

            # Reduce: make a binary expression from the three topmost entries.
            while (len(ops) > 0) and prec < ops[-1]["prec"]:
                right, left = exprs.pop(), exprs.pop()
                op = ops.pop()
                exprs.append(
                    {
                        "type": BINARY_EXP,
                        "operator": op["value"],
                        "left": left,
                        "right": right,
                    }
                )

            # gobble the next token in the tree
            node = self.__gobbleToken()
            if node is None:
                self.__throw_error("Expected expression after " + biop)
            exprs.append(node)

            # and store the info about the oeprator
            ops.append({"value": biop, "prec": prec})

        i = len(exprs) - 1
        j = len(ops) - 1
        node = exprs[i]
        while i > 0 and j >= 0:
            node = {
                "type": BINARY_EXP,
                "operator": ops[j]["value"],
                "left": exprs[i - 1],
                "right": node,
            }
            j -= 1
            i -= 1

        return node

    # An individual part of a binary expression:
    # e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
    def __gobbleToken(self) -> Optional["Expression[L,U,B]"]:
        ch: int = -1
        to_check = None
        tc_len = None

        self.__gobbleSpaces()
        ch = self.__exprICode()

        if self.__isDecimalDigit(ch) or ch == PreJsPy.PERIOD_CODE:
            # Char code 46 is a dot `.` which can start off a numeric literal
            return self.__gobbleNumericLiteral()
        elif ch == PreJsPy.SQUOTE_CODE or ch == PreJsPy.DQUOTE_CODE:
            # Single or double quotes
            return self.__gobbleStringLiteral()
        elif ch == PreJsPy.OBRACK_CODE:
            return self.__gobbleArray()

        to_check = self.__expr[self.__index : self.__index + self.__max_uops_len]
        tc_len = len(to_check)
        while tc_len > 0:
            if to_check in self.__config["Operators"]["Unary"]:
                self.__index += tc_len
                argument = self.__gobbleToken()
                if argument is None:
                    self.__throw_error("Expected argument to unary expression")

                return {
                    "type": UNARY_EXP,
                    "operator": cast(U, to_check),
                    "argument": argument,
                }
            tc_len -= 1
            to_check = to_check[:tc_len]

        if PreJsPy.__isIdentifierStart(ch) or ch == PreJsPy.OPAREN_CODE:
            # `foo`, `bar.baz`
            return self.__gobbleVariable()

        return None

    # Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
    # keep track of everything in the numeric literal and then calling `parseFloat` on that string
    def __gobbleNumericLiteral(self) -> Literal[L, U, B]:
        number = ""
        ch = None
        chCode = None

        while self.__isDecimalDigit(self.__exprICode()):
            number += self.__exprI()
            self.__index += 1

        if self.__exprICode() == PreJsPy.PERIOD_CODE:
            # can start with a decimal marker
            number += self.__exprI()
            self.__index += 1

            while self.__isDecimalDigit(self.__exprICode()):
                number += self.__exprI()
                self.__index += 1

        ch = self.__exprI()
        if ch == "e" or ch == "E":  # exponent marker
            number += self.__exprI()
            self.__index += 1

            ch = self.__exprI()
            if ch == "+" or ch == "-":
                # exponent sign
                number += self.__exprI()
                self.__index += 1
            while self.__isDecimalDigit(self.__exprICode()):
                # exponent itself
                number += self.__exprI()
                self.__index += 1

            self.__index -= 1
            isDecimalDigit = self.__isDecimalDigit(self.__exprICode())
            self.__index += 1

            if not isDecimalDigit:
                self.__throw_error(
                    "Expected exponent (" + number + self.__exprI() + ")"
                )

        chCode = self.__exprICode()
        # Check to make sure this isn't a variable name that start with a number (123abc)
        if PreJsPy.__isIdentifierStart(chCode):
            self.__throw_error(
                "Variable names cannot start with a number ("
                + number
                + self.__exprI()
                + ")",
            )
        elif chCode == PreJsPy.PERIOD_CODE:
            self.__throw_error("Unexpected period")

        if not self.__config["Features"]["Literals"]["Numeric"]:
            self.__index -= len(number)
            self.__throw_error("Unexpected numeric literal")

        return {"type": LITERAL, "value": float(number), "raw": number}

    # Parses a string literal, staring with single or double quotes with basic support for escape codes
    # e.g. `"hello world"`, `'this is\nJSEP'`
    def __gobbleStringLiteral(self) -> Literal[L, U, B]:
        s = ""

        index_start = self.__index

        quote = self.__exprI()
        self.__index += 1

        closed = False
        ch = None

        while self.__index < self.__length:
            ch = self.__exprI()
            self.__index += 1

            if ch == quote:
                closed = True
                break

            if ch == "\\":
                # Check for all of the common escape codes
                ch = self.__exprI()
                self.__index += 1

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
            self.__throw_error('Unclosed quote after "' + s + '"')
        if not self.__config["Features"]["Literals"]["String"]:
            self.__index = index_start
            self.__throw_error("Unexpected string literal")

        return {"type": LITERAL, "value": s, "raw": quote + s + quote}

    # Gobbles only identifiers
    # e.g.: `foo`, `_value`, `$x1`
    # Also, this function checks if that identifier is a literal:
    # (e.g. `true`, `false`, `null`)
    def __gobbleIdentifier(self) -> Union[Literal[L, U, B], Identifier[L, U, B]]:
        # can't gobble an identifier if the first character isn't the start of one.
        ch = self.__exprICode()
        if not PreJsPy.__isIdentifierStart(ch):
            self.__throw_error("Unexpected " + self.__exprI())

        # record where the identifier starts
        start = self.__index
        self.__index += 1

        # continue scanning the literal
        while self.__index < self.__length:
            ch = self.__exprICode()
            if not PreJsPy.__isIdentifierPart(ch):
                break

            self.__index += 1

        # if the identifier is a known literal, return it!
        identifier = self.__expr[start : self.__index]
        if identifier in self.__config["Operators"]["Literals"]:
            return {
                "type": LITERAL,
                "value": self.__config["Operators"]["Literals"][identifier],
                "raw": identifier,
            }

        # if identifiers are disabled, we can bail out
        if not self.__config["Features"]["Identifiers"]:
            self.__throw_error('Unknown literal "' + identifier + '"')

        # found the identifier
        return {"type": IDENTIFIER, "name": identifier}

    # Gobbles a list of arguments within the context of a function call
    # or array literal. This function also assumes that the opening character
    # `(` or `[` has already been gobbled, and gobbles expressions and commas
    # until the terminator character `)` or `]` is encountered.
    # e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
    def __gobbleArguments(self, termination: int) -> List["Expression[L,U,B]"]:
        ch_i = None
        args = []  # type: List[Expression[L,U,B]]
        node = None

        while self.__index < self.__length:
            self.__gobbleSpaces()
            ch_i = self.__exprICode()

            if ch_i == termination:
                self.__index += 1
                break

            # between expressions
            if ch_i == PreJsPy.COMMA_CODE:
                self.__index += 1
                continue

            node = self.__gobbleExpression()

            if (node is None) or node["type"] == COMPOUND:
                self.__throw_error("Expected comma")

            args.append(node)

        return args

    # Gobble a non-literal variable name. This variable name may include properties
    # e.g. `foo`, `bar.baz`, `foo['bar'].baz`
    # It also gobbles function calls:
    # e.g. `Math.acos(obj.angle)`
    def __gobbleVariable(self) -> Optional["Expression[L,U,B]"]:
        ch_i = None

        ch_i = self.__exprICode()

        if ch_i == PreJsPy.OPAREN_CODE:
            node = self.__gobbleGroup()
        else:
            node = self.__gobbleIdentifier()

        if node is None:
            return None

        self.__gobbleSpaces()

        ch_i = self.__exprICode()

        while (
            ch_i == PreJsPy.PERIOD_CODE
            or ch_i == PreJsPy.OBRACK_CODE
            or ch_i == PreJsPy.OPAREN_CODE
        ):
            self.__index += 1

            if ch_i == PreJsPy.PERIOD_CODE:
                if not self.__config["Features"]["Members"]["Static"]:
                    self.__throw_error("Unexpected static MemberExpression")

                self.__gobbleSpaces()

                node = {
                    "type": MEMBER_EXP,
                    "computed": False,
                    "object": node,
                    "property": self.__gobbleIdentifier(),
                }
            elif ch_i == PreJsPy.OBRACK_CODE:
                if not self.__config["Features"]["Members"]["Computed"]:
                    self.__throw_error("Unexpected computed MemberExpression")

                prop = self.__gobbleExpression()
                if prop is None:
                    self.__throw_error("Expected expression")

                node = {
                    "type": MEMBER_EXP,
                    "computed": True,
                    "object": node,
                    "property": prop,
                }

                self.__gobbleSpaces()

                ch_i = self.__exprICode()

                if ch_i != PreJsPy.CBRACK_CODE:
                    self.__throw_error("Unclosed [")

                self.__index += 1
            elif ch_i == PreJsPy.OPAREN_CODE:
                if not self.__config["Features"]["Calls"]:
                    self.__throw_error("Unexpected function call")
                # A function call is being made; gobble all the arguments
                node = {
                    "type": CALL_EXP,
                    "arguments": self.__gobbleArguments(PreJsPy.CPAREN_CODE),
                    "callee": node,
                }

            self.__gobbleSpaces()
            ch_i = self.__exprICode()

        return node

    # Responsible for parsing a group of things within parentheses `()`
    # This function assumes that it needs to gobble the opening parenthesis
    # and then tries to gobble everything within that parenthesis, assuming
    # that the next thing it should see is the close parenthesis. If not,
    # then the expression probably doesn't have a `)`
    def __gobbleGroup(self) -> Optional["Expression[L,U,B]"]:
        self.__index += 1
        node = self.__gobbleExpression()

        self.__gobbleSpaces()

        if self.__exprICode() != PreJsPy.CPAREN_CODE:
            self.__throw_error("Unclosed (")

        self.__index += 1
        return node

    # Responsible for parsing Array literals `[1, 2, 3]`
    # This function assumes that it needs to gobble the opening bracket
    # and then tries to gobble the expressions as arguments.
    def __gobbleArray(self) -> Ary[L, U, B]:
        if not self.__config["Features"]["Literals"]["Array"]:
            self.__throw_error("Unexpected array literal")

        self.__index += 1

        return {
            "type": ARRAY_EXP,
            "elements": self.__gobbleArguments(PreJsPy.CBRACK_CODE),
        }

    @staticmethod
    def GetDefaultConfig() -> Config[Any, str, str]:
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
                "Compound": True,
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
