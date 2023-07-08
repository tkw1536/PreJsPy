/**
 * (c) Tom Wiesing 2016-23, licensed under MIT license
 *
 * This code is heavily based on the JavaScript version JSEP.
 * The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT.
 *
 * @license MIT
 */

/**
 * An Expression represents a parsed tree for PreJSPy.
 * @template L is the type of literals
 * @template U is the type of unary expressions
 * @template B is the type of binary expressions
 */
export type Expression<L, U extends string, B extends string> =
    Identifier |
    Literal<L> |
    StringLiteral |
    NumericLiteral |
    Compound<L, U, B> |
    Member<L, U, B> |
    Call<L, U, B> |
    Unary<L, U, B> |
    Binary<L, U, B> |
    Condition<L, U, B> |
    Ary<L, U, B>

class ParsingError extends Error {
  readonly error: string
  readonly expr: string
  readonly index: number

  /**
     * Creates a new ParsingError.
     *
     * @param error Error message produced by the parser
     * @param expr Expression that was originally parsed
     * @param index Index of position in expression where the error occurred
     */
  constructor (error: string, expr: string, index: number) {
    super('Index ' + index.toString() + ' of ' + JSON.stringify(expr) + ': ' + error)

    this.error = error
    this.expr = expr
    this.index = index
  }
}

interface Compound<L, U extends string, B extends string> {
  type: 'Compound'
  body: Array<Expression<L, U, B>>
}

interface Identifier {
  type: 'Identifier'
  name: string
}

interface Member<L, U extends string, B extends string> {
  type: 'MemberExpression'
  computed: boolean
  object: Expression<L, U, B>
  property: Expression<L, U, B>
}

interface Literal<L> {
  type: 'Literal'
  value: L
  raw: string
}

interface StringLiteral {
  type: 'Literal'
  kind: 'string'
  value: string
  raw: string
}

interface NumericLiteral {
  type: 'Literal'
  kind: 'number'
  value: number
  raw: string
}

interface Call<L, U extends string, B extends string> {
  type: 'CallExpression'
  arguments: Array<Expression<L, U, B>>
  callee: Expression<L, U, B>
}

interface Unary<L, U extends string, B extends string> {
  type: 'UnaryExpression'
  operator: U
  argument: Expression<L, U, B>
}

interface Binary<L, U extends string, B extends string> {
  type: 'BinaryExpression'
  operator: B
  left: Expression<L, U, B>
  right: Expression<L, U, B>
}

interface Condition<L, U extends string, B extends string> {
  type: 'ConditionalExpression'
  test: Expression<L, U, B>
  consequent: Expression<L, U, B>
  alternate: Expression<L, U, B>
}

interface Ary<L, U extends string, B extends string> {
  type: 'ArrayExpression'
  elements: Array<Expression<L, U, B>>
}

/**
 * Configuration for PreJsPy.
 */
export interface Config<L extends boolean | null, U extends string, B extends string> {
  Operators: {
    Literals: Record<string, L>
    Unary: U[]
    Binary: Record<B, number>
  }

  Features: {
    Compound: boolean
    Tertiary: boolean
    Identifiers: boolean
    Calls: boolean
    Members: {
      Static: boolean
      Computed: boolean
    }
    Literals: {
      Numeric: boolean
      NumericSeparator: string
      String: boolean
      Array: boolean
    }
  }
}

export type PartialConfig<L extends boolean | null, U extends string, B extends string> = Partial<{
  Operators: Partial<Config<L, U, B>['Operators']>
  Features: Partial<{
    Compound: boolean
    Tertiary: boolean
    Identifiers: boolean
    Calls: boolean
    Members: Partial<{
      Static: boolean
      Computed: boolean
    }>
    Literals: Partial<{
      Numeric: boolean
      NumericSeparator: string
      String: boolean
      Array: boolean
    }>
  }>
}>

const COMPOUND = 'Compound'
const IDENTIFIER = 'Identifier'
const MEMBER_EXP = 'MemberExpression'
const LITERAL = 'Literal'
const CALL_EXP = 'CallExpression'
const UNARY_EXP = 'UnaryExpression'
const BINARY_EXP = 'BinaryExpression'
const CONDITIONAL_EXP = 'ConditionalExpression'
const ARRAY_EXP = 'ArrayExpression'

