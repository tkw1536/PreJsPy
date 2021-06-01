package prejspy

import "encoding/json"

// (c) Tom Wiesing 2016-20, licensed under MIT license
// This code is heavily based on the JavaScript version JSEP
// The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT

// PreJSPy is a single instance of the PreJSPy Parser.
type PreJSPy struct {
	constants map[string]interface{}

	unaryOps   []string
	maxUnopLen int

	binOps       map[string]int
	maxBinOpsLen int

	tertiary bool
}

// Gets the constants to be used by this parser.
func (parser *PreJSPy) GetConstants() map[string]interface{} {
	return parser.constants
}

// Sets the constants to be used by this parser.
func (parser *PreJSPy) SetConstants(constants map[string]interface{}) {
	parser.constants = constants
}

// Gets the unary operators known to this parser.
func (parser *PreJSPy) GetUnaryOperators() []string {
	return parser.unaryOps
}

// Sets the unary operators known to this parser.
func (parser *PreJSPy) SetUnaryOperators(operators []string) {
	parser.unaryOps = operators
	parser.maxUnopLen = getMaxMemLen(operators)
}

func (parser *PreJSPy) GetMaxUnaryOperatorsLength() int {
	return parser.maxUnopLen
}

func (parser *PreJSPy) GetBinaryOperators() map[string]int {
	return parser.binOps
}

func (parser *PreJSPy) GetMaxBinaryOperatorsLength() int {
	return parser.maxBinOpsLen
}

func (parser *PreJSPy) SetBinaryOperators(operators map[string]int) {
	parser.binOps = operators
	parser.maxBinOpsLen = getMaxKeyLen(operators)
}

func (parser *PreJSPy) SetTertiaryOperatorEnabled(enabled bool) {
	parser.tertiary = enabled
}

func (parser *PreJSPy) GetTertiaryOperatorEnabled() bool {
	return parser.tertiary
}

// =========
// INIT CODE
// =========

func NewPreJSPy() *PreJSPy {
	parser := &PreJSPy{}

	parser.SetConstants(map[string]interface{}{
		"true":  true,
		"false": false,
		"null":  nil,
	})
	parser.SetUnaryOperators([]string{"-", "!", "~", "+"})
	parser.SetBinaryOperators(map[string]int{
		"||": 1, "&&": 2, "|": 3, "^": 4, "&": 5,
		"==": 6, "!=": 6, "===": 6, "!==": 6,
		"<": 7, ">": 7, "<=": 7, ">=": 7,
		"<<": 8, ">>": 8, ">>>": 8,
		"+": 9, "-": 9,
		"*": 10, "/": 10, "%": 10,
	})
	parser.SetTertiaryOperatorEnabled(true)

	return parser
}

// ============
// MISC HELPERS
// ============

// Returns the precedence of a binary operator or `0` if it isn't a binary operator.
func (parser *PreJSPy) binaryPrecendence(op_val string) int {
	if value, ok := parser.GetBinaryOperators()[op_val]; ok {
		return value
	}
	return 0
}

// =======
// Parsing
// =======

func (parser *PreJSPy) Parse(expr string) Expression {
	run := &ParsingRun{
		PreJSPy: parser,
	}
	run.Reset(expr)
	return run.Run()
}

// ParsingRun represents a single run of the parser
type ParsingRun struct {
	*PreJSPy

	// expr is the expression to be parsed
	expr []rune

	// `index` stores the character number we are currently at while `length` is a constant
	// All of the gobbles below will modify `index` as we move along
	index, length int
}

// Reset resets the data in this ParsingRun
func (r *ParsingRun) Reset(expr string) {
	r.expr = []rune(expr)
	r.index = 0
	r.length = len(r.expr)
}

// exprI returns the current character
func (r ParsingRun) exprI() string {
	if r.index >= r.length {
		return ""
	}
	return string(r.expr[r.index])
}

// exprICode returns the current character
func (r ParsingRun) exprICode() int {
	if r.index >= r.length {
		return 0
	}
	return int(r.expr[r.index])
}

// TODO: substring!

