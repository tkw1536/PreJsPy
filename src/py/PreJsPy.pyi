from abc import ABC

from typing import Final, Generic
from typing import Literal as tLiteral
from typing import Sequence, TypeAlias, TypedDict, TypeVar, Union

L = TypeVar('L')
U = TypeVar('U', bound=str)
B = TypeVar('B', bound=str)

class Expression(TypedDict, Generic[L,U,B]):
    pass

class Compound(Expression[L,U,B]):
    type: tLiteral['Compound']
    body: Sequence[Expression[L,U,B]]
class Identifier(TypedDict):
    type: tLiteral['Identifier']
    name: str

class Member(Expression[L,U,B]):
    type: tLiteral['MemberExpression']
    computed: bool
    object: Expression[L,U,B]
    property: Expression[L,U,B]

class Literal(Expression[L,U,B]):
    type: tLiteral['Literal']
    value: L | float | str
    raw: str

class Call(Expression[L,U,B]):
    type: tLiteral['CallExpression']
    arguments: Sequence[Expression[L,U,B]]
    callee: Expression[L,U,B]

class Unary(Expression[L,U,B]):
    type: tLiteral['UnaryExpression']
    operator: U
    argument: Expression[L,U,B]

class Binary(Expression[L,U,B]):
    type: tLiteral['BinaryExpression']
    operator: B
    left: Expression[L,U,B]
    right: Expression[L,U,B]

class Condition(Expression[L,U,B]):
    type: tLiteral['ConditionalExpression']
    test: Expression
    consequent: Expression
    alternate: Expression

class Ary(Expression[L,U,B]):
    type: tLiteral['ArrayExpression']
    elements: Sequence[Expression]

Config: TypeAlias = dict

class PreJsPy:
    COMPOUND: Final[str]
    IDENTIFIER: Final[str]
    MEMBER_EXP: Final[str]
    LITERAL: Final[str]
    CALL_EXP: Final[str]
    UNARY_EXP: Final[str]
    BINARY_EXP: Final[str]
    CONDITIONAL_EXP: Final[str]
    ARRAY_EXP: Final[str]

    def __init__(self) -> None: ...
    def parse(self, expr: str) -> Expression: ...
    
    def getConfig(self) -> Config: ...
    def setConfig(self, config: Config) -> Config: ...

    def getConstants(self) -> dict[str, L]: ...
    def setConstants(self, d: dict[str, L]) -> dict[str, L]: ...
    def getUnaryOperators(self) -> list[U]: ...
    def setUnaryOperators(self, ary: list[U]) -> list[U]: ...
    def getBinaryOperators(self) -> dict[B, int]: ...
    def setBinaryOperators(self, d: dict[B, int]) -> dict[B, int]: ...
    def getTertiaryOperatorEnabled(self) -> bool: ...
    def setTertiaryOperatorEnabled(self, e: bool) -> bool: ...
    def getIdentifiersEnabled(self) -> bool: ...
    def setIdentifiersEnabled(self, e: bool) -> bool: ...


__all__ = ["PreJsPy"]