// LIST OF CHAR CODES
const PERIOD_CODE = 46 // '.'
const COMMA_CODE = 44 // ','
const SQUOTE_CODE = 39 // single quote
const DQUOTE_CODE = 34 // double quotes
const OPAREN_CODE = 40 // (
const CPAREN_CODE = 41 // )
const OBRACK_CODE = 91 // [
const CBRACK_CODE = 93 // ]
const QUMARK_CODE = 63 // ?
const SEMCOL_CODE = 59 // ;
const COLON_CODE = 58 // :

/** ParsingResult represents a result from parsing */
type ParsingResult<T> = [T, null] | [null, ParsingError]

export class PreJsPy<L extends boolean | null, U extends string, B extends string> {
  /**
     * Throws a parser error with a given message and a given index.
     * @param message Message of error to throw.
     */
  private throwError (message: string): never {
    throw new ParsingError(message, this.expr, this.index)
  }

  /**
     * Gets the longest key length of an object
     * @param o {object} Object to iterate over
     * @returns {number}
     */
  private static getMaxKeyLen (o: Record<string, any>): number {
    return Math.max(0, ...Object.keys(o).map(x => x.length))
  };

  /**
     * Gets the maximum length of the member of any members of an array.
     * @param ary Array to iterate over.
     * @returns
     */
  private static getMaxMemLen (ary: string[]): number {
    return Math.max(0, ...ary.map(x => x.length))
  };

  /**
     * Checks if a character is a decimal digit.
     * @param ch Code of character to check.
     * @returns
     */
  private static isDecimalDigit (ch: number): boolean {
    return (ch >= 48 && ch <= 57) // 0...9
  };

  /**
     * Checks if a character is the start of an identifier.
     * @param ch {number} Code of character to check.
     * @returns {boolean}
     */
  private static isIdentifierStart (ch: number): boolean {
    return (ch === 36) || (ch === 95) || // `$` and `_`
            (ch >= 65 && ch <= 90) || // A...Z
            (ch >= 97 && ch <= 122) || // a...z
            ch >= 128 // non-ascii
  };

  /**
     * Checks if a character is part of an identifier.
     * @param ch Code of character to check.
     * @returns
     */
  private static isIdentifierPart (ch: number): boolean {
    return (ch === 36) || (ch === 95) || // `$` and `_`
            (ch >= 65 && ch <= 90) || // A...Z
            (ch >= 97 && ch <= 122) || // a...z
            (ch >= 48 && ch <= 57) || // 0...9
            ch >= 128 // non-ascii
  };

  /**
     * Copies a dictionary for use in other functions.
     *
     * @template {string|number|symbol} K
     * @template V
     *
     * @param {Record<K, V>} record
     * @return {Record<K, V>}
     */
  private static copyDict<S extends string | number | symbol, T, U extends Record<S,T>>(dict: U): U {
    return { ...dict }
  }

  /**
     * Copies a list.
     *
     * @template T
     *
     * @param {Array<T>} ary
     * @return {Array<T>}
     */
  private static copyList<T>(ary: T[]): T[] {
    return ary.slice(0)
  }

  // ==================
  // CONFIG
  // ==================

  /**
     * Gets the configuration of this parser.
     * @return {PreJsPy.Config<L,U,B>}
     */
  GetConfig (): Config<L, U, B> {
    return {
      Operators: {
        Literals: PreJsPy.copyDict(this.config.Operators.Literals),
        Unary: PreJsPy.copyList(this.config.Operators.Unary),
        Binary: PreJsPy.copyDict(this.config.Operators.Binary)
      },
      Features: {
        Compound: this.config.Features.Compound,
        Tertiary: this.config.Features.Tertiary,
        Identifiers: this.config.Features.Identifiers,
        Calls: this.config.Features.Calls,
        Members: PreJsPy.copyDict(this.config.Features.Members),
        Literals: PreJsPy.copyDict(this.config.Features.Literals)
      }
    }
  }