// Run runs this parsing run
func (r *ParsingRun) Run() Expression {

	var nodes []Expression
	var ch_i int

	for r.index < r.length {
		ch_i = r.exprICode()

		// Expressions can be separated by semicolons, commas, or just inferred without any
		// separators
		if ch_i == SEMCOL_CODE || ch_i == COMMA_CODE {
			r.index++ // ignore separators
			continue
		}

		node := r.gobbleExpression()
		if node != nil {
			nodes = append(nodes, node)
		} else if r.index < r.length {
			ThrowError("Unexpected \""+r.exprI()+"\"", r.index)
		}
	}

	// If there's only one expression just try returning the expression
	if len(nodes) == 1 {
		return nodes[0]
	}

	return Compound{
		Body: nodes,
	}
}

func (r *ParsingRun) gobbleSpaces() {
	var ch int
	for {
		ch = r.exprICode()
		if !(ch == 32 || ch == 9) {
			break
		}
		r.index++
	}
}

// The main parsing function. Much of this code is dedicated to ternary expressions
func (r *ParsingRun) gobbleExpression() Expression {
	var test = r.gobbleBinaryExpression()
	var consequent, alternate Expression

	r.gobbleSpaces()

	if r.exprICode() != QUMARK_CODE {
		return test
	}
	r.index++

	// Ternary expression: test ? consequent : alternate
	consequent = r.gobbleExpression()
	if consequent == nil {
		ThrowError("Expected expression", r.index)
	}

	r.gobbleSpaces()

	if r.exprICode() != COLON_CODE {
		ThrowError("Expected :", r.index)
	}
	r.index++

	alternate = r.gobbleExpression()
	if alternate == nil {
		ThrowError("Expected expression", r.index)
	}
	if !r.GetTertiaryOperatorEnabled() {
		ThrowError("Unexpected tertiary operator", r.index)
	}

	return ConditionalExpression{
		Test:       test,
		Consequent: consequent,
		Alternate:  alternate,
	}
}

// Search for the operation portion of the string (e.g. `+`, `===`)
// Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
// and move down from 3 to 2 to 1 character until a matching binary operation is found
// then, return that binary operation
func (r *ParsingRun) gobbleBinaryOp() (string, bool) {
	r.gobbleSpaces()

	to_check := substring(string(r.expr), r.index, r.GetMaxBinaryOperatorsLength())
	tc_len := strlen(to_check)

	for tc_len > 0 {
		if _, ok := r.binOps[to_check]; ok {
			r.index += tc_len
			return to_check, true
		}

		tc_len--
		to_check = substring(to_check, 0, tc_len)
	}

	return "", false
}

// This function is responsible for gobbling an individual expression,
// e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
func (r *ParsingRun) gobbleBinaryExpression() (node Expression) {

	// First, try to get the leftmost thing
	// Then, check to see if there's a binary operator operating on that leftmost thing
	left := r.gobbleToken()

	biop, biopOK := r.gobbleBinaryOp()
	if !biopOK {
		return left
	}

	// Otherwise, we need to start a stack to properly place the binary operations in their
	// precedence structure
	biop_info := binaryOperator{
		Value: biop, Prec: r.binaryPrecendence(biop),
	}

	right := r.gobbleToken()
	if right == nil {
		ThrowError("Expected expression after "+biop, r.index)
	}

	stack := []Expression{left, biop_info, right}

	for {
		biop, biopOK := r.gobbleBinaryOp()
		if !biopOK {
			break
		}

		prec := r.binaryPrecendence(biop)
		if prec == 0 {
			break
		}

		biop_info = binaryOperator{Value: biop, Prec: prec}

		var op Expression
		for len(stack) > 2 && (prec <= stack[len(stack)-2].(binaryOperator).Prec) {
			right, stack = stack[len(stack)-1], stack[:len(stack)-1]
			op, stack = stack[len(stack)-1], stack[:len(stack)-1]
			left, stack = stack[len(stack)-1], stack[:len(stack)-1]

			biop = op.(binaryOperator).Value

			stack = append(stack, BinaryExpression{
				Operator: biop,
				Left:     left,
				Right:    right,
			})
		}

		node = r.gobbleToken()
		if node == nil {
			ThrowError("Expected expression after "+biop, r.index)
		}
		stack = append(stack, biop_info, node)
	}

	i := len(stack) - 1
	node = stack[i]
	for i > 1 {
		node = BinaryExpression{
			Operator: stack[i-1].(binaryOperator).Value,
			Left:     stack[i-2],
			Right:    node,
		}
		i -= 2
	}
	return node
}

