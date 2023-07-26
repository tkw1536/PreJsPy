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
 */
export type Expression =
  Identifier |
  Literal |
  StringLiteral |
  NumericLiteral |
  Compound |
  Member |
  Call |
  Unary |
  Binary |
  Condition |
  Ary

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

    Object.setPrototypeOf(this, ParsingError.prototype)
  }
}

interface Compound {
  type: ExpressionType.COMPOUND
  body: Expression[]
}

interface Identifier {
  type: ExpressionType.IDENTIFIER
  name: string
}

interface Member {
  type: ExpressionType.MEMBER_EXP
  computed: boolean
  object: Expression
  property: Expression
}

interface Literal {
  type: ExpressionType.LITERAL
  value: any
  raw: string
}

interface StringLiteral {
  type: ExpressionType.LITERAL
  kind: 'string'
  value: string
  raw: string
}

interface NumericLiteral {
  type: ExpressionType.LITERAL
  kind: 'number'
  value: number
  raw: string
}

interface Call {
  type: ExpressionType.CALL_EXP
  arguments: Expression[]
  callee: Expression
}

interface Unary {
  type: ExpressionType.UNARY_EXP
  operator: string
  argument: Expression
}

interface Binary {
  type: ExpressionType.BINARY_EXP
  operator: string
  left: Expression
  right: Expression
}

interface Condition {
  type: ExpressionType.CONDITIONAL_EXP
  test: Expression
  consequent: Expression
  alternate: Expression
}

interface Ary {
  type: ExpressionType.ARRAY_EXP
  elements: Expression[]
}

/**
 * Configuration for PreJsPy.
 */
export interface Config {
  Operators: {
    Literals: Record<string, any>
    Unary: string[]
    Binary: Record<string, number>
  }