  readonly config: Config<L, U, B>
  private max_unop_len = 0
  private max_binop_len = 0

  /**
     * Set the configuration of this parser.
     * @param {PreJsPy.PartialConfig<L,U,B>?} config
     * @return {PreJsPy.Config<L,U,B>}
     */
  SetConfig (config?: PartialConfig<L, U, B>): Config<L, U, B> {
    if (typeof config === 'object') {
      if (typeof config.Operators === 'object') {
        if (config.Operators.Literals != null) {
          this.config.Operators.Literals = PreJsPy.copyDict(config.Operators.Literals)
        }
        if (config.Operators.Unary != null) {
          this.config.Operators.Unary = PreJsPy.copyList(config.Operators.Unary)
          this.max_unop_len = PreJsPy.getMaxMemLen(this.config.Operators.Unary)
        }
        if (config.Operators.Binary != null) {
          this.config.Operators.Binary = PreJsPy.copyDict(config.Operators.Binary)
          this.max_binop_len = PreJsPy.getMaxKeyLen(this.config.Operators.Binary)
        }
      }
      if (typeof config.Features === 'object') {
        if (typeof config.Features.Compound === 'boolean') {
          this.config.Features.Compound = config.Features.Compound
        }
        if (typeof config.Features.Tertiary === 'boolean') {
          this.config.Features.Tertiary = config.Features.Tertiary
        }
        if (typeof config.Features.Identifiers === 'boolean') {
          this.config.Features.Identifiers = config.Features.Identifiers
        }
        if (typeof config.Features.Calls === 'boolean') {
          this.config.Features.Calls = config.Features.Calls
        }
        if (typeof config.Features.Members === 'object') {
          if (typeof config.Features.Members.Computed === 'boolean') {
            this.config.Features.Members.Computed = config.Features.Members.Computed
          }
          if (typeof config.Features.Members.Static === 'boolean') {
            this.config.Features.Members.Static = config.Features.Members.Static
          }
        }

        if (typeof config.Features.Literals === 'object') {
          if (typeof config.Features.Literals.Array === 'boolean') {
            this.config.Features.Literals.Array = config.Features.Literals.Array
          }
          if (typeof config.Features.Literals.Numeric === 'boolean') {
            this.config.Features.Literals.Numeric = config.Features.Literals.Numeric
          }
          if (typeof config.Features.Literals.NumericSeparator === 'string') {
            this.config.Features.Literals.NumericSeparator = config.Features.Literals.NumericSeparator
          }
          if (typeof config.Features.Literals.String === 'boolean') {
            this.config.Features.Literals.String = config.Features.Literals.String
          }
        }
      }
    }

    return this.GetConfig()
  }

  // =========
  // INIT CODE
  // =========
  constructor () {
    this.config = PreJsPy.GetDefaultConfig() as Config<L, U, B>
    this.SetConfig(this.config)
  }

  // ============
  // MISC HELPERS
  // ============

  /**
     * Returns the precedence of a binary operator or `0` if it isn't a binary operator.
     * @param operator Value of operator to lookup
     */
  private binaryPrecedence (operator: B): number {
    const binary = this.config.Operators.Binary
    return binary[operator] ?? 0
  };

  // =======
  // Parsing
  // =======

  private index: number = 0
  private length: number = 0
  private expr: string = ''

  /** returns the current character inside the input string */
  private char (): string {
    return this.expr.charAt(this.index)
  }

  /** returns the current character code inside the input string */
  private charCode (): number {
    return this.expr.charCodeAt(this.index)
  }

  /**
     * Parses a source string into a parse tree
     */
  Parse (expr: string): Expression<L, U, B> {
    // setup the state properly
    this.index = 0
    this.expr = expr
    this.length = expr.length

    try {
      return this.gobbleCompound()
    } finally {
      // revert state, to avoid any leaks of the expression that has been parsed
      this.index = 0
      this.expr = ''
      this.length = 0
    }
  }

  /**
   * Parses a source string into an expression, or returns an error
   */
  TryParse (expr: string): ParsingResult<Expression<L, U, B>> {
    try {
      const result = this.Parse(expr)
      return [result, null]
    } catch (e: any) {
      if (e instanceof ParsingError) {
        return [null, e]
      }
      throw e
    }
  }

