"""
    (c) Tom Wiesing 2016-23, licensed under MIT license
    This code is inspired by the JavaScript version JSEP
    The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and
    licensed under MIT
"""

from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Union,
    Final,
    Literal as tLiteral,
    Optional,
    cast,
    TypedDict,
    NoReturn,
)

from enum import Enum
import json


class ExpressionType(str, Enum):
    """Represents the type of expressions"""

    COMPOUND = "Compound"
    IDENTIFIER = "Identifier"
    MEMBER_EXP = "MemberExpression"
    LITERAL = "Literal"
    CALL_EXP = "CallExpression"
    UNARY_EXP = "UnaryExpression"
    BINARY_EXP = "BinaryExpression"
    CONDITIONAL_EXP = "ConditionalExpression"
    ARRAY_EXP = "ArrayExpression"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from typing import TypeAlias
    except ImportError:
        try:
            from typing_extensions import TypeAlias
        except ImportError:
            TypeAlias = Any  # type: ignore[assignment]

    Expression: TypeAlias = Union[
        "Compound",
        "Identifier",
        "Member",
        "Literal",
        "StringLiteral",
        "NumericLiteral",
        "Call",
        "Unary",
        "Binary",
        "Condition",
        "Ary",
    ]

    class Compound(TypedDict):
        type: tLiteral[ExpressionType.COMPOUND]
        body: List[Expression]

    class Identifier(TypedDict):
        type: tLiteral[ExpressionType.IDENTIFIER]
        name: str

    class Member(TypedDict):
        type: tLiteral[ExpressionType.MEMBER_EXP]
        computed: bool
        object: Expression
        property: Expression

    class Literal(TypedDict):
        type: tLiteral[ExpressionType.LITERAL]
        value: Any
        raw: str

    class StringLiteral(TypedDict):
        type: tLiteral[ExpressionType.LITERAL]
        kind: tLiteral["string"]
        value: str
        raw: str

    class NumericLiteral(TypedDict):
        type: tLiteral[ExpressionType.LITERAL]
        kind: tLiteral["number"]
        value: float
        raw: str

    class Call(TypedDict):
        type: tLiteral[ExpressionType.CALL_EXP]
        arguments: List[Expression]
        callee: "Expression"

    class Unary(TypedDict):
        type: tLiteral[ExpressionType.UNARY_EXP]
        operator: str
        argument: Expression

    class Binary(TypedDict):
        type: tLiteral[ExpressionType.BINARY_EXP]
        operator: str
        left: Expression
        right: Expression

    class Condition(TypedDict):
        type: tLiteral[ExpressionType.CONDITIONAL_EXP]
        test: Expression
        consequent: Expression
        alternate: Expression

    class Ary(TypedDict):
        type: tLiteral[ExpressionType.ARRAY_EXP]
        elements: List[Expression]

    class _BinaryOperatorInfo(TypedDict):
        value: str
        precedence: int

    class _OperatorsConfig(TypedDict):
        Literals: Dict[str, Any]
        Unary: List[str]
        Binary: Dict[str, int]

    class _PartialOperatorsConfig(TypedDict, total=False):
        Literals: Dict[str, Any]
        Unary: List[str]
        Binary: Dict[str, int]

    class _Members(TypedDict):
        Static: bool
        Computed: bool

    class _PartialMembers(TypedDict, total=False):
        Static: bool
        Computed: bool

    class _Literals(TypedDict):
        Numeric: bool
        NumericSeparator: str
        String: bool
        Array: bool

    class _PartialLiterals(TypedDict, total=False):
        Numeric: bool
        NumericSeparator: str
        String: bool
        Array: bool

    class _Features(TypedDict):
        Compound: bool
        Conditional: bool
        Identifiers: bool
        Calls: bool
        Members: _Members
        Literals: _Literals

    class _PartialFeatures(TypedDict, total=False):
        Compound: bool
        Conditional: bool
        Identifiers: bool
        Calls: bool
        Members: _PartialMembers
        Literals: _PartialLiterals

    class Config(TypedDict):
        """Configuration represents the configuration of a PreJsPy instance"""

        Operators: _OperatorsConfig
        Features: _Features

    class PartialConfig(TypedDict, total=False):
        Operators: _PartialOperatorsConfig
        Features: _PartialFeatures


