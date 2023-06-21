// Type definitions for PreJsPy
// (c) Tom Wiesing 2016-20, licensed under MIT license
// This code is heavily based on the JavaScript version JSEP
// The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT

export as namespace PreJsPy;

/**
 * An Expression represents a parsed tree for PreJSPy. 
 * @tparam L is the type of literals
 * @tparam U is the type of unary expressions
 * @tparam B is the type of binary expressions
 */
export type Expression<L, U extends string, B extends string> = 
    Identifier |
    Literal<L> |
    Compound<L, U, B> |
    Member<L, U, B> | 
    Call<L, U, B> |
    Unary<L, U, B> |
    Binary<L, U, B> |
    Condition<L, U, B> |
    Ary<L, U, B>;

interface Compound<L, U extends string, B extends string> {
    type: "Compound";
    body: Expression<L, U, B>[];
}


interface Identifier {
    type: "Identifier";
    name: string;
}

interface Member<L, U extends string, B extends string> {
    type: "MemberExpression";
    computed: boolean;
    object: Expression<L, U, B>,
    name: Expression<L, U, B>,
}

interface Literal<L> {
    type: "Literal";
    value: L | number;
    raw: true;
}

interface Call<L, U extends string, B extends string> {
    type: "CallExpression";
    arguments: Expression<L, U, B>[];
    callee: Expression<L, U, B>;
}

interface Unary<L, U extends string, B extends string> {
    type: "UnaryExpression";
    operator: U;
    argument: Expression<L, U, B>;
}

interface Binary<L, U extends string, B extends string> {
    type: "BinaryExpression";
    operator: B;
    left: Expression<L, U, B>;
    right: Expression<L, U, B>;
}

interface Condition<L, U extends string, B extends string> {
    type: "ConditionalExpression";
    test: Expression<L, U, B>;
    consequent: Expression<L, U, B>;
    alternate: Expression<L, U, B>;
}

interface Ary<L, U extends string, B extends string> {
    type: "ArrayExpression";
    elements: Expression<L, U, B>[];
}

export class PreJsPy<L extends boolean | null, U extends string, B extends string> {
    getConstants(): Record<string, L>
    setConstants(constants: Record<string, L>): Record<string, L>

    getUnaryOperators(): U[]
    getMaxUnaryOperatorsLength(): number;
    setUnaryOperators(operators: U[]): U[]

    getBinaryOperators(): Record<B, number>; 
    getMaxBinaryOperatorsLength(): number
    setBinaryOperators(operators: Record<B, number>): Record<B, number>

    getTertiaryOperatorEnabled(): boolean
    setTertiaryOperatorEnabled(enabled: boolean): boolean;

    getIdentifiersEnabled(): boolean
    setIdentifiersEnabled(enabled: boolean): boolean;

    parse(source: string): Expression<L, U, B>
}