  /**
     * Gobbles a single or compound expression from the input.
     */
  private gobbleCompound (): Expression<L, U, B> {
    // TODO: Disable compound expressions

    const nodes: Array<Expression<L, U, B>> = []

    while (this.index < this.length) {
      const cc = this.charCode()

      // Expressions can be separated by semicolons, commas, or just inferred without any
      // separators
      if (cc === SEMCOL_CODE || cc === COMMA_CODE) {
        this.index++ // ignore separators
        continue
      }

      // Try to gobble each expression individually
      const node = this.gobbleExpression()
      if (node !== null) {
        nodes.push(node)
        continue
      }

      if (this.index < this.length) {
        // If we weren't able to find a binary expression and are out of room, then
        // the expression passed in probably has too much
        this.throwError('Unexpected "' + this.char() + '"')
      }
    }

    // If there's only one expression just try returning the expression
    if (nodes.length === 1) {
      return nodes[0]
    }
    
    // do not allow compound expressions if they are not enabled
    if (!this.config.Features.Compound) {
      this.throwError('Unexpected compound expression')
    }

    return {
      type: COMPOUND,
      body: nodes
    }
  }

  /**
     * Advances the index to the next non-space character.
     */
  private gobbleSpaces (): void {
    while (true) {
      const ch = this.charCode()
      if (!(ch === 32 || ch === 9)) {
        break
      }
      this.index++
    }
  }

  /**
     * The main parsing function to pick an expression.
     *
     * This code first attempts to check if a tertiary expression is provided and, if not the case, delegates to a binary expression.
     * @returns
     */
  private gobbleExpression (): Expression<L, U, B> | null {
    // if we don't have the tertiary enabled, gobble a binary expression
    const test = this.gobbleBinaryExpression()
    if (!this.config.Features.Tertiary) {
      return test
    }

    this.gobbleSpaces()

    // didn't actually get a ternary expression
    if (test === null || this.charCode() !== QUMARK_CODE) {
      return test
    }

    // Ternary expression: test ? consequent : alternate

    this.index++

    const consequent = this.gobbleExpression()
    if (consequent === null) {
      this.throwError('Expected expression')
    }

    this.gobbleSpaces()
    if (this.charCode() !== COLON_CODE) {
      this.throwError('Expected :')
    }

    this.index++
    const alternate = this.gobbleExpression()
    if (alternate === null) {
      this.throwError('Expected expression')
    }

    return {
      type: CONDITIONAL_EXP,
      test,
      consequent,
      alternate
    }
  }

  /**
     * Search for the operation portion of the string (e.g. `+`, `===`)
     * Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
     * and move down from 3 to 2 to 1 character until a matching binary operation is found
     * then, return that binary operation.
     *
     * @returns {string|false}
     */
  private gobbleBinaryOp (): B | null {
    this.gobbleSpaces()

    let candidate = this.expr.substring(this.index, this.index + this.max_binop_len)
    let candidateLength = candidate.length
    while (candidateLength > 0) {
      if (Object.prototype.hasOwnProperty.call(this.config.Operators.Binary, candidate)) {
        this.index += candidateLength
        return candidate as B
      }
      candidateLength--
      candidate = candidate.substring(0, candidateLength)
    }
    return null
  }

