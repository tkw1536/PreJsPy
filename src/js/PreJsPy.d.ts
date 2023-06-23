// Type definitions for PreJsPy
// (c) Tom Wiesing 2016-20, licensed under MIT license
// This code is heavily based on the JavaScript version JSEP
// The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT

export as namespace PreJsPy;

/**
 * An Expression represents a parsed tree for PreJSPy. 
 * @template L is the type of literals
 * @template U is the type of unary expressions
 * @template B is the type of binary expressions
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

export type ParsingError = Error & {
    index?: number
    description?: string
}

type Compound<L, U extends string, B extends string> = {
    type: "Compound";
    body: Expression<L, U, B>[];
}


type Identifier = {
    type: "Identifier";
    name: string;
}

type Member<L, U extends string, B extends string> = {
    type: "MemberExpression";
    computed: boolean;
    object: Expression<L, U, B>,
    property: Expression<L, U, B>,
}

type Literal<L> = {
    type: "Literal";
    value: L | number;
    raw: string;
}

type Call<L, U extends string, B extends string> = {
    type: "CallExpression";
    arguments: Expression<L, U, B>[];
    callee: Expression<L, U, B>;
}

type Unary<L, U extends string, B extends string> = {
    type: "UnaryExpression";
    operator: U;
    argument: Expression<L, U, B>;
}

type Binary<L, U extends string, B extends string> = {
    type: "BinaryExpression";
    operator: B;
    left: Expression<L, U, B>;
    right: Expression<L, U, B>;
}

type Condition<L, U extends string, B extends string> = {
    type: "ConditionalExpression";
    test: Expression<L, U, B>;
    consequent: Expression<L, U, B>;
    alternate: Expression<L, U, B>;
}

type Ary<L, U extends string, B extends string> = {
    type: "ArrayExpression";
    elements: Expression<L, U, B>[];
}


/** Config represents a configuration of the parser */
type Config<L extends boolean | null, U extends string, B extends string> = {
    Operators: {
        Literals: Record<string, L>,
        Unary: U[],
        Binary: Record<B, number>,
    }

    Features: {
        Tertiary: boolean;
        Identifiers: boolean;
        Calls: boolean;
        Members: { 
            Static: boolean; // TODO
            Computed: boolean; // TODO
        };
        Literals: {
            Numeric: boolean;
            String: boolean;
            Array: boolean;
        }
    }
}

type PartialConfig<L extends boolean | null, U extends string, B extends string> = Partial<{
    Operators: Partial<Config<L,U,B>["Operators"]>
    Features: {
        Tertiary?: boolean;
        Identifiers?: boolean;
        Calls?: boolean;
        Members?: Partial<{
            Static: boolean;
            Computed: boolean;
        }>
        Literals?: Partial<{
            Numeric: boolean;
            String: boolean;
            Array: boolean;
        }>
    }
}>


export class PreJsPy<L extends boolean | null, U extends string, B extends string> {
    parse(source: string): Expression<L, U, B>

    getConfig(): Config<L,U,B>
    setConfig(config: PartialConfig<L,U,B>): Config<L,U,B>

    /** @deprecated */
    getConstants(): PreJsPy.Config<L,U,B>["Operators"]["Literals"]
    /** @deprecated */
    setConstants(constants: PreJsPy.Config<L,U,B>["Operators"]["Literals"]): PreJsPy.Config<L,U,B>["Operators"]["Literals"]

    static getDefaultConfig<L extends boolean | null, U extends string, B extends string>(): Config<L, U, B>;

    /** @deprecated */
    getUnaryOperators(): U[]
    /** @deprecated */
    getMaxUnaryOperatorsLength(): number;
    /** @deprecated */
    setUnaryOperators(operators: U[]): U[]

    /** @deprecated */
    getBinaryOperators(): Record<B, number>;
    /** @deprecated */
    getMaxBinaryOperatorsLength(): number
    /** @deprecated */
    setBinaryOperators(operators: Record<B, number>): Record<B, number>

    /** @deprecated */
    getTertiaryOperatorEnabled(): boolean
    /** @deprecated */
    setTertiaryOperatorEnabled(enabled: boolean): boolean
}