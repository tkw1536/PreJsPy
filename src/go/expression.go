package prejspy

import "encoding/json"

type ASTKind string

const (
	COMPOUND        ASTKind = "Compound"
	IDENTIFIER      ASTKind = "Identifier"
	MEMBER_EXP      ASTKind = "MemberExpression"
	LITERAL         ASTKind = "Literal"
	CALL_EXP        ASTKind = "CallExpression"
	UNARY_EXP       ASTKind = "UnaryExpression"
	BINARY_EXP      ASTKind = "BinaryExpression"
	CONDITIONAL_EXP ASTKind = "ConditionalExpression"
	ARRAY_EXP       ASTKind = "ArrayExpression"
)

type Expression interface {
	Type() ASTKind
	isExpression() // sealed
}

// Compound is a compound expression consisting of multiple Expressions
type Compound struct {
	Body []Expression `json:"body"`
}

func (Compound) Type() ASTKind { return COMPOUND }
func (Compound) isExpression() {}

func (expr Compound) MarshalJSON() ([]byte, error) {
	type Fake Compound
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// Idenfitifer is an identifier
type Identifier struct {
	Name string `json:"name"`
}

func (Identifier) Type() ASTKind { return IDENTIFIER }
func (Identifier) isExpression() {}

func (expr Identifier) MarshalJSON() ([]byte, error) {
	type Fake Identifier
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// MemberExpression is a member expression
type MemberExpression struct {
	Computed bool       `json:"computed"`
	Object   Expression `json:"object"`
	Property Expression `json:"property"`
}

func (MemberExpression) Type() ASTKind { return MEMBER_EXP }
func (MemberExpression) isExpression() {}

func (expr MemberExpression) MarshalJSON() ([]byte, error) {
	type Fake MemberExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// Literal is a literal
type Literal struct {
	Value interface{} `json:"value"` // dependening on the type of literal
	Raw   string      `json:"raw"`
}

func (Literal) isExpression() {}
func (Literal) Type() ASTKind { return LITERAL }

func (expr Literal) MarshalJSON() ([]byte, error) {
	type Fake Literal
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// CallExpression is a call expression
type CallExpression struct {
	Arguments []Expression `json:"arguments"`
	Callee    Expression   `json:"callee"`
}

func (CallExpression) isExpression() {}
func (CallExpression) Type() ASTKind { return CALL_EXP }

func (expr CallExpression) MarshalJSON() ([]byte, error) {
	type Fake CallExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// UnaryExpression is a unary expression
type UnaryExpression struct {
	Operator string     `json:"operator"`
	Argument Expression `json:"argument"`
}

func (UnaryExpression) isExpression() {}
func (UnaryExpression) Type() ASTKind { return UNARY_EXP }

func (expr UnaryExpression) MarshalJSON() ([]byte, error) {
	type Fake UnaryExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// BinaryExpression is a binary expression
type BinaryExpression struct {
	Operator string     `json:"operator"`
	Left     Expression `json:"left"`
	Right    Expression `json:"right"`
}

func (BinaryExpression) isExpression() {}
func (BinaryExpression) Type() ASTKind { return BINARY_EXP }

func (expr BinaryExpression) MarshalJSON() ([]byte, error) {
	type Fake BinaryExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// ConditionalExpression is a conditional expression
type ConditionalExpression struct {
	Test       Expression `json:"test"`
	Consequent Expression `json:"consequent"`
	Alternate  Expression `json:"alternate"`
}

func (ConditionalExpression) isExpression() {}
func (ConditionalExpression) Type() ASTKind { return CONDITIONAL_EXP }

func (expr ConditionalExpression) MarshalJSON() ([]byte, error) {
	type Fake ConditionalExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

// ArrayExpression is an array expression
type ArrayExpression struct {
	Elements []Expression `json:"elements"`
}

func (ArrayExpression) isExpression() {}
func (ArrayExpression) Type() ASTKind { return ARRAY_EXP }

func (expr ArrayExpression) MarshalJSON() ([]byte, error) {
	type Fake ArrayExpression
	return json.Marshal(struct {
		Fake
		Type ASTKind `json:"type"`
	}{
		Fake: Fake(expr),
		Type: expr.Type(),
	})
}

type binaryOperator struct {
	Value string
	Prec  int
}

func (binaryOperator) Type() ASTKind { panic("implementation error") }
func (binaryOperator) isExpression() {}