  // This function is responsible for gobbling an individual expression,
  // e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
  private gobbleBinaryExpression (): Expression<L, U, B> | null {
    // First, try to get the leftmost thing
    // Then, check to see if there's a binary operator operating on that leftmost thing
    const left = this.gobbleToken()
    const biop = this.gobbleBinaryOp()

    // If there wasn't a binary operator, just return the leftmost node
    if (biop === null || left === null) {
      return left
    }

    const right = this.gobbleToken()
    if (right === null) {
      this.throwError('Expected expression after ' + biop)
    }

    // Create a stack of expressions and information about the operators between them
    const exprs = [left, right]
    const ops = [
      { value: biop, prec: this.binaryPrecedence(biop) }
    ]

    // Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
    while (true) {
      const biop = this.gobbleBinaryOp()
      if (biop === null) {
        break
      }

      const prec = this.binaryPrecedence(biop)
      if (prec === 0) {
        break
      }

      while ((ops.length > 0) && (prec < ops[ops.length - 1].prec)) {
        const right = exprs.pop()
        const left = exprs.pop()
        const op = ops.pop()

        if (typeof right === 'undefined' || typeof left === 'undefined' || typeof op === 'undefined') {
          // the code guarantees that there are always enough expressions.
          // so this case should never occur.
          this.throwError('Logic Error: Expression and operator length inconsistent')
        }

        exprs.push({
          type: BINARY_EXP,
          operator: op.value,
          left,
          right
        }
        )
      }

      const node = this.gobbleToken()
      if (node === null) {
        this.throwError('Expected expression after ' + biop)
      }
      exprs.push(node)

      ops.push({ value: biop, prec })
    }

    let i = exprs.length - 1
    let j = ops.length - 1

    let node = exprs[i]
    while ((i > 0) && (j >= 0)) {
      node = {
        type: BINARY_EXP,
        operator: ops[j].value,
        left: exprs[i - 1],
        right: node
      }
      j--
      i--
    }
    return node
  }

  // An individual part of a binary expression:
  // e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
  private gobbleToken (): Expression<L, U, B> | null {
    this.gobbleSpaces()
    const ch = this.charCode()

    if (PreJsPy.isDecimalDigit(ch) || ch === PERIOD_CODE) {
      // Char code 46 is a dot `.` which can start off a numeric literal
      return this.gobbleNumericLiteral()
    } else if (ch === SQUOTE_CODE || ch === DQUOTE_CODE) {
      // Single or double quotes
      return this.gobbleStringLiteral()
    } else if (ch === OBRACK_CODE) {
      return this.gobbleArray()
    }

    let candidate = this.expr.substring(this.index, this.index + this.max_unop_len)
    let candidateLength = candidate.length
    while (candidateLength > 0) {
      if (this.config.Operators.Unary.includes(candidate as U)) {
        this.index += candidateLength

        const argument = this.gobbleToken()
        if (argument === null) {
          this.throwError('Expected Expression')
        }

        return {
          type: UNARY_EXP,
          operator: candidate as U,
          argument
        }
      }

      candidateLength--
      candidate = candidate.substring(0, candidateLength)
    }

    if (PreJsPy.isIdentifierStart(ch) || ch === OPAREN_CODE) { // open parenthesis
      // `foo`, `bar.baz`
      return this.gobbleVariable()
    }

    return null
  }

  /**
   * Gobbles a contiguous sequence of decimal numbers, possibly separated with numeric separators.
   * The returned string does not include numeric separators.
   */
  private gobbleDecimal(): string {
    // Fast path: No separator enabled case: no numeric separator
    const separator = this.config.Features.Literals.NumericSeparator
    if (separator === "") {
      const start = this.index
      while(PreJsPy.isDecimalDigit(this.charCode())) {
        this.index++
      }
      return this.expr.substring(start, this.index)
    }

    // slow path: need to check for separator
    let number = ""

    while(true) {
      if (PreJsPy.isDecimalDigit(this.charCode())) {
        number += this.char()
      } else if(this.char() !== separator) {
        break;
      }

      this.index++
    }

    return number
  }
  /**
     * Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
     * keep track of everything in the numeric literal and then calling `parseFloat` on that string
     */
  private gobbleNumericLiteral (): NumericLiteral {
    const start = this.index

    // gobble the number itself
    let number = this.gobbleDecimal()

    if (this.charCode() === PERIOD_CODE) { // can start with a decimal marker
      number += '.'
      this.index++

      number += this.gobbleDecimal()
    }

    const ch = this.char()
    if (ch === 'e' || ch === 'E') { // exponent marker
      number += ch
      this.index++

      {
        const ch = this.char()
        if (ch === '+' || ch === '-') { // exponent sign
          number += ch
          this.index++
        }
      }

      const exponent = this.gobbleDecimal()
      if (exponent == "") {
        this.throwError('Expected exponent (' + number + this.char() + ')')
      }

      number += exponent
    }

    // validate that the number ends properly
    const chCode = this.charCode()

    // can't be a part of an identifier
    if (PreJsPy.isIdentifierStart(chCode)) {
      this.throwError('Variable names cannot start with a number (' + number + this.char() + ')')
    }

    // can't contain another period.
    if (chCode === PERIOD_CODE) {
      this.throwError('Unexpected period')
    }

    if (!this.config.Features.Literals.Numeric) {
      this.index -= number.length
      this.throwError('Unexpected numeric literal')
    }

    // Parse the float value and get the literal (if needed)
    const value = parseFloat(number)
    if (this.config.Features.Literals.NumericSeparator != '') {
      number = this.expr.substring(start, this.index)
    }

    return {
      type: LITERAL,
      kind: 'number',
      value: value,
      raw: number
    }
  }