  Features: {
    Compound: boolean
    Conditional: boolean
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

export type PartialConfig = Partial<{
  Operators: Partial<Config['Operators']>
  Features: Partial<{
    Compound: boolean
    Conditional: boolean
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

/** Represents the type of expressions */
export enum ExpressionType {
  COMPOUND = 'Compound',
  IDENTIFIER = 'Identifier',
  MEMBER_EXP = 'MemberExpression',
  LITERAL = 'Literal',
  CALL_EXP = 'CallExpression',
  UNARY_EXP = 'UnaryExpression',
  BINARY_EXP = 'BinaryExpression',
  CONDITIONAL_EXP = 'ConditionalExpression',
  ARRAY_EXP = 'ArrayExpression',
}

/** ParsingResult represents a result from parsing */
type ParsingResult<T> = [T, null] | [null, ParsingError]

export class PreJsPy {
  // LIST OF SPECIAL CHARACTER
  private static readonly CHAR_PERIOD = '.'
  private static readonly CHAR_COMMA = ','
  private static readonly CHAR_SINGLE_QUOTE = '\''
  private static readonly CHAR_DOUBLE_QUOTE = '"'
  private static readonly CHAR_OPEN_PARENTHESES = '('
  private static readonly CHAR_CLOSE_PARENTHESES = ')'
  private static readonly CHAR_OPEN_BRACKET = '['
  private static readonly CHAR_CLOSE_BRACKET = ']'
  private static readonly CHAR_QUESTIONMARK = '?'
  private static readonly CHAR_SEMICOLON = ';'
  private static readonly CHAR_COLON = ':'
  private static readonly CHAR_SPACE = ' '
  private static readonly CHAR_TAB = '\t'

  /**
   * Makes a parsing error with the given message and current index.
   * @param message Message of error to throw.
   */
  private error (message: string): ParsingError {
    return new ParsingError(message, this.expr, this.index)
  }

  /**
     * Checks if a character is a decimal digit.
     * @param ch Character to check
     * @returns
     */
  private static isDecimalDigit (ch: string): boolean {
    return ch.length === 1 && (ch >= '0' && ch <= '9')
  };

  /**
     * Checks if a character is the start of an identifier.
     * @param ch Character to check
     * @returns
     */
  private static isIdentifierStart (ch: string): boolean {
    return ch.length === 1 && (
      (ch === '$') ||
      (ch === '_') ||
      (ch >= 'A' && ch <= 'Z') ||
      (ch >= 'a' && ch <= 'z') ||
      ch.charCodeAt(0) >= 128 // non-ascii
    )
  };

  /**
     * Checks if a character is part of an identifier.
     * @param ch Code of character to check.
     * @returns
     */
  private static isIdentifierPart (ch: string): boolean {
    return ch.length === 1 && (
      (ch === '$') ||
      (ch === '_') ||
      (ch >= 'A' && ch <= 'Z') ||
      (ch >= 'a' && ch <= 'z') ||
      (ch >= '0' && ch <= '9') ||
      ch.charCodeAt(0) >= 128 // non-ascii
    )
  };

  // #region "Config"

  readonly config: Config
  private unaryOperatorLength = 0
  private binaryOperatorLength = 0

  /**
   * Creates a new PreJsPy Object.
   */
  constructor () {
    this.config = PreJsPy.GetDefaultConfig()
    this.SetConfig(this.config)
  }

  /**
     * Set the configuration of this parser.
     */
  SetConfig (config?: PartialConfig): Config {
    if (typeof config === 'object') {
      PreJsPy.assign(this.config, config, 'Operators', 'Literals')
      PreJsPy.assign(this.config, config, 'Operators', 'Unary')
      PreJsPy.assign(this.config, config, 'Operators', 'Binary')

      PreJsPy.assign(this.config, config, 'Features', 'Compound')
      PreJsPy.assign(this.config, config, 'Features', 'Conditional')
      PreJsPy.assign(this.config, config, 'Features', 'Identifiers')
      PreJsPy.assign(this.config, config, 'Features', 'Calls')

      PreJsPy.assign(this.config, config, 'Features', 'Members', 'Computed')
      PreJsPy.assign(this.config, config, 'Features', 'Members', 'Static')

      PreJsPy.assign(this.config, config, 'Features', 'Literals', 'Array')
      PreJsPy.assign(this.config, config, 'Features', 'Literals', 'Numeric')
      PreJsPy.assign(this.config, config, 'Features', 'Literals', 'NumericSeparator')
      PreJsPy.assign(this.config, config, 'Features', 'Literals', 'String')

      this.unaryOperatorLength = PreJsPy.maxArrayValueLen(this.config.Operators.Unary)
      this.binaryOperatorLength = PreJsPy.maxObjectKeyLen(this.config.Operators.Binary)
    }

    return this.GetConfig()
  }

  /**
   * Gets the configuration of this parser.
   * @return {PreJsPy.Config<L,U,B>}
   */
  GetConfig (): Config {
    return PreJsPy.clone(this.config)
  }

  // the prototype of the {} object (used for cloneing)
  private static readonly plainObjectPrototype = Object.getPrototypeOf({})

  /**
   * Clone makes a deep clone of an object.
   *
   * @param obj
   * @returns
   */
  private static clone<T>(obj: T): T {
    // use structuredClone when available
    if (typeof structuredClone === 'function') {
      return structuredClone(obj)
    }

    // simple polyfill

    // an array
    if (Array.isArray(obj)) {
      return obj.map(obj => this.clone(obj)) as T
    }

    // an associative object
    if (obj !== null && typeof obj === 'object' && Object.getPrototypeOf(obj) === this.plainObjectPrototype) {
      return Object.fromEntries(Object.entries(obj).map(([k, v]) => [k, this.clone(v)])) as T
    }

    // return object as-is
    return obj
  }

  /**
   * Assigns a specific nested property from source to dest.
   * The value is cloned.
   *
   * This is roughly equivalent to
   *
   * dest[path[0]]...[path[n]] = this.clone(source[path[0]]...[path[n]])
   *
   * with appropriate existence checks.
   *
   * @param dest the destination element to assign into
   * @param source the source object to assign from
   * @param path the names of properties to navigate through
   */
  private static assign (dest: any, source: any, ...path: string[]): void {
    // skip if we have no arguments
    if (path.length === 0) {
      return
    }

    // find the source as dest properties
    let destProp = dest
    let sourceProp = source

    // iterate through to the penultimate elements
    for (const element of path.slice(0, path.length - 1)) {
      if (!Object.prototype.hasOwnProperty.call(destProp, element)) {
        return
      }
      if (!Object.prototype.hasOwnProperty.call(sourceProp, element)) {
        return
      }

      destProp = destProp[element]
      sourceProp = sourceProp[element]
    }

    // check the last element
    const element = path[path.length - 1]
    if (!Object.prototype.hasOwnProperty.call(destProp, element)) {
      return
    }
    if (!Object.prototype.hasOwnProperty.call(sourceProp, element)) {
      return
    }

    // and assign the clone
    destProp[element] = this.clone(sourceProp[element])
  }

  /**
     * Gets the longest key length of an object
     * @param o {object} Object to iterate over
     * @returns {number}
     */
  private static maxObjectKeyLen (o: Record<string, any>): number {
    return Math.max(0, ...Object.keys(o).map(x => x.length))
  };

  /**
     * Gets the maximum length of the member of an array.
     * @param ary Array to iterate over.
     * @returns
     */
  private static maxArrayValueLen (ary: string[]): number {
    return Math.max(0, ...ary.map(x => x.length))
  };

  // #endregion

  // #region "State"

  private index: number = 0
  private length: number = 0
  private expr: string = ''

  /**
   * Resets internal state to be able to parse expression
   */
  private reset (expr: string): void {
    this.expr = expr
    this.length = expr.length
    this.index = 0
  }

  /**
   * @returns the current character or "" if the end of the string was reached
   */
  private char (): string {
    return this.expr.charAt(this.index)
  }

  /**
   * Returns count characters of the input string, starting at the current character.
   */
  private chars (count: number): string {
    return this.expr.substring(this.index, this.index + count)
  }

  /**
   * Returns the string of characters starting at start up to (but not including) the current character.
   *
   * @param start
   */
  private charsFrom (start: number): string {
    return this.expr.substring(start, this.index)
  }

  // #endregion

  /**
     * Parses a source string into a parse tree
     */
  Parse (expr: string): Expression {
    const result = this.gobble(expr)
    if (result instanceof ParsingError) {
      throw result
    }
    return result
  }

  /**
   * Parses a source string into an expression, or returns an error
   */
  TryParse (expr: string): ParsingResult<Expression> {
    const result = this.gobble(expr)
    if (result instanceof ParsingError) {
      return [null, result]
    }
    return [result, null]
  }

  /**
   * Gobbles the given source string
   * @param expr
   * @returns
   */
  private gobble (expr: string): Expression | ParsingError {
    this.reset(expr) // setup the state properly
    const result = this.gobbleCompound()
    this.reset('') // don't keep the last parsed expression in memory

    return result
  }

  /**
     * Gobbles a single or compound expression from the input.
     */
  private gobbleCompound (): Expression | ParsingError {
    const nodes: Expression[] = []

    while (this.index < this.length) {
      const ch = this.char()

      // Expressions can be separated by semicolons, commas, or just inferred without any separators
      if (ch === PreJsPy.CHAR_SEMICOLON || ch === PreJsPy.CHAR_COMMA) {
        this.index++ // ignore separators
        continue
      }

      // Try to gobble each expression individually
      const node = this.gobbleExpression()
      if (node instanceof ParsingError) {
        return node
      }
      if (node === null) {
        break
      }

      nodes.push(node)
    }

    if (this.index < this.length) {
      // If we weren't able to find a binary expression and are out of room, then
      // the expression passed in probably has too much
      const ch = this.char()
      return this.error('Unexpected ' + JSON.stringify(ch))
    }

    // If there's only one expression just try returning the expression
    if (nodes.length === 1) {
      return nodes[0]
    }

    // do not allow compound expressions if they are not enabled
    if (!this.config.Features.Compound) {
      return this.error('Unexpected compound expression')
    }

    return {
      type: ExpressionType.COMPOUND,
      body: nodes
    }
  }

  /**
   * Advances the index to the next non-space character
   * @returns the next non-space character
   */
  private skipSpaces (): string {
    while (true) {
      const ch = this.char()
      if (!(ch === PreJsPy.CHAR_SPACE || ch === PreJsPy.CHAR_TAB)) {
        return ch
      }
      this.index++
    }
  }

  /**
     * The main parsing function to pick an expression.
     *
     * This code first attempts to check if a conditional expression is provided and, if not the case, delegates to a binary expression.
     * @returns
     */
  private gobbleExpression (): Expression | ParsingError | null {
    // gobble the binary expression
    const test = this.gobbleBinaryExpression()

    // only continue if there is a chance of finding a conditional
    if (!this.config.Features.Conditional || test === null || test instanceof ParsingError) {
      return test
    }

    // didn't actually get a conditional expression
    {
      const ch = this.skipSpaces()
      if (ch !== PreJsPy.CHAR_QUESTIONMARK) {
        return test
      }
    }

    // Conditional expression: test ? consequent : alternate
    this.index++

    const consequent = this.gobbleExpression()
    if (consequent instanceof ParsingError) {
      return consequent
    }
    if (consequent === null) {
      return this.error('Expected expression')
    }

    {
      const ch = this.skipSpaces()
      if (ch !== PreJsPy.CHAR_COLON) {
        return this.error('Expected ' + JSON.stringify(PreJsPy.CHAR_COLON))
      }
    }

    this.index++
    const alternate = this.gobbleExpression()
    if (alternate instanceof ParsingError) {
      return alternate
    }
    if (alternate === null) {
      return this.error('Expected expression')
    }

    return {
      type: ExpressionType.CONDITIONAL_EXP,
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
  private gobbleBinaryOp (): string | null {
    this.skipSpaces()

    for (let candidateLength = this.binaryOperatorLength; candidateLength > 0; candidateLength--) {
      const candidate = this.chars(candidateLength)
      if (Object.prototype.hasOwnProperty.call(this.config.Operators.Binary, candidate)) {
        this.index += candidateLength
        return candidate
      }
    }
    return null
  }

  // This function is responsible for gobbling an individual expression,
  // e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
  private gobbleBinaryExpression (): Expression | ParsingError | null {
    // get the leftmost token of a binary expression or bail out
    const left = this.gobbleToken()
    if (left instanceof ParsingError) {
      return left
    }
    if (left === null) {
      return null
    }

    const exprs = [left] // a list of expressions
    const ops = [] // and a list of binary operators between them

    // Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
    while (true) {
      const value = this.gobbleBinaryOp()
      if (value === null) {
        break
      }

      const precedence = this.config.Operators.Binary[value]

      while ((ops.length > 0) && (precedence < ops[ops.length - 1].precedence)) {
        // the code maintains invariance ops.length === exprs.length + 1
        // so the .pop()s are safe because ops.length >= 1 and exprs.length >= 2

        const right = exprs.pop()! // eslint-disable-line @typescript-eslint/no-non-null-assertion
        const left = exprs.pop()! // eslint-disable-line @typescript-eslint/no-non-null-assertion
        const op = ops.pop()! // eslint-disable-line @typescript-eslint/no-non-null-assertion

        exprs.push({
          type: ExpressionType.BINARY_EXP,
          operator: op.value,
          left,
          right
        })
      }

      const node = this.gobbleToken()
      if (node instanceof ParsingError) {
        return node
      }
      if (node === null) {
        return this.error('Expected expression after ' + JSON.stringify(value))
      }
      exprs.push(node)

      ops.push({ value, precedence })
    }

    let i = exprs.length - 1
    let j = ops.length - 1

    let node = exprs[i]
    while ((i > 0) && (j >= 0)) {
      node = {
        type: ExpressionType.BINARY_EXP,
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
  private gobbleToken (): Expression | ParsingError | null {
    const ch = this.skipSpaces()

    // numeric literals
    if (this.config.Features.Literals.Numeric && (PreJsPy.isDecimalDigit(ch) || ch === PreJsPy.CHAR_PERIOD)) {
      return this.gobbleNumericLiteral()
    }

    // single or double quoted strings
    if (this.config.Features.Literals.String && (ch === PreJsPy.CHAR_SINGLE_QUOTE || ch === PreJsPy.CHAR_DOUBLE_QUOTE)) {
      return this.gobbleStringLiteral()
    }

    // array literal
    if (this.config.Features.Literals.Array && ch === PreJsPy.CHAR_OPEN_BRACKET) {
      return this.gobbleArray()
    }

    let candidateLength = this.unaryOperatorLength
    while (candidateLength > 0) {
      const candidate = this.chars(candidateLength)

      if (this.config.Operators.Unary.includes(candidate)) {
        this.index += candidateLength

        const argument = this.gobbleToken()
        if (argument instanceof ParsingError) {
          return argument
        }
        if (argument === null) {
          return this.error('Expected argument for unary expression')
        }

        return {
          type: ExpressionType.UNARY_EXP,
          operator: candidate,
          argument
        }
      }

      candidateLength--
    }

    if (PreJsPy.isIdentifierStart(ch) || ch === PreJsPy.CHAR_OPEN_PARENTHESES) {
      return this.gobbleVariable(ch)
    }

    return null
  }

  /**
   * Gobbles a contiguous sequence of decimal numbers, possibly separated with numeric separators.
   * The returned string does not include numeric separators.
   */
  private gobbleDecimal (): string {
    // Fast path: No separator enabled case: no numeric separator
    const separator = this.config.Features.Literals.NumericSeparator
    if (separator === '') {
      const start = this.index
      while (PreJsPy.isDecimalDigit(this.char())) {
        this.index++
      }
      return this.charsFrom(start)
    }

    // slow path: need to check for separator
    let number = ''

    while (true) {
      const ch = this.char()
      if (PreJsPy.isDecimalDigit(ch)) {
        number += ch
      } else if (ch !== separator) {
        break
      }

      this.index++
    }

    return number
  }

  /**
     * Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
     * keep track of everything in the numeric literal and then calling `parseFloat` on that string
     */
  private gobbleNumericLiteral (): NumericLiteral | ParsingError {
    const start = this.index

    // gobble the number itself
    let number = this.gobbleDecimal()

    // can start with a decimal marker
    {
      const ch = this.char()
      if (ch === PreJsPy.CHAR_PERIOD) {
        number += '.'
        this.index++

        number += this.gobbleDecimal()
      }
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
      if (exponent === '') {
        const ch = this.char()
        return this.error('Expected exponent after ' + JSON.stringify(number + ch))
      }

      number += exponent
    }

    // validate that the number ends properly
    // (can't be a part of an identifier)
    {
      const ch = this.char()
      if (PreJsPy.isIdentifierStart(ch)) {
        return this.error('Variable names cannot start with a number like ' + JSON.stringify(number + ch))
      }
    }

    // Parse the float value and get the literal (if needed)
    const value = parseFloat(number)
    if (this.config.Features.Literals.NumericSeparator !== '') {
      number = this.charsFrom(start)
    }

    return {
      type: ExpressionType.LITERAL,
      kind: 'number',
      value,
      raw: number
    }
  }

  /**
     * Parses a string literal, staring with single or double quotes with basic support for escape codes
     * e.g. `"hello world"`, `'this is\na linebreak'`
     */
  private gobbleStringLiteral (): StringLiteral | ParsingError {
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
      return this.error('Unclosed quote after ' + JSON.stringify(str))
    }

    return {
      type: ExpressionType.LITERAL,
      kind: 'string',
      value: str,
      raw: this.charsFrom(start)
    }
  }

  /**
     * Gobbles only identifiers
     * e.g.: `foo`, `_value`, `$x1`
     *
     * Also, this function checks if that identifier is a literal:
     * (e.g. `true`, `false`, `null`) or `this`
     */
  private gobbleIdentifier (ch: string): Literal | Identifier | ParsingError {
    const start = this.index

    if (ch === '') {
      return this.error('Expected literal')
    }
    if (!PreJsPy.isIdentifierStart(ch)) {
      return this.error('Unexpected ' + JSON.stringify(ch))
    }
    this.index++

    while (this.index < this.length) {
      if (!PreJsPy.isIdentifierPart(this.char())) {
        break
      }
      this.index++
    }

    const identifier = this.charsFrom(start)

    if (Object.prototype.hasOwnProperty.call(this.config.Operators.Literals, identifier)) {
      return {
        type: ExpressionType.LITERAL,
        value: this.config.Operators.Literals[identifier],
        raw: identifier
      }
    }

    if (!this.config.Features.Identifiers) {
      return this.error('Unknown literal ' + JSON.stringify(identifier))
    }

    return {
      type: ExpressionType.IDENTIFIER,
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
  private gobbleArguments (start: string, end: string): Expression[] | ParsingError {
    const args: Expression[] = []

    let closed = false // is the expression closed?
    let hadComma = false // did we have a comma in the last iteration?

    while (this.index < this.length) {
      const ch = this.skipSpaces()
      if (ch === end) { // done parsing
        closed = true
        this.index++
        break
      }

      if (ch === PreJsPy.CHAR_COMMA) { // between expressions
        if (hadComma) {
          return this.error('Duplicate ' + JSON.stringify(PreJsPy.CHAR_COMMA))
        }
        hadComma = true
        this.index++
        continue
      }

      // check that there was a comma (if we expected one)
      const wantsComma = args.length > 0
      if (wantsComma !== hadComma) {
        if (wantsComma) {
          return this.error('Expected ' + JSON.stringify(PreJsPy.CHAR_COMMA))
        } else {
          return this.error('Unexpected ' + JSON.stringify(PreJsPy.CHAR_COMMA))
        }
      }

      const node = this.gobbleExpression()
      if (node instanceof ParsingError) {
        return node
      }
      if (node === null || node.type === ExpressionType.COMPOUND) {
        return this.error('Expected ' + JSON.stringify(PreJsPy.CHAR_COMMA))
      }

      args.push(node)
      hadComma = false
    }
    if (!closed) {
      return this.error('Unclosed ' + JSON.stringify(start))
    }
    return args
  }

  /**
     * Gobble a non-literal variable name. This variable name may include properties
     * e.g. `foo`, `bar.baz`, `foo['bar'].baz`
     *
     * ch is the first character
     *
     *
     * It also gobbles function calls:
     * Math.acos(obj.angle)
     */
  private gobbleVariable (ch: string): Expression | ParsingError | null {
    // parse a group or identifier first
    let node: Expression
    if (ch === PreJsPy.CHAR_OPEN_PARENTHESES) {
      const group = this.gobbleGroup()
      if (group === null || group instanceof ParsingError) {
        return group
      }
      node = group
    } else {
      const identifier = this.gobbleIdentifier(ch)
      if (identifier instanceof ParsingError) {
        return identifier
      }
      node = identifier
    }

    // then iterate over operations applied to it
    while (true) {
      const ch = this.skipSpaces()

      this.index++

      // access via .
      if (this.config.Features.Members.Static && ch === PreJsPy.CHAR_PERIOD) {
        const ch = this.skipSpaces()

        const property = this.gobbleIdentifier(ch)
        if (property instanceof ParsingError) {
          return property
        }

        node = {
          type: ExpressionType.MEMBER_EXP,
          computed: false,
          object: node,
          property
        }
        continue
      }

      // access via []s
      if (this.config.Features.Members.Computed && ch === PreJsPy.CHAR_OPEN_BRACKET) {
        const property = this.gobbleExpression()
        if (property === null) {
          return this.error('Expected Expression')
        }
        if (property instanceof ParsingError) {
          return property
        }

        node = {
          type: ExpressionType.MEMBER_EXP,
          computed: true,
          object: node,
          property
        }

        const ch = this.skipSpaces()
        if (ch !== PreJsPy.CHAR_CLOSE_BRACKET) {
          return this.error('Unclosed ' + JSON.stringify(PreJsPy.CHAR_OPEN_BRACKET))
        }
        this.index++
        continue
      }

      // call with ()s
      if (this.config.Features.Calls && ch === PreJsPy.CHAR_OPEN_PARENTHESES) {
        const args = this.gobbleArguments(PreJsPy.CHAR_OPEN_PARENTHESES, PreJsPy.CHAR_CLOSE_PARENTHESES)
        if (args instanceof ParsingError) {
          return args
        }
        node = {
          type: ExpressionType.CALL_EXP,
          arguments: args,
          callee: node
        }
        continue
      }

      // done
      this.index -= 1
      break
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
  private gobbleGroup (): Expression | ParsingError | null {
    this.index++

    const node = this.gobbleExpression()
    if (node instanceof ParsingError) {
      return node
    }

    const ch = this.skipSpaces()
    if (ch !== PreJsPy.CHAR_CLOSE_PARENTHESES) {
      return this.error('Unclosed ' + JSON.stringify(PreJsPy.CHAR_OPEN_PARENTHESES))
    }

    this.index++
    return node
  }

  /**
     * Responsible for parsing Array literals `[1, 2, 3]`.
     * This function assumes that it needs to gobble the opening bracket
     * and then tries to gobble the expressions as arguments.
     */
  private gobbleArray (): Ary | ParsingError {
    this.index++

    const elements = this.gobbleArguments(PreJsPy.CHAR_OPEN_BRACKET, PreJsPy.CHAR_CLOSE_BRACKET)
    if (elements instanceof ParsingError) {
      return elements
    }

    return {
      type: ExpressionType.ARRAY_EXP,
      elements
    }
  }

  /**
     * Creates and returns a new default configuration.
     */
  static GetDefaultConfig (): Config {
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
        Conditional: true,
        Identifiers: true,
        Calls: true,
        Members: {
          Static: true,
          Computed: true
        },
        Literals: {
          Numeric: true,
          NumericSeparator: '',
          String: true,
          Array: true
        }
      }
    }
  };
}

// cSpell:words JSEP Oney
