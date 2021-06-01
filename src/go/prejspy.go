package prejspy

import "encoding/json"

// (c) Tom Wiesing 2016-20, licensed under MIT license
// This code is heavily based on the JavaScript version JSEP
// The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT

// PreJSPy is a single instance of the PreJSPy Parser.
type PreJSPy struct {
	literals map[string]interface{}

	unaryOps   []string
	maxUnopLen int

	binOps       map[string]int
	maxBinOpsLen int

	tertiary bool
}

// Gets the constants to be used by this parser.
func (parser *PreJSPy) GetConstants() map[string]interface{} {
	return parser.literals
}

// Sets the constants to be used by this parser.
func (parser *PreJSPy) SetConstants(constants map[string]interface{}) {
	parser.literals = constants
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
	var index, length int

	var exprI func(int) string
	var exprICode func(int) int
	var gobbleExpression, gobbleBinaryExpression, gobbleToken, gobbleNumericLiteral, gobbleStringLiteral, gobbleGroup, gobbleArray, gobbleVariable, gobbleIdentifier func() Expression
	var gobbleArguments func(termination int) (args []Expression)

	// `index` stores the character number we are currently at while `length` is a constant
	// All of the gobbles below will modify `index` as we move along
	exprI = func(i int) string {
		if i >= length {
			return ""
		}
		return string([]rune(expr)[i])
	}

	exprICode = func(i int) int {
		if i >= length {
			return 0
		}
		return int([]rune(expr)[i])
	}

	length = strlen(expr)

	// Push `index` up to the next non-space character
	gobbleSpaces := func() {
		ch := exprICode(index)
		for ch == 32 || ch == 9 {
			index++
			ch = exprICode(index)
		}
	}

	// The main parsing function. Much of this code is dedicated to ternary expressions
	gobbleExpression = func() Expression {
		var test = gobbleBinaryExpression()
		var consequent, alternate Expression

		gobbleSpaces()
		if exprICode(index) == QUMARK_CODE {
			// Ternary expression: test ? consequent : alternate
			index++
			consequent = gobbleExpression()
			if consequent == nil {
				ThrowError("Expected expression", index)
			}
			gobbleSpaces()
			if exprICode(index) == COLON_CODE {
				index++
				alternate = gobbleExpression()
				if alternate == nil {
					ThrowError("Expected expression", index)
				}
				if !parser.GetTertiaryOperatorEnabled() {
					ThrowError("Unexpected tertiary operator", index)
				}
				return ConditionalExpression{
					Test:       test,
					Consequent: consequent,
					Alternate:  alternate,
				}
			} else {
				ThrowError("Expected :", index)
			}
		} else {
			return test
		}
		panic("never reached")
	}

	u_ops := parser.GetUnaryOperators()
	bin_ops := parser.GetBinaryOperators()
	constants := parser.GetConstants()

	// Search for the operation portion of the string (e.g. `+`, `===`)
	// Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
	// and move down from 3 to 2 to 1 character until a matching binary operation is found
	// then, return that binary operation
	gobbleBinaryOp := func() (string, bool) {
		gobbleSpaces()

		to_check := substring(expr, index, parser.GetMaxBinaryOperatorsLength())
		tc_len := strlen(to_check)

		for tc_len > 0 {
			if _, ok := bin_ops[to_check]; ok {
				index += tc_len
				return to_check, true
			}

			tc_len--
			to_check = substring(to_check, 0, tc_len)
		}
		return "", false
	}

	// This function is responsible for gobbling an individual expression,
	// e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
	gobbleBinaryExpression = func() (node Expression) {

		// First, try to get the leftmost thing
		// Then, check to see if there's a binary operator operating on that leftmost thing
		left := gobbleToken()
		biop, biopOK := gobbleBinaryOp()

		// If there wasn't a binary operator, just return the leftmost node
		if !biopOK {
			return left
		}

		// Otherwise, we need to start a stack to properly place the binary operations in their
		// precedence structure
		biop_info := binaryOperator{
			Value: biop, Prec: parser.binaryPrecendence(biop),
		}

		right := gobbleToken()
		if right == nil {
			ThrowError("Expected expression after "+biop, index)
		}

		stack := []Expression{left, biop_info, right}

		biop, biopOK = gobbleBinaryOp()
		for biopOK {
			prec := parser.binaryPrecendence(biop)
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

			node = gobbleToken()
			if node == nil {
				ThrowError("Expected expression after "+biop, index)
			}
			stack = append(stack, biop_info, node)

			biop, biopOK = gobbleBinaryOp()
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

	gobbleToken = func() Expression {
		var ch int
		var to_check string
		var tc_len int

		gobbleSpaces()

		ch = exprICode(index)

		if isDecimalDigit(ch) || ch == PERIOD_CODE { // Char code 46 is a dot `.` which can start off a numeric literal
			return gobbleNumericLiteral()
		} else if ch == SQUOTE_CODE || ch == DQUOTE_CODE { // Single or double quotes
			return gobbleStringLiteral()
		} else if ch == OBRACK_CODE {
			return gobbleArray()
		} else {
			to_check = substring(expr, index, parser.GetMaxUnaryOperatorsLength())
			tc_len = strlen(to_check)

			for tc_len > 0 {
				if contains(u_ops, to_check) {
					index += tc_len
					return UnaryExpression{
						Operator: to_check,
						Argument: gobbleToken(),
					}
				}

				tc_len--
				to_check = substring(to_check, 0, tc_len)
			}

			if isIdentifierStart(ch) || ch == OPAREN_CODE {
				return gobbleVariable()
			}
		}

		return nil
	}

	gobbleNumericLiteral = func() Expression {
		var number, ch string
		var chCode int
		for isDecimalDigit(exprICode(index)) {
			number += exprI(index)
			index++
		}

		if exprICode(index) == PERIOD_CODE {
			number += exprI(index)
			index++

			for isDecimalDigit(exprICode(index)) {
				number += exprI(index)
				index++
			}
		}

		ch = exprI(index)
		if ch == "e" || ch == "E" { // exponent marker
			number += exprI(index)
			index++
			ch = exprI(index)
			if ch == "+" || ch == "-" { // exponent sign
				number += exprI(index)
				index++
			}

			for isDecimalDigit(exprICode(index)) { //exponent itself
				number += exprI(index)
				index++
			}

			if !isDecimalDigit(exprICode(index - 1)) {
				ThrowError("Expected exponent ("+number+exprI(index)+")", index)
			}

		}

		chCode = exprICode(index)

		// Check to make sure this isn't a variable name that start with a number (123abc)
		if isIdentifierStart(chCode) {
			ThrowError("Variable names cannot start with a number ("+number+exprI(index)+")", index)
		} else if chCode == PERIOD_CODE {
			ThrowError("Unexpected period", index)
		}

		// parse the number
		var floatNumber float64
		if err := json.Unmarshal([]byte(number), &floatNumber); err != nil {
			panic(err)
		}

		return Literal{
			Value: floatNumber,
			Raw:   number,
		}
	}

	// Parses a string literal, staring with single or double quotes with basic support for escape codes
	// e.g. `"hello world"`, `'this is\nJSEP'`
	gobbleStringLiteral = func() Expression {
		var str string
		quote := exprI(index)
		index++
		var closed bool
		var ch string

		for index < length {
			ch = exprI(index)
			index++
			if ch == quote {
				closed = true
				break
			} else if ch == "\\" {
				ch = exprI(index)
				index++
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
			} else {
				str += ch
			}
		}

		if !closed {
			ThrowError("Unclosed quote after \""+str+"\"", index)
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
	gobbleIdentifier = func() Expression {
		ch := exprICode(index)
		start := index

		if isIdentifierStart(ch) {
			index++
		} else {
			ThrowError("Unexpected "+exprI(index), index)
		}

		for index < length {
			ch := exprICode(index)
			if isIdentifierPart(ch) {
				index++
			} else {
				break
			}
		}
		identifier := substring(expr, start, index-start)

		if c, ok := constants[identifier]; ok {
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
	gobbleArguments = func(termination int) (args []Expression) {
		var ch_i int

		for index < length {
			gobbleSpaces()
			ch_i = exprICode(index)
			if ch_i == termination {
				index++
				break
			} else if ch_i == COMMA_CODE {
				index++
			} else {
				node := gobbleExpression()
				if node == nil || node.Type() == COMPOUND {
					ThrowError("Expected comma", index)
				}
				args = append(args, node)
			}
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
	gobbleVariable = func() (node Expression) {

		ch_i := exprICode(index)
		if ch_i == OPAREN_CODE {
			node = gobbleGroup()
		} else {
			node = gobbleIdentifier()
		}
		gobbleSpaces()

		ch_i = exprICode(index)
		for ch_i == PERIOD_CODE || ch_i == OBRACK_CODE || ch_i == OPAREN_CODE {
			index++

			if ch_i == PERIOD_CODE {
				gobbleSpaces()
				node = MemberExpression{
					Computed: false,
					Object:   node,
					Property: gobbleIdentifier(),
				}
			} else if ch_i == OBRACK_CODE {
				node = MemberExpression{
					Computed: true,
					Object:   node,
					Property: gobbleExpression(),
				}
				gobbleSpaces()
				ch_i = exprICode(index)
				if ch_i != CBRACK_CODE {
					ThrowError("Unclosed [", index)
				}
				index++
			} else if ch_i == OPAREN_CODE {
				// A function call is being made; gobble all the arguments
				node = CallExpression{
					Arguments: gobbleArguments(CPAREN_CODE),
					Callee:    node,
				}
			}
			gobbleSpaces()
			ch_i = exprICode(index)
		}
		return
	}

	// Responsible for parsing a group of things within parentheses `()`
	// This function assumes that it needs to gobble the opening parenthesis
	// and then tries to gobble everything within that parenthesis, assuming
	// that the next thing it should see is the close parenthesis. If not,
	// then the expression probably doesn't have a `)`
	gobbleGroup = func() Expression {
		index++
		node := gobbleExpression()
		gobbleSpaces()
		if exprICode(index) == CPAREN_CODE {
			index++
			return node
		} else {
			ThrowError("Unclosed (", index)
		}
		return nil
	}

	// Responsible for parsing Array literals `[1, 2, 3]`
	// This function assumes that it needs to gobble the opening bracket
	// and then tries to gobble the expressions as arguments.
	gobbleArray = func() Expression {
		index++
		return ArrayExpression{
			Elements: gobbleArguments(CBRACK_CODE),
		}
	}

	var nodes []Expression
	var ch_i int

	for index < length {
		ch_i = exprICode(index)

		// Expressions can be separated by semicolons, commas, or just inferred without any
		// separators
		if ch_i == SEMCOL_CODE || ch_i == COMMA_CODE {
			index++ // ignore separators
		} else {
			node := gobbleExpression()
			if node != nil {
				nodes = append(nodes, node)
			} else if index < length {
				ThrowError("Unexpected \""+exprI(index)+"\"", index)
			}
		}
	}

	// If there's only one expression just try returning the expression
	if len(nodes) == 1 {
		return nodes[0]
	} else {
		return Compound{
			Body: nodes,
		}
	}
}