  /**
     * Parses a string literal, staring with single or double quotes with basic support for escape codes
     * e.g. `"hello world"`, `'this is\na linebreak'`
     */
  private gobbleStringLiteral (): StringLiteral {
    let str = ''
    const quote = this.char()
    let closed = false

    const start = this.index
    this.index++

    while (this.index < this.length) {
      {
        const ch = this.char()
        this.index++

        if (ch === quote) {
          closed = true
          break
        }

        if (ch !== '\\') {
          str += ch
          continue
        }
      }

      // Check for all of the common escape codes
      const ch = this.char()
      this.index++

      switch (ch) {
        case 'n':
          str += '\n'
          break
        case 'r':
          str += '\r'
          break
        case 't':
          str += '\t'
          break
        case 'b':
          str += '\b'
          break
        case 'f':
          str += '\f'
          break
        case 'v':
          str += '\x0B'
          break
        case '\\':
          str += '\\'
          break

          // default: just add the character literally.
        default:
          str += ch
      }
    }

    if (!closed) {
      this.throwError('Unclosed quote after "' + str + '"')
    }

    if (!this.config.Features.Literals.String) {
      this.index = start
      this.throwError('Unexpected string literal')
    }

    return {
      type: LITERAL,
      kind: 'string',
      value: str,
      raw: quote + str + quote // TODO: Does this need fixing
    }
  }

  /**
     * Gobbles only identifiers
     * e.g.: `foo`, `_value`, `$x1`
     *
     * Also, this function checks if that identifier is a literal:
     * (e.g. `true`, `false`, `null`) or `this`
     */
  private gobbleIdentifier (): Literal<L> | Identifier {
    const start = this.index

    if (!PreJsPy.isIdentifierStart(this.charCode())) {
      this.throwError('Unexpected ' + this.char())
    }
    this.index++

    while (this.index < this.length) {
      if (!PreJsPy.isIdentifierPart(this.charCode())) {
        break
      }
      this.index++
    }

    const identifier = this.expr.substring(start, this.index)

    if (Object.prototype.hasOwnProperty.call(this.config.Operators.Literals, identifier)) {
      return {
        type: LITERAL,
        value: this.config.Operators.Literals[identifier],
        raw: identifier
      }
    }

    if (!this.config.Features.Identifiers) {
      this.throwError('Unknown literal "' + identifier + '"')
    }
    return {
      type: IDENTIFIER,
      name: identifier
    }
  }

  /**
     * Gobbles a list of arguments within the context of a function call
     * or array literal. This function also assumes that the opening character
     * `(` or `[` has already been gobbled, and gobbles expressions and commas
     * until the terminator character `)` or `]` is encountered.
     *
     * e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
     */
  private gobbleArguments (termination: number): Array<Expression<L, U, B>> {
    const args: Array<Expression<L, U, B>> = []
    while (this.index < this.length) {
      this.gobbleSpaces()
      const cc = this.charCode()
      if (cc === termination) { // done parsing
        this.index++
        break
      }

      if (cc === COMMA_CODE) { // between expressions
        this.index++
        continue
      }

      const node = this.gobbleExpression()
      if (node === null || node.type === COMPOUND) {
        this.throwError('Expected comma')
      }
      args.push(node)
    }
    return args
  }