func (r *ParsingRun) gobbleToken() Expression {
	r.gobbleSpaces()

	ch := r.exprICode()
	switch {
	// Char code 46 is a dot `.` which can start off a numeric literal
	case isDecimalDigit(ch) || ch == PERIOD_CODE:
		return r.gobbleNumericLiteral()
	// Single or double quotes
	case ch == SQUOTE_CODE || ch == DQUOTE_CODE:
		return r.gobbleStringLiteral()
	case ch == OBRACK_CODE:
		return r.gobbleArray()
	}

	to_check := substring(string(r.expr), r.index, r.GetMaxUnaryOperatorsLength())
	tc_len := strlen(to_check)

	for tc_len > 0 {
		if contains(r.unaryOps, to_check) {
			r.index += tc_len
			return UnaryExpression{
				Operator: to_check,
				Argument: r.gobbleToken(),
			}
		}

		tc_len--
		to_check = substring(to_check, 0, tc_len) // TODO: Optimize this operation
	}

	if isIdentifierStart(ch) || ch == OPAREN_CODE {
		return r.gobbleVariable()
	}

	return nil
}

func (r *ParsingRun) gobbleNumericLiteral() Expression {
	var number, ch string
	var chCode int
	for isDecimalDigit(r.exprICode()) {
		number += r.exprI()
		r.index++
	}

	if r.exprICode() == PERIOD_CODE {
		number += r.exprI()
		r.index++

		for isDecimalDigit(r.exprICode()) {
			number += r.exprI()
			r.index++
		}
	}

	ch = r.exprI()
	if ch == "e" || ch == "E" { // exponent marker
		number += r.exprI()
		r.index++
		ch = r.exprI()
		if ch == "+" || ch == "-" { // exponent sign
			number += r.exprI()
			r.index++
		}

		for isDecimalDigit(r.exprICode()) { //exponent itself
			number += r.exprI()
			r.index++
		}

		// check that the last digit is a decimal digit
		r.index--
		isDecimalDigit := isDecimalDigit(r.exprICode())
		r.index++

		if !isDecimalDigit {
			ThrowError("Expected exponent ("+number+r.exprI()+")", r.index)
		}

	}

	chCode = r.exprICode()

	// Check to make sure this isn't a variable name that start with a number (123abc)
	if isIdentifierStart(chCode) {
		ThrowError("Variable names cannot start with a number ("+number+r.exprI()+")", r.index)
	} else if chCode == PERIOD_CODE {
		ThrowError("Unexpected period", r.index)
	}

	// parse the number
	var floatNumber float64
	if err := json.Unmarshal([]byte(number), &floatNumber); err != nil {
		panic(err)
	}

	// and return the literal!
	return Literal{
		Value: floatNumber,
		Raw:   number,
	}
}

// Parses a string literal, staring with single or double quotes with basic support for escape codes
// e.g. `"hello world"`, `'this is\nJSEP'`
func (r *ParsingRun) gobbleStringLiteral() Expression {
	var str string

	quote := r.exprI()
	r.index++

	var closed bool
	for r.index < r.length {
		ch := r.exprI()
		r.index++

		if ch == quote {
			closed = true
			break
		}
		if ch != "\\" {
			str += ch
			continue
		}

		ch = r.exprI()
		r.index++
		switch ch {
		case "n":
			str += "\n"
		case "r":
			str += "\r"
		case "t":
			str += "\t"
		case "b":
			str += "\b"
		case "f":
			str += "\f"
		case "v":
			str += "\x0B"
		case "\\":
			str += "\\"

		// default: just add the character literally.
		default:
			str += ch
		}
	}

	if !closed {
		ThrowError("Unclosed quote after \""+str+"\"", r.index)
	}

	return Literal{
		Value: str,
		Raw:   quote + str + quote,
	}
}

