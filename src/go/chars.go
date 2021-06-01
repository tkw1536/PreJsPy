package prejspy

const (
	PERIOD_CODE = 46 // '.'
	COMMA_CODE  = 44 // ','
	SQUOTE_CODE = 39 // single quote
	DQUOTE_CODE = 34 // double quotes
	OPAREN_CODE = 40 // (
	CPAREN_CODE = 41 // )
	OBRACK_CODE = 91 // [
	CBRACK_CODE = 93 // ]
	QUMARK_CODE = 63 // ?
	SEMCOL_CODE = 59 // ;
	COLON_CODE  = 58 // :
)

// isDecimalDigit checks if ch is a decimal digit
func isDecimalDigit(ch int) bool {
	return ch >= 48 && ch <= 57 // 0...9
}

// isIdentifierStart checks if ch is an identifier
func isIdentifierStart(ch int) bool {
	return (ch == 36) || (ch == 95) || // `$` and `_`
		(ch >= 65 && ch <= 90) || // A...Z
		(ch >= 97 && ch <= 122) || // a...z
		ch >= 128 // non-ascii
}

// isIdentifierPart checks if ch is a part of an identifier
func isIdentifierPart(ch int) bool {
	return (ch == 36) || (ch == 95) || // `$` and `_`
		(ch >= 65 && ch <= 90) || // A...Z
		(ch >= 97 && ch <= 122) || // a...z
		(ch >= 48 && ch <= 57) || // 0...9
		ch >= 128 // non-ascii
}