  /**
     * Gobble a non-literal variable name. This variable name may include properties
     * e.g. `foo`, `bar.baz`, `foo['bar'].baz`
     *
     * It also gobbles function calls:
     * Math.acos(obj.angle)
     */
  private gobbleVariable (): Expression<L, U, B> | null {
    // parse a group or identifier first
    let node: Expression<L, U, B> | null = (this.charCode() === OPAREN_CODE) ? this.gobbleGroup() : this.gobbleIdentifier()
    if (node === null) {
      return null
    }
    this.gobbleSpaces()

    // then iterate accessor calls
    let cc = this.charCode()
    while (cc === PERIOD_CODE || cc === OBRACK_CODE || cc === OPAREN_CODE) {
      this.index++
      if (cc === PERIOD_CODE) {
        if (!this.config.Features.Members.Static) {
          this.throwError('Unexpected static MemberExpression')
        }
        this.gobbleSpaces()
        node = {
          type: MEMBER_EXP,
          computed: false,
          object: node,
          property: this.gobbleIdentifier()
        }
      } else if (cc === OBRACK_CODE) {
        if (!this.config.Features.Members.Computed) {
          this.throwError('Unexpected computed MemberExpression')
        }
        const property = this.gobbleExpression()
        if (property === null) {
          this.throwError('Expected Expression')
        }

        node = {
          type: MEMBER_EXP,
          computed: true,
          object: node,
          property
        }

        this.gobbleSpaces()
        cc = this.charCode()
        if (cc !== CBRACK_CODE) {
          this.throwError('Unclosed [')
        }
        this.index++
      } else if (cc === OPAREN_CODE) {
        if (!this.config.Features.Calls) {
          this.throwError('Unexpected function call')
        }

        // A function call is being made; gobble all the arguments
        node = {
          type: CALL_EXP,
          arguments: this.gobbleArguments(CPAREN_CODE),
          callee: node
        }
      }

      this.gobbleSpaces()
      cc = this.charCode()
    }
    return node
  }

  /**
     * Responsible for parsing a group of things within parentheses `()`
     * This function assumes that it needs to gobble the opening parenthesis
     * and then tries to gobble everything within that parenthesis, assuming
     * that the next thing it should see is the close parenthesis. If not,
     * then the expression probably doesn't have a `)`
     */
  private gobbleGroup (): Expression<L, U, B> | null {
    this.index++

    const node = this.gobbleExpression()
    this.gobbleSpaces()

    if (this.charCode() !== CPAREN_CODE) {
      this.throwError('Unclosed (')
    }

    this.index++
    return node
  }

  /**
     * Responsible for parsing Array literals `[1, 2, 3]`.
     * This function assumes that it needs to gobble the opening bracket
     * and then tries to gobble the expressions as arguments.
     */
  private gobbleArray (): Ary<L, U, B> {
    if (!this.config.Features.Literals.Array) {
      this.throwError('Unexpected array literal')
    }

    this.index++

    return {
      type: ARRAY_EXP,
      elements: this.gobbleArguments(CBRACK_CODE)
    }
  }

  /**
     * Creates and returns a new default configuration.
     */
  static GetDefaultConfig (): Config<any, string, string> {
    return {
      Operators: {
        Literals: {
          true: true,
          false: false,
          null: null
        },
        Unary: ['-', '!', '~', '+'],
        Binary: {
          '||': 1,
          '&&': 2,
          '|': 3,
          '^': 4,
          '&': 5,
          '==': 6,
          '!=': 6,
          '===': 6,
          '!==': 6,
          '<': 7,
          '>': 7,
          '<=': 7,
          '>=': 7,
          '<<': 8,
          '>>': 8,
          '>>>': 8,
          '+': 9,
          '-': 9,
          '*': 10,
          '/': 10,
          '%': 10
        }
      },

      Features: {
        Compound: true,
        Tertiary: true,
        Identifiers: true,
        Calls: true,
        Members: {
          Static: true,
          Computed: true
        },
        Literals: {
          Numeric: true,
          NumericSeparator: "",
          String: true,
          Array: true
        }
      }
    }
  };
}