// Gobbles only identifiers
// e.g.: `foo`, `_value`, `$x1`
// Also, this function checks if that identifier is a literal:
// (e.g. `true`, `false`, `null`) or `this`
func (r *ParsingRun) gobbleIdentifier() Expression {
	ch := r.exprICode()
	start := r.index

	if !isIdentifierStart(ch) {
		ThrowError("Unexpected "+r.exprI(), r.index)
	}
	r.index++

	for r.index < r.length {
		ch := r.exprICode()
		if !isIdentifierPart(ch) {
			break
		}
		r.index++
	}

	identifier := substring(string(r.expr), start, r.index-start)

	if c, ok := r.constants[identifier]; ok {
		return Literal{
			Value: c,
			Raw:   identifier,
		}
	} else {
		return Identifier{
			Name: identifier,
		}
	}
}

// Gobbles a list of arguments within the context of a function call
// or array literal. This function also assumes that the opening character
// `(` or `[` has already been gobbled, and gobbles expressions and commas
// until the terminator character `)` or `]` is encountered.
// e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
func (r *ParsingRun) gobbleArguments(termination int) (args []Expression) {
	for r.index < r.length {
		r.gobbleSpaces()
		ch_i := r.exprICode()
		if ch_i == termination {
			r.index++
			break
		}

		if ch_i == COMMA_CODE {
			r.index++
			continue
		}

		node := r.gobbleExpression()
		if node == nil || node.Type() == COMPOUND {
			ThrowError("Expected comma", r.index)
		}
		args = append(args, node)
	}

	if args == nil {
		args = []Expression{}
	}

	return args
}

// Gobble a non-literal variable name. This variable name may include properties
// e.g. `foo`, `bar.baz`, `foo['bar'].baz`
// It also gobbles function calls:
// e.g. `Math.acos(obj.angle)`
func (r *ParsingRun) gobbleVariable() (node Expression) {

	ch_i := r.exprICode()
	if ch_i == OPAREN_CODE {
		node = r.gobbleGroup()
	} else {
		node = r.gobbleIdentifier()
	}

loop:
	for {
		r.gobbleSpaces()
		ch_i := r.exprICode()
		r.index++

		switch ch_i {
		case PERIOD_CODE:
			r.gobbleSpaces()
			node = MemberExpression{
				Computed: false,
				Object:   node,
				Property: r.gobbleIdentifier(),
			}
		case OBRACK_CODE:
			node = MemberExpression{
				Computed: true,
				Object:   node,
				Property: r.gobbleExpression(),
			}
			r.gobbleSpaces()
			ch_i = r.exprICode()
			if ch_i != CBRACK_CODE {
				ThrowError("Unclosed [", r.index)
			}
			r.index++
		case OPAREN_CODE:
			// A function call is being made; gobble all the arguments
			node = CallExpression{
				Arguments: r.gobbleArguments(CPAREN_CODE),
				Callee:    node,
			}
		default:
			r.index--
			break loop
		}
	}
	return
}

// Responsible for parsing a group of things within parentheses `()`
// This function assumes that it needs to gobble the opening parenthesis
// and then tries to gobble everything within that parenthesis, assuming
// that the next thing it should see is the close parenthesis. If not,
// then the expression probably doesn't have a `)`
func (r *ParsingRun) gobbleGroup() Expression {
	r.index++
	node := r.gobbleExpression()

	r.gobbleSpaces()
	if r.exprICode() != CPAREN_CODE {
		ThrowError("Unclosed (", r.index)
	}

	r.index++
	return node
}

// Responsible for parsing Array literals `[1, 2, 3]`
// This function assumes that it needs to gobble the opening bracket
// and then tries to gobble the expressions as arguments.
func (r *ParsingRun) gobbleArray() Expression {
	r.index++

	return ArrayExpression{
		Elements: r.gobbleArguments(CBRACK_CODE),
	}
}