class ParsingError(Exception):
    error: str
    expr: str
    index: int

    def __init__(self, error: str, expr: str, index: int):
        """
        Creates a new ParsingError.

        :param error: Error message produced by the parser
        :param expr: Expression that was originally parsed
        :param index: Index of position in the expression where the error occurred
        """
        self.error = error
        self.expr = expr
        self.index = index

        super().__init__(
            "Index " + str(index) + " of " + json.dumps(expr) + ": " + error
        )


class PreJsPy(object):
    """Represents a single instance of the PreJSPy Parser."""

    # List of char codes.
    __CHAR_PERIOD: Final = "."
    __CHAR_COMMA: Final = ","
    __CHAR_SINGLE_QUOTE: Final = "'"
    __CHAR_DOUBLE_QUOTE: Final = '"'
    __CHAR_OPEN_PARENTHESES: Final = "("
    __CHAR_CLOSE_PARENTHESES: Final = ")"
    __CHAR_OPEN_BRACKET: Final = "["
    __CHAR_CLOSE_BRACKET: Final = "]"
    __CHAR_QUESTIONMARK: Final = "?"
    __CHAR_SEMICOLON: Final = ";"
    __CHAR_COLON: Final = ":"
    __CHAR_SPACE: Final = " "
    __CHAR_TAB: Final = "\t"

    # =======================
    # STATIC HELPER FUNCTIONS
    # =======================
    def __throw_error(self, error: str) -> NoReturn:
        """Throws a parser error with a given message and a given index.

        :param error: Message of error to throw.
        :param index: Character index at which the error should be thrown.
        """
        raise ParsingError(error, self.__expr, self.__index)

    @staticmethod
    def __getMaxKeyLen(o: Dict[str, int]) -> int:
        """Gets the longest key length of an object

        :param o: Object to iterate over
        """

        if len(o.keys()) == 0:
            return 0
        return max(map(len, o.keys()))

    @staticmethod
    def __getMaxMemLen(ary: List[str]) -> int:
        """Gets the maximum length of the member of any members of an array.

        :param ary: Array to iterate over.
        """
        if len(ary) == 0:
            return 0
        return max(map(len, ary))

    @staticmethod
    def __isDecimalDigit(ch: str) -> bool:
        """Checks if a character is a decimal digit.

        :param ch: Character to check
        """

        return len(ch) == 1 and ch >= "0" and ch <= "9"  # 0...9

    @staticmethod
    def __isIdentifierStart(ch: str) -> bool:
        """Checks if a character is the start of an identifier.

        :param ch: Character to check
        """

        return len(ch) == 1 and (
            (ch == "$")
            or (ch == "_")
            or (ch >= "A" and ch <= "Z")
            or (ch >= "a" and ch <= "z")
            or (ord(ch) >= 128)  # non-ascii
        )

    @staticmethod
    def __isIdentifierPart(ch: str) -> bool:
        """Checks if a character is part of an identifier.

        :param ch: Character to check
        """

        # `$`,  `_`, A...Z, a...z and 0...9 and non-ascii
        return len(ch) == 1 and (
            (ch == "$")
            or (ch == "_")
            or (ch >= "A" and ch <= "Z")
            or (ch >= "a" and ch <= "z")
            or (ch >= "0" and ch <= "9")
            or (ord(ch) >= 128)  # non-ascii
        )

    # =======
    # CONFIG
    # =======

    def GetConfig(self) -> "Config":
        """Gets the current config used by this parser."""
        return {
            "Operators": {
                "Literals": self.__config["Operators"]["Literals"].copy(),
                "Unary": self.__config["Operators"]["Unary"].copy(),
                "Binary": self.__config["Operators"]["Binary"].copy(),
            },
            "Features": {
                "Compound": self.__config["Features"]["Compound"],
                "Conditional": self.__config["Features"]["Conditional"],
                "Identifiers": self.__config["Features"]["Identifiers"],
                "Calls": self.__config["Features"]["Calls"],
                "Members": self.__config["Features"]["Members"].copy(),
                "Literals": self.__config["Features"]["Literals"].copy(),
            },
        }

    def SetConfig(self, config: Optional["PartialConfig"]) -> "Config":
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
                    self.__unaryOperatorLength = PreJsPy.__getMaxMemLen(
                        self.__config["Operators"]["Unary"]
                    )
                if "Binary" in config["Operators"]:
                    self.__config["Operators"]["Binary"] = config["Operators"][
                        "Binary"
                    ].copy()
                    self.__binaryOperatorLength = PreJsPy.__getMaxKeyLen(
                        self.__config["Operators"]["Binary"]
                    )
            if "Features" in config:
                if "Compound" in config["Features"]:
                    self.__config["Features"]["Compound"] = config["Features"][
                        "Compound"
                    ]
                if "Conditional" in config["Features"]:
                    self.__config["Features"]["Conditional"] = config["Features"][
                        "Conditional"
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
                    if "NumericSeparator" in config["Features"]["Literals"]:
                        self.__config["Features"]["Literals"][
                            "NumericSeparator"
                        ] = config["Features"]["Literals"]["NumericSeparator"]
                    if "String" in config["Features"]["Literals"]:
                        self.__config["Features"]["Literals"]["String"] = config[
                            "Features"
                        ]["Literals"]["String"]

        return self.GetConfig()

    # =========
    # INIT CODE
    # =========

    __config: "Config"
    __unaryOperatorLength: int
    __binaryOperatorLength: int

    def __init__(self) -> None:
        """Creates a new PreJSPyParser instance."""

        self.__config = self.__class__.GetDefaultConfig()
        self.SetConfig(cast("PartialConfig", self.__config))

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

        return self.__config["Operators"]["Binary"][op_val]

    # =======
    # PARSING
    # =======

    __index: int = 0
    __length: int = 0
    __expr: str = ""

    def __char(self) -> str:
        if self.__index >= self.__length:
            return ""

        return self.__expr[self.__index]

    def Parse(self, expr: str) -> "Expression":
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

    def TryParse(
        self, expr: str
    ) -> "Union[Tuple[Expression, None],Tuple[None, ParsingError]]":
        try:
            result = self.Parse(expr)
            return result, None
        except ParsingError as pe:
            return None, pe

    def __gobbleCompound(self) -> "Expression":
        """Gobbles a single or compound expression"""
        nodes = []

        while self.__index < self.__length:
            ch = self.__char()

            # Expressions can be separated by semicolons, commas, or just inferred without any separators
            if ch == PreJsPy.__CHAR_SEMICOLON or ch == PreJsPy.__CHAR_COMMA:
                self.__index += 1  # ignore separators
                continue

            # Try to gobble each expression individually
            node = self.__gobbleExpression()
            if node is None:
                break

            nodes.append(node)

        # didn't find an expression => something went wrong
        if self.__index < self.__length:
            self.__throw_error("Unexpected " + json.dumps(self.__char()))

        # If there is only one expression, return it as is
        if len(nodes) == 1:
            return nodes[0]

        # do not allow compound expressions if they are not enabled
        if not self.__config["Features"]["Compound"]:
            self.__throw_error("Unexpected compound expression")

        return {"type": ExpressionType.COMPOUND, "body": nodes}

    def __gobbleSpaces(self) -> None:
        """Push `index` up to the next non-space character"""
        ch = self.__char()
        while ch == PreJsPy.__CHAR_SPACE or ch == PreJsPy.__CHAR_TAB:
            self.__index += 1
            ch = self.__char()

    def __gobbleExpression(self) -> Optional["Expression"]:
        """Main parsing function to parse any kind of expression"""

        # This function attempts to parse a conditional expression or a binary expression.
        # But if the conditional is turned of, we can go right into binary expressions.
        if not self.__config["Features"]["Conditional"]:
            return self.__gobbleBinaryExpression()

        test = self.__gobbleBinaryExpression()
        self.__gobbleSpaces()

        # not a ternary expression => return immediately
        if self.__char() != PreJsPy.__CHAR_QUESTIONMARK or test is None:
            return test

        #  Ternary expression: test ? consequent : alternate
        self.__index += 1
        consequent = self.__gobbleExpression()
        if not consequent:
            self.__throw_error("Expected expression")

        self.__gobbleSpaces()

        # need a ':' for the second part of the alternate
        if self.__char() != PreJsPy.__CHAR_COLON:
            self.__throw_error("Expected " + json.dumps(PreJsPy.__CHAR_COLON))

        self.__index += 1
        alternate = self.__gobbleExpression()

        if not alternate:
            self.__throw_error("Expected expression")

        return {
            "type": ExpressionType.CONDITIONAL_EXP,
            "test": test,
            "consequent": consequent,
            "alternate": alternate,
        }

    # Search for the operation portion of the string (e.g. `+`, `===`)
    # Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
    # and move down from 3 to 2 to 1 character until a matching binary operation is found
    # then, return that binary operation
    def __gobbleBinaryOp(self) -> Optional[str]:
        self.__gobbleSpaces()
        to_check = self.__expr[
            self.__index : self.__index + self.__binaryOperatorLength
        ]
        tc_len = len(to_check)
        while tc_len > 0:
            if to_check in self.__config["Operators"]["Binary"]:
                self.__index += tc_len
                return to_check
            tc_len -= 1
            to_check = to_check[:tc_len]
        return None

    # This function is responsible for gobbling an individual expression,
    # e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
    def __gobbleBinaryExpression(self) -> Optional["Expression"]:
        # get the leftmost token of a binary expression or bail out
        left = self.__gobbleToken()
        if left is None:
            return left

        exprs = [left]  # a list of expressions
        # and a list of binary operators between them
        ops = []  # type: List[_BinaryOperatorInfo]

        # Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
        while True:
            value = self.__gobbleBinaryOp()
            if value is None:
                break

            precedence = self.__binaryPrecedence(value)
            if precedence == 0:
                break

            # Reduce: make a binary expression from the three topmost entries.
            while (len(ops) > 0) and precedence < ops[-1]["precedence"]:
                right, left = exprs.pop(), exprs.pop()
                op = ops.pop()
                exprs.append(
                    {
                        "type": ExpressionType.BINARY_EXP,
                        "operator": op["value"],
                        "left": left,
                        "right": right,
                    }
                )

            # gobble the next token in the tree
            node = self.__gobbleToken()
            if node is None:
                self.__throw_error("Expected expression after " + json.dumps(value))
            exprs.append(node)

            # and store the info about the operator
            ops.append({"value": value, "precedence": precedence})

        i = len(exprs) - 1
        j = len(ops) - 1
        node = exprs[i]
        while i > 0 and j >= 0:
            node = {
                "type": ExpressionType.BINARY_EXP,
                "operator": ops[j]["value"],
                "left": exprs[i - 1],
                "right": node,
            }
            j -= 1
            i -= 1

        return node

    # An individual part of a binary expression:
    # e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
    def __gobbleToken(self) -> Optional["Expression"]:
        self.__gobbleSpaces()
        ch = self.__char()

        # numeric literals
        if self.__config["Features"]["Literals"]["Numeric"] and (
            self.__isDecimalDigit(ch) or ch == PreJsPy.__CHAR_PERIOD
        ):
            return self.__gobbleNumericLiteral()

        # single or double quoted strings
        if self.__config["Features"]["Literals"]["String"] and (
            ch == PreJsPy.__CHAR_SINGLE_QUOTE or ch == PreJsPy.__CHAR_DOUBLE_QUOTE
        ):
            return self.__gobbleStringLiteral()

        # array literal
        if (
            self.__config["Features"]["Literals"]["Array"]
            and ch == PreJsPy.__CHAR_OPEN_BRACKET
        ):
            return self.__gobbleArray()

        to_check = self.__expr[self.__index : self.__index + self.__unaryOperatorLength]
        tc_len = len(to_check)
        while tc_len > 0:
            if to_check in self.__config["Operators"]["Unary"]:
                self.__index += tc_len
                argument = self.__gobbleToken()
                if argument is None:
                    self.__throw_error("Expected argument for unary expression")

                return {
                    "type": ExpressionType.UNARY_EXP,
                    "operator": to_check,
                    "argument": argument,
                }
            tc_len -= 1
            to_check = to_check[:tc_len]

        if PreJsPy.__isIdentifierStart(ch) or ch == PreJsPy.__CHAR_OPEN_PARENTHESES:
            return self.__gobbleVariable()

        return None

    # Gobbles a contiguous sequence of decimal numbers, possibly separated with numeric separators.
    # The returned string does not include numeric separators
    def __gobbleDecimal(self) -> str:
        # Fast path: No separator enabled case: no numeric separator
        separator = self.__config["Features"]["Literals"]["NumericSeparator"]
        if separator == "":
            start = self.__index
            while self.__isDecimalDigit(self.__char()):
                self.__index += 1
            return self.__expr[start : self.__index]

        # slow path: need to check for separator
        number = ""
        while True:
            # iterate over decimal digit
            digit = self.__char()
            if self.__isDecimalDigit(digit):
                number += digit
            elif digit != separator:
                break

            self.__index += 1

        return number

    # Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
    # keep track of everything in the numeric literal and then calling `parseFloat` on that string
    def __gobbleNumericLiteral(self) -> "NumericLiteral":
        start = self.__index

        # gobble the number itself
        number = self.__gobbleDecimal()

        if self.__char() == PreJsPy.__CHAR_PERIOD:
            # can start with a decimal marker
            number += self.__char()
            self.__index += 1

            number += self.__gobbleDecimal()

        ch = self.__char()
        if ch == "e" or ch == "E":  # exponent marker
            number += self.__char()
            self.__index += 1

            ch = self.__char()
            if ch == "+" or ch == "-":
                # exponent sign
                number += self.__char()
                self.__index += 1

            # exponent itself
            exponent = self.__gobbleDecimal()
            if exponent == "":
                self.__throw_error(
                    "Expected exponent after " + json.dumps(number + self.__char())
                )

            number += exponent

        ch = self.__char()
        # Check to make sure this isn't a variable name that start with a number (123abc)
        if PreJsPy.__isIdentifierStart(ch):
            self.__throw_error(
                "Variable names cannot start with a number like "
                + json.dumps(number + ch),
            )

        # parse the float value and get the literal (if needed)
        value = float(number)
        if self.__config["Features"]["Literals"]["NumericSeparator"] != "":
            number = self.__expr[start : self.__index]

        return {
            "type": ExpressionType.LITERAL,
            "kind": "number",
            "value": value,
            "raw": number,
        }

    # Parses a string literal, staring with single or double quotes with basic support for escape codes
    # e.g. `"hello world"`, `'this is\nJSEP'`
    def __gobbleStringLiteral(self) -> "StringLiteral":
        s = ""

        start = self.__index

        quote = self.__char()
        self.__index += 1

        closed = False

        while self.__index < self.__length:
            ch = self.__char()
            self.__index += 1

            if ch == quote:
                closed = True
                break

            if ch == "\\":
                # Check for all of the common escape codes
                ch = self.__char()
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
            self.__throw_error("Unclosed quote after " + json.dumps(s))

        return {
            "type": ExpressionType.LITERAL,
            "kind": "string",
            "value": s,
            "raw": self.__expr[start : self.__index],
        }

    # Gobbles only identifiers
    # e.g.: `foo`, `_value`, `$x1`
    # Also, this function checks if that identifier is a literal:
    # (e.g. `true`, `false`, `null`)
    def __gobbleIdentifier(self) -> "Union[Literal, Identifier]":
        # can't gobble an identifier if the first character isn't the start of one.
        ch = self.__char()
        if ch == "":
            self.__throw_error("Expected literal")

        if not PreJsPy.__isIdentifierStart(ch):
            self.__throw_error("Unexpected " + json.dumps(ch))

        # record where the identifier starts
        start = self.__index
        self.__index += 1

        # continue scanning the literal
        while self.__index < self.__length:
            ch = self.__char()
            if not PreJsPy.__isIdentifierPart(ch):
                break

            self.__index += 1

        # if the identifier is a known literal, return it!
        identifier = self.__expr[start : self.__index]
        if identifier in self.__config["Operators"]["Literals"]:
            return {
                "type": ExpressionType.LITERAL,
                "value": self.__config["Operators"]["Literals"][identifier],
                "raw": identifier,
            }

        # if identifiers are disabled, we can bail out
        if not self.__config["Features"]["Identifiers"]:
            self.__throw_error('Unknown literal "' + identifier + '"')

        # found the identifier
        return {"type": ExpressionType.IDENTIFIER, "name": identifier}

    # Gobbles a list of arguments within the context of a function call
    # or array literal. This function also assumes that the opening character
    # `(` or `[` has already been gobbled, and gobbles expressions and commas
    # until the terminator character `)` or `]` is encountered.
    # e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
    def __gobbleArguments(self, start: str, end: str) -> List["Expression"]:
        args = []  # type: List[Expression]

        closed = False  # is the expression closed?
        hadComma = False  # did we have a comma in the last iteration?

        while self.__index < self.__length:
            self.__gobbleSpaces()
            ch = self.__char()

            if ch == end:
                closed = True
                self.__index += 1
                break

            # between expressions
            if ch == PreJsPy.__CHAR_COMMA:
                if hadComma:
                    self.__throw_error("Duplicate " + json.dumps(PreJsPy.__CHAR_COMMA))
                hadComma = True
                self.__index += 1
                continue

            wantsComma = len(args) > 0
            if wantsComma != hadComma:
                if wantsComma:
                    self.__throw_error("Expected " + json.dumps(PreJsPy.__CHAR_COMMA))
                else:
                    self.__throw_error("Unexpected " + json.dumps(PreJsPy.__CHAR_COMMA))

            node = self.__gobbleExpression()

            if (node is None) or node["type"] == ExpressionType.COMPOUND:
                self.__throw_error("Expected " + json.dumps(PreJsPy.__CHAR_COMMA))

            args.append(node)
            hadComma = False

        if not closed:
            self.__throw_error("Unclosed " + json.dumps(start))

        return args

    # Gobble a non-literal variable name. This variable name may include properties
    # e.g. `foo`, `bar.baz`, `foo['bar'].baz`
    # It also gobbles function calls:
    # e.g. `Math.acos(obj.angle)`
    def __gobbleVariable(self) -> Optional["Expression"]:
        # parse a group or identifier first
        ch = self.__char()
        if ch == PreJsPy.__CHAR_OPEN_PARENTHESES:
            node = self.__gobbleGroup()
        else:
            node = self.__gobbleIdentifier()

        if node is None:
            return None

        # then iterate over operations applied to it
        while True:
            self.__gobbleSpaces()
            ch = self.__char()

            self.__index += 1

            # access via .
            if (
                self.__config["Features"]["Members"]["Static"]
                and ch == PreJsPy.__CHAR_PERIOD
            ):
                self.__gobbleSpaces()

                node = {
                    "type": ExpressionType.MEMBER_EXP,
                    "computed": False,
                    "object": node,
                    "property": self.__gobbleIdentifier(),
                }
                continue

            # access via []s
            if (
                self.__config["Features"]["Members"]["Computed"]
                and ch == PreJsPy.__CHAR_OPEN_BRACKET
            ):
                prop = self.__gobbleExpression()
                if prop is None:
                    self.__throw_error("Expected expression")

                node = {
                    "type": ExpressionType.MEMBER_EXP,
                    "computed": True,
                    "object": node,
                    "property": prop,
                }

                self.__gobbleSpaces()

                ch = self.__char()
                if ch != PreJsPy.__CHAR_CLOSE_BRACKET:
                    self.__throw_error(
                        "Unclosed " + json.dumps(PreJsPy.__CHAR_OPEN_BRACKET)
                    )

                self.__index += 1

                continue

            # call with ()s
            if (
                self.__config["Features"]["Calls"]
                and ch == PreJsPy.__CHAR_OPEN_PARENTHESES
            ):
                node = {
                    "type": ExpressionType.CALL_EXP,
                    "arguments": self.__gobbleArguments(
                        PreJsPy.__CHAR_OPEN_PARENTHESES,
                        PreJsPy.__CHAR_CLOSE_PARENTHESES,
                    ),
                    "callee": node,
                }
                continue

            # done
            self.__index -= 1
            break

        return node

    # Responsible for parsing a group of things within parentheses `()`
    # This function assumes that it needs to gobble the opening parenthesis
    # and then tries to gobble everything within that parenthesis, assuming
    # that the next thing it should see is the close parenthesis. If not,
    # then the expression probably doesn't have a `)`
    def __gobbleGroup(self) -> Optional["Expression"]:
        self.__index += 1
        node = self.__gobbleExpression()

        self.__gobbleSpaces()

        if self.__char() != PreJsPy.__CHAR_CLOSE_PARENTHESES:
            self.__throw_error(
                "Unclosed " + json.dumps(PreJsPy.__CHAR_OPEN_PARENTHESES)
            )

        self.__index += 1
        return node

    # Responsible for parsing Array literals `[1, 2, 3]`
    # This function assumes that it needs to gobble the opening bracket
    # and then tries to gobble the expressions as arguments.
    def __gobbleArray(self) -> "Ary":
        self.__index += 1

        return {
            "type": ExpressionType.ARRAY_EXP,
            "elements": self.__gobbleArguments(
                PreJsPy.__CHAR_OPEN_BRACKET, PreJsPy.__CHAR_CLOSE_BRACKET
            ),
        }

    @staticmethod
    def GetDefaultConfig() -> "Config":
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
                "Conditional": True,
                "Identifiers": True,
                "Calls": True,
                "Members": {
                    "Static": True,
                    "Computed": True,
                },
                "Literals": {
                    "Numeric": True,
                    "NumericSeparator": "",
                    "String": True,
                    "Array": True,
                },
            },
        }


# cSpell:words JSEP Oney
