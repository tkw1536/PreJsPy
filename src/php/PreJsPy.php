<?php

/**
 * (c) Tom Wiesing 2016-23, licensed under MIT license
 * This code is inspired by the JavaScript version JSEP
 * The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and
 * licensed under MIT
 */

/**
 * Represents the type of expressions. 
 */
enum ExpressionType: string
{
    case COMPOUND = 'Compound';
    case IDENTIFIER = 'Identifier';
    case MEMBER_EXP = 'MemberExpression';
    case LITERAL = 'Literal';
    case CALL_EXP = 'CallExpression';
    case UNARY_EXP = 'UnaryExpression';
    case BINARY_EXP = 'BinaryExpression';
    case CONDITIONAL_EXP = 'ConditionalExpression';
    case ARRAY_EXP = 'ArrayExpression';
}

class ParsingError extends Exception
{

    public readonly string $error;
    public readonly string $expr;
    public readonly int $index;

    /**
     * Creates a new ParsingError.
     *
     * @param string $error Error message produced by the parser
     * @param string $expr Expression that was originally parsed
     * @param integer $index Index of position in the expression where the error occurred
     */
    public function __construct(string $error, string $expr, int $index)
    {
        $this->error = $error;
        $this->expr = $expr;
        $this->index = $index;

        parent::__construct('Index ' . strval($index) . ' of ' . json_encode($expr) . ': ' . $error, 0, null);
    }
}



/**
 * Represents a single instance of the PreJsPy parser
 */
class PreJsPy
{
    private const CHAR_PERIOD = '.';
    private const CHAR_COMMA = ',';
    private const CHAR_SINGLE_QUOTE = '\'';
    private const CHAR_DOUBLE_QUOTE = '"';
    private const CHAR_OPEN_PARENTHESES = '(';
    private const CHAR_CLOSE_PARENTHESES = ')';
    private const CHAR_OPEN_BRACKET = '[';
    private const CHAR_CLOSE_BRACKET = ']';
    private const CHAR_QUESTIONMARK = '?';
    private const CHAR_SEMICOLON = ';';
    private const CHAR_COLON = ':';
    private const CHAR_SPACE = ' ';
    private const CHAR_TAB = '\t';

    // =======================
    // Error Messages
    // =======================

    /**
     * Throws a parser error with a given message and a given index.
     *
     * @param string $message
     * @return never
     */
    private function throw_error(string $message): never
    {
        throw new ParsingError($message, $this->expr, $this->index);
    }

    // =======================
    // STATIC HELPER FUNCTIONS
    // =======================

    /**
     * Gets the longest key length of an object
     *
     * @param array $o Object to iterate over.
     * @return integer
     */
    private static function getMaxKeyLen(array $o): int
    {
        $len = 0;
        foreach ($o as $key => $value) {
            $keyLen = mb_strlen($key, 'UTF-8');
            if ($keyLen > $len) {
                $len = $keyLen;
            }
        }
        return $len;
    }

    /**
     * Gets the maximum length of the member of any members of an array.
     *
     * @param array $ary Array to iterate over.
     * @return integer
     */
    private static function getMaxMemLen(array $ary): int
    {
        $len = 0;
        foreach ($ary as $value) {
            $valueLen = mb_strlen($value, 'UTF-8');
            if ($valueLen > $len) {
                $len = $valueLen;
            }
        }
        return $len;
    }

    /**
     * Checks if a character is a decimal digit.
     *
     * @param string $ch Character to check.
     * @return boolean
     */
    private static function isDecimalDigit(string $ch): bool
    {
        return mb_strlen($ch, 'UTF-8') === 1 && $ch >= '0' && $ch <= '9';
    }

    /**
     * Checks if a character is the start of an identifier.
     *
     * @param string $ch Character to check.
     * @return boolean
     */
    private static function isIdentifierStart(string $ch): bool
    {
        return mb_strlen($ch, 'UTF-8') === 1 && (
            ($ch === '$')
            || ($ch === '_')
            || ($ch >= 'a' && $ch <= 'z')
            || ($ch >= 'A' && $ch <= 'Z')
            || (ord($ch) >= 128) // non-ascii
        );
    }

    /**
     * Checks if a character is part of an identifier.
     *
     * @param string $ch Character to check.
     * @return boolean
     */
    private static function isIdentifierPart(string $ch): bool
    {
        return mb_strlen($ch, 'UTF-8') === 1 && (
            ($ch === '$')
            || ($ch === '_')
            || ($ch >= 'a' && $ch <= 'z')
            || ($ch >= 'A' && $ch <= 'Z')
            || ($ch >= '0' && $ch <= '9')
            || (ord($ch) >= 128) // non-ascii
        );
    }

    /**
     * Copies a dictionary or list
     *
     * @param array $dict
     * @return array
     */
    private static function copy(array $ary): array
    {
        return array_merge(array(), $ary);
    }

    // =======
    // CONFIG
    // =======

    /**
     * Gets the current config used by this parser.
     *
     * @return array
     */
    public function GetConfig(): array
    {
        return [
            'Operators' => [
                'Literals' => self::copy($this->config['Operators']['Literals']),
                'Unary' => self::copy($this->config['Operators']['Unary']),
                'Binary' => self::copy($this->config['Operators']['Binary']),
            ],
            'Features' => [
                'Compound' => $this->config['Features']['Compound'],
                'Conditional' => $this->config['Features']['Conditional'],
                'Identifiers' => $this->config['Features']['Identifiers'],
                'Calls' => $this->config['Features']['Calls'],
                'Members' => self::copy($this->config['Features']['Members']),
                'Literals' => self::copy($this->config['Features']['Literals']),
            ]
        ];
    }

    /**
     * Sets the config used by this parser.
     *
     * @param array|null $config (Possibly partial) configuration to use.
     * @return void
     */
    public function SetConfig(array|null $config): array
    {
        if ($config !== null) {
            if (array_key_exists('Operators', $config)) {
                if (array_key_exists('Literals', $config['Operators'])) {
                    $this->config['Operators']['Literals'] = self::copy($config['Operators']['Literals']);
                }
                if (array_key_exists('Unary', $config['Operators'])) {
                    $this->config['Operators']['Unary'] = self::copy($config['Operators']['Unary']);
                    $this->unaryOperatorLength = self::getMaxMemLen($this->config['Operators']['Unary']);
                }
                if (array_key_exists('Binary', $config['Operators'])) {
                    $this->config['Operators']['Binary'] = self::copy($config['Operators']['Binary']);
                    $this->binaryOperatorLength = self::getMaxKeyLen($this->config['Operators']['Binary']);
                }
            }
            if (array_key_exists('Features', $config)) {
                if (array_key_exists('Compound', $config['Features'])) {
                    $this->config['Features']['Compound'] = $config['Features']['Compound'];
                }
                if (array_key_exists('Conditional', $config['Features'])) {
                    $this->config['Features']['Conditional'] = $config['Features']['Conditional'];
                }
                if (array_key_exists('Identifiers', $config['Features'])) {
                    $this->config['Features']['Identifiers'] = $config['Features']['Identifiers'];
                }
                if (array_key_exists('Calls', $config['Features'])) {
                    $this->config['Features']['Calls'] = $config['Features']['Calls'];
                }
                if (array_key_exists('Members', $config['Features'])) {
                    if (array_key_exists('Computed', $config['Features']['Members'])) {
                        $this->config['Features']['Members']['Computed'] = $config['Features']['Members']['Computed'];
                    }
                    if (array_key_exists('Static', $config['Features']['Members'])) {
                        $this->config['Features']['Members']['Static'] = $config['Features']['Members']['Static'];
                    }
                }
                if (array_key_exists('Literals', $config['Features'])) {
                    if (array_key_exists('Array', $config['Features']['Literals'])) {
                        $this->config['Features']['Literals']['Array'] = $config['Features']['Literals']['Array'];
                    }
                    if (array_key_exists('Numeric', $config['Features']['Literals'])) {
                        $this->config['Features']['Literals']['Numeric'] = $config['Features']['Literals']['Numeric'];
                    }
                    if (array_key_exists('NumericSeparator', $config['Features']['Literals'])) {
                        $this->config['Features']['Literals']['NumericSeparator'] = $config['Features']['Literals']['NumericSeparator'];
                    }
                    if (array_key_exists('String', $config['Features']['Literals'])) {
                        $this->config['Features']['Literals']['String'] = $config['Features']['Literals']['String'];
                    }
                }
            }
        }
        return $this->GetConfig();
    }

    // =========
    // INIT CODE
    // =========
    private array $config;
    private int $unaryOperatorLength;
    private int $binaryOperatorLength;

    /**
     * Creates a new PreJsPy instance
     */
    public function __construct()
    {
        $this->config = self::GetDefaultConfig();
        $this->SetConfig($this->config);
    }


    // ============
    // MISC HELPERS
    // ============

    private function binaryPrecedence(string $op_val): int
    {
        if (!array_key_exists($op_val, $this->config['Operators']['Binary'])) {
            return 0;
        }

        return $this->config['Operators']['Binary'][$op_val];
    }

    // =======
    // PARSING
    // =======

    private int $index = 0;
    private int $length = 0;
    private string $expr = '';

    private function char(): string
    {
        if ($this->index > $this->length) {
            return '';
        }
        return mb_substr($this->expr, $this->index, 1);
    }

    /**
     * Parses an expression into a parse tree.
     *
     * @param string $expr Expression to pare
     * @return array
     */
    public function Parse(string $expr): array
    {
        try {
            $this->index = 0;
            $this->expr = $expr;
            $this->length = mb_strlen($expr, 'UTF-8');

            return $this->gobbleCompound();
        } finally {
            // to avoid leaks of the state
            $this->index = 0;
            $this->expr = '';
            $this->length = 0;
        }
    }

    public function TryParse(string $expr): array
    {
        try {
            $result = $this->Parse($expr);
            return [$result, null];
        } catch (ParsingError $pe) {
            return [null, $pe];
        }
    }

    public function gobbleCompound(): array
    {
        $nodes = [];

        while ($this->index < $this->length) {

            $ch = $this->char();

            // Expressions can be separated by semicolons, commas, or just inferred without any separators
            if ($ch === self::CHAR_SEMICOLON || $ch == self::CHAR_COMMA) {
                continue;
            }

            // Try to gobble each expression individually
            $node = $this->gobbleExpression();
            if ($node === NULL) {
                break;
            }

            $nodes[] = $node;
        }

        // didn't find an expression => something went wrong
        if ($this->index < $this->length) {
            $this->throw_error('Unexpected ' . json_encode($this->char()));
        }

        // If there is only one expression, return it as is
        if (count($nodes) === 1) {
            return $nodes[0];
        }

        // do not allow compound expressions if they are not enabled
        if (!$this->config['Features']['Compound']) {
            $this->throw_error('Unexpected compound expression');
        }

        return [
            'type' => ExpressionType::COMPOUND,
            'body' => $nodes,
        ];
    }

    /**
     * Advances the index to the next non-space character.
     *
     * @return string the next non-space character
     */
    private function skipSpaces(): string
    {
        while(TRUE) {
            $ch = $this->char();
            if (!($ch === self::CHAR_SPACE || $ch === self::CHAR_TAB)) {
                return $ch;
            }
            $this->index++;
        }
    }

    /**
     * Main parsing function to parse any kind of expression
     *
     * @return array|null
     */
    private function gobbleExpression(): array | null
    {

        // gobble a binary expression
        $test = $this->gobbleBinaryExpression();

        // only continue if there is a chance of finding a conditional
        if ((!$this->config['Features']['Conditional']) || $test === null) {
            return $test;
        }

        // not a conditional expression => return immediately
        $ch = $this->skipSpaces();
        if ($ch !== self::CHAR_QUESTIONMARK || $test === null) {
            return $test;
        }

        // conditional expression: test ? consequent : alternate
        $this->index++;
        $consequent = $this->gobbleExpression();
        if ($consequent === null) {
            $this->throw_error('Expected expression');
        }

        // need a ':' for the second part of the alternate
        $ch = $this->skipSpaces();
        if ($ch !== self::CHAR_COLON) {
            $this->throw_error('Expected ' . json_encode(self::CHAR_COLON));
        }

        $this->index++;
        $alternate = $this->gobbleExpression();

        if ($alternate === null) {
            $this->throw_error('Expected expression');
        }

        return [
            'type' => ExpressionType::CONDITIONAL_EXP,
            'test' => $test,
            'consequent' => $consequent,
            'alternate' => $alternate,
        ];
    }

    /**
     * Search for the operation portion of the string (e.g. `+`, `===`)
     * Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
     * and move down from 3 to 2 to 1 character until a matching binary operation is found
     * then, return that binary operation
     *
     * @return string|null
     */
    private function gobbleBinaryOp(): string|null
    {
        $this->skipSpaces();

        $to_check = mb_substr($this->expr, $this->index, $this->binaryOperatorLength, 'UTF-8');
        $tc_len = mb_strlen($to_check, 'UTF-8');

        while ($tc_len > 0) {
            if (array_key_exists($to_check, $this->config['Operators']['Binary'])) {
                $this->index += $tc_len;
                return $to_check;
            }
            $tc_len--;
            $to_check = mb_substr($to_check, 0, $tc_len, 'UTF-8');
        }

        return null;
    }

    /**
     * This function is responsible for gobbling an individual expression,
     * e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
     *
     * @return array|null
     */
    public function gobbleBinaryExpression(): array|null
    {
        // Get the leftmost token of a binary expression or bail out
        $left = $this->gobbleToken();
        if ($left === null) {
            return null;
        }

        $exprs = [$left]; // a list of expressions
        $ops = []; // and a list of binary operators between them

        // Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
        while (True) {
            $value = $this->gobbleBinaryOp();
            if ($value === null) {
                break;
            }

            $precedence = $this->binaryPrecedence($value);
            if ($precedence === 0) {
                break;
            }

            // Reduce: make a binary expression from the three topmost entries.
            while ((count($ops) > 0) && $precedence < end($ops)['precedence']) {
                $right = array_pop($exprs);
                $left = array_pop($exprs);
                $op = array_pop($ops);
                $exprs[] = [
                    'type' => ExpressionType::BINARY_EXP,
                    'operator' => $op['value'],
                    'left' => $left,
                    'right' => $right,
                ];
            }

            // gobble the next token in the tree
            $node = $this->gobbleToken();
            if ($node === null) {
                $this->throw_error('Expected expression after ' . json_encode($value));
            }
            $exprs[] = $node;

            // and store the info about the operator
            $ops[] = ['value' => $value, 'precedence' => $precedence];
        }

        $i = count($exprs) - 1;
        $j = count($ops) - 1;
        $node = $exprs[$i];
        while ($i > 0 && $j >= 0) {
            $node = [
                'type' => ExpressionType::BINARY_EXP,
                'operator' => $ops[$j]['value'],
                'left' => $exprs[$i - 1],
                'right' => $node,
            ];
            $j--;
            $i--;
        }

        return $node;
    }

    /**
     * An individual part of a binary expression:
     * e.g. `foo.bar(baz)`, `1`, `'abc'`, `(a % 2)` (because it's in parenthesis)
     *
     * @return array|null
     */
    public function gobbleToken(): array|null
    {
        $ch = $this->skipSpaces();

        // numeric literals
        if ($this->config['Features']['Literals']['Numeric'] && (self::isDecimalDigit($ch) || $ch === self::CHAR_PERIOD)) {
            return $this->gobbleNumericLiteral();
        }
        
        // single or double quoted strings
        if ($this->config['Features']['Literals']['String'] && ($ch === self::CHAR_SINGLE_QUOTE || $ch === self::CHAR_DOUBLE_QUOTE)) {
            return $this->gobbleStringLiteral();
        }
        
        // array literal
        if ($this->config['Features']['Literals']['Array'] && $ch === self::CHAR_OPEN_BRACKET) {
            return $this->gobbleArray();
        }

        $to_check = mb_substr($this->expr, $this->index, $this->unaryOperatorLength, 'UTF-8');
        $tc_len = mb_strlen($to_check, 'UTF-8');
        while ($tc_len > 0) {
            if (in_array($to_check, $this->config['Operators']['Unary'])) {
                $this->index += $tc_len;
                $argument = $this->gobbleToken();
                if ($argument === null) {
                    $this->throw_error('Expected argument for unary expression');
                }

                return [
                    'type' => ExpressionType::UNARY_EXP,
                    'operator' => $to_check,
                    'argument' => $argument,
                ];
            }

            $tc_len--;
            $to_check = mb_substr($to_check, 0, $tc_len, 'UTF-8');
        }

        if (self::isIdentifierStart($ch) || $ch === self::CHAR_OPEN_PARENTHESES) {
            return $this->gobbleVariable();
        }

        return null;
    }

    /**
     * Gobbles a contiguous sequence of decimal numbers, possibly separated with numeric separators.
     * The returned string does not include numeric separators
     *
     * @return string
     */
    private function gobbleDecimal(): string
    {
        // Fast path: No separator enabled case: no numeric separator
        $separator = $this->config['Features']['Literals']['NumericSeparator'];
        if ($separator === '') {
            $start = $this->index;
            $count = 0;
            while (self::isDecimalDigit($this->char())) {
                $this->index++;
                $count++;
            }
            return mb_substr($this->expr, $start, $count, 'UTF-8');
        }

        // slow path: need to check for separator
        $number = '';
        while (True) {
            $ch = $this->char();
            if ($this->isDecimalDigit($ch)) {
                $number .= $ch;
            } else if ($ch !== $separator) {
                break;
            }
            $this->index++;
        }

        return $number;
    }

    /**
     * Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
     * keep track of everything in the numeric literal and then calling `parseFloat` on that string
     *
     * @return array
     */
    private function gobbleNumericLiteral(): array
    {
        $start = $this->index;

        // gobble the number itself
        $number = $this->gobbleDecimal();

        $ch = $this->char();
        if ($ch === self::CHAR_PERIOD) {
            // can start with a decimal marker
            $number .= '.';
            $this->index++;

            $number .= $this->gobbleDecimal();
        }

        $ch = $this->char();
        if ($ch === 'e' || $ch === 'E') { // exponent marker
            $number .= $ch;
            $this->index++;

            $ch = $this->char();
            if ($ch === '+' || $ch === '-') {
                // exponent sign
                $number .= $ch;
                $this->index++;
            }

            // exponent itself
            $exponent = $this->gobbleDecimal();
            if ($exponent === '') {
                $this->throw_error('Expected exponent after ' . json_encode($number . $this->char()));
            }

            $number .= $exponent;
        }

        $ch = $this->char();
        // Check to make sure this isn't a variable name that start with a number (123abc)
        if (self::isIdentifierStart($ch)) {
            $this->throw_error('Variable names cannot start with a number like ' . json_encode($number . $ch));
        }

        // parse the float value and get the literal (if needed)
        $value = (float)($number);
        if ($this->config['Features']['Literals']['NumericSeparator'] !== '') {
            $number = mb_substr($this->expr, $start, $this->index - $start, 'UTF-8');
        }

        return [
            'type' => ExpressionType::LITERAL,
            'kind' => 'number',
            'value' => $value,
            'raw' => $number,
        ];
    }

    /**
     * Parses a string literal, staring with single or double quotes with basic support for escape codes.
     * 
     * e.g. `'hello world'`, `'this is\nJSEP'`
     *
     * @return array
     */
    private function gobbleStringLiteral(): array
    {
        $s = '';

        $start = $this->index;

        $quote = $this->char();
        $this->index++;

        $closed = FALSE;

        while ($this->index < $this->length) {
            $ch = $this->char();
            $this->index++;

            if ($ch === $quote) {
                $closed = TRUE;
                break;
            }

            if ($ch === '\\') {
                // Check for all of the common escape codes
                $ch = $this->char();
                $this->index++;

                if ($ch === 'n') {
                    $s .= "\n";
                } else if ($ch === 'r') {
                    $s .= "\r";
                } else if ($ch === 't') {
                    $s .= "\t";
                } else if ($ch === 'b') {
                    $s .= "\b";
                } else if ($ch === 'f') {
                    $s .= "\f";
                } else if ($ch === 'v') {
                    $s .= "\x0B";
                } else if ($ch === '\\') {
                    $s .= "\\";
                }
                // default: just add the character literally.
                else {
                    $s .= $ch;
                }
            } else {
                $s .= $ch;
            }
        }

        if (!$closed) {
            $this->throw_error('Unclosed quote after ' . json_encode($s));
        }

        return [
            'type' => ExpressionType::LITERAL,
            'kind' => 'string',
            'value' => $s,
            'raw' => mb_substr($this->expr, $start, $this->index - $start, 'UTF-8'),
        ];
    }

    /**
     * Gobbles only identifiers
     * e.g.: `foo`, `_value`, `$x1`
     * Also, this function checks if that identifier is a literal:
     * (e.g. `true`, `false`, `null`)
     *
     * @return array
     */
    private function gobbleIdentifier(): array
    {
        // can't gobble an identifier if the first character isn't the start of one.
        $ch = $this->char();
        if ($ch === '') {
            $this->throw_error('Expected literal');
        }

        if (!self::isIdentifierStart($ch)) {
            $this->throw_error('Unexpected ' . json_encode($ch));
        }

        // record where the identifier starts
        $start = $this->index;
        $this->index++;

        // continue scanning the literal
        while ($this->index < $this->length) {
            $ch = $this->char();
            if (!self::isIdentifierPart($ch)) {
                break;
            }
            $this->index++;
        }

        // if the identifier is a known literal, return it!
        $identifier = mb_substr($this->expr, $start, $this->index - $start, 'UTF-8');
        if (array_key_exists($identifier, $this->config['Operators']['Literals'])) {
            return [
                'type' => ExpressionType::LITERAL,
                'value' => $this->config['Operators']['Literals'][$identifier],
                'raw' => $identifier,
            ];
        }

        // if identifiers are disabled, we can bail out
        if (!$this->config["Features"]["Identifiers"]) {
            $this->throw_error('Unknown literal ' . json_encode($identifier));
        }

        // found the identifier
        return [
            'type' => ExpressionType::IDENTIFIER,
            'name' => $identifier,
        ];
    }

    /**
     * Gobbles a list of arguments within the context of a function call
     * or array literal. This function also assumes that the opening character
     * `(` or `[` has already been gobbled, and gobbles expressions and commas
     * until the terminator character `)` or `]` is encountered.
     * e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
     *
     * @param integer $termination
     * @return array
     */
    private function gobbleArguments(string $start, string $end): array
    {
        $args = [];

        $closed = FALSE; // is the expression closed?
        $hadComma = FALSE; // did we have a comma in the last iteration?

        while ($this->index < $this->length) {
            $ch = $this->skipSpaces();

            if ($ch === $end) {
                $closed = TRUE;
                $this->index++;
                break;
            }

            // between expressions
            if ($ch === self::CHAR_COMMA) {
                if ($hadComma) {
                    $this->throw_error('Duplicate ' . json_encode(self::CHAR_COMMA));
                }
                $hadComma = TRUE;
                $this->index++;
                continue;
            }

            // check that there was a comma (if we expected one)
            $wantsComma = count($args) > 0;
            if ($wantsComma !== $hadComma) {
                if ($wantsComma) {
                    $this->throw_error('Expected ' . json_encode(self::CHAR_COMMA));
                } else {
                    $this->throw_error('Unexpected ' . json_encode(self::CHAR_COMMA));
                }
            }

            $node = $this->gobbleExpression();
            if (($node === null) || ($node['type'] === ExpressionType::COMPOUND)) {
                $this->throw_error('Expected ' . json_encode(self::CHAR_COMMA));
            }

            $args[] = $node;
            $hadComma = FALSE;
        }

        if (!$closed) {
            $this->throw_error('Unclosed ' . json_encode($start));
        }

        return $args;
    }

    /**
     * Gobble a non-literal variable name. This variable name may include properties
     * e.g. `foo`, `bar.baz`, `foo['bar'].baz`
     * It also gobbles function calls:
     * e.g. `Math.acos(obj.angle)`
     *
     * @return array|null
     */
    private function gobbleVariable(): array|null
    {
        // parse a group or identifier first
        $ch = $this->char();
        if ($ch === self::CHAR_OPEN_PARENTHESES) {
            $node = $this->gobbleGroup();
        } else {
            $node = $this->gobbleIdentifier();
        }
        if ($node === NULL) {
            return null;
        }

        // then iterate over operations applied to it
        while (true) {
            $ch = $this->skipSpaces();

            $this->index++;

            // access via .
            if ($this->config['Features']['Members']['Static'] && $ch === self::CHAR_PERIOD) {
                $this->skipSpaces();

                $node = [
                    'type' => ExpressionType::MEMBER_EXP,
                    'computed' => False,
                    'object' => $node,
                    'property' => $this->gobbleIdentifier(),
                ];

                continue;
            } 
            
            // access via []s
            if ($this->config['Features']['Members']['Computed'] && $ch === self::CHAR_OPEN_BRACKET) {
                $prop = $this->gobbleExpression();
                if ($prop === null) {
                    $this->throw_error('Expected expression');
                }

                $node = [
                    'type' => ExpressionType::MEMBER_EXP,
                    'computed' => True,
                    'object' => $node,
                    'property' => $prop,
                ];

                $ch = $this->skipSpaces();
                if ($ch !== self::CHAR_CLOSE_BRACKET) {
                    $this->throw_error('Unclosed ' . json_encode(self::CHAR_OPEN_BRACKET));
                }

                $this->index++;

                continue;
            }
            
            // call via ()s
            if ($this->config['Features']['Calls'] && $ch === self::CHAR_OPEN_PARENTHESES) {
                $node = [
                    'type' => ExpressionType::CALL_EXP,
                    'arguments' => $this->gobbleArguments(self::CHAR_OPEN_PARENTHESES, self::CHAR_CLOSE_PARENTHESES),
                    'callee' => $node,
                ];
                continue;
            }
            
            // Done
            $this->index--;
            break;
        }

        return $node;
    }

    /**
     * Responsible for parsing a group of things within parentheses `()`
     * This function assumes that it needs to gobble the opening parenthesis
     * and then tries to gobble everything within that parenthesis, assuming
     * that the next thing it should see is the close parenthesis. If not,
     * then the expression probably doesn't have a `)`
     *
     * @return array|null
     */
    private function gobbleGroup(): array|null
    {
        $this->index++;
        $expr = $this->gobbleExpression();

        $ch = $this->skipSpaces();
        if ($ch !== self::CHAR_CLOSE_PARENTHESES) {
            $this->throw_error('Unclosed ' . json_encode(self::CHAR_OPEN_PARENTHESES));
        }

        $this->index++;
        return $expr;
    }


    /**
     * Responsible for parsing Array literals `[1, 2, 3]`
     * This function assumes that it needs to gobble the opening bracket
     * and then tries to gobble the expressions as arguments.
     *
     * @return array
     */
    private function gobbleArray(): array
    {
        $this->index++;

        return [
            'type' => ExpressionType::ARRAY_EXP,
            'elements' => $this->gobbleArguments(self::CHAR_OPEN_BRACKET, self::CHAR_CLOSE_BRACKET),
        ];
    }


    /**
     * Gets the default configuration.
     *
     * @return array
     */
    public static function GetDefaultConfig(): array
    {
        return [
            'Operators' => [
                'Literals' => [
                    'true' => True,
                    'false' => False,
                    'null' => null,
                ],
                'Unary' => ['-', '!', '~', '+'],
                'Binary' => [
                    '||' => 1,
                    '&&' => 2,
                    '|' => 3,
                    '^' => 4,
                    '&' => 5,
                    '==' => 6,
                    '!=' => 6,
                    '===' => 6,
                    '!==' => 6,
                    '<' => 7,
                    '>' => 7,
                    '<=' => 7,
                    '>=' => 7,
                    '<<' => 8,
                    '>>' => 8,
                    '>>>' => 8,
                    '+' => 9,
                    '-' => 9,
                    '*' => 10,
                    '/' => 10,
                    '%' => 10,
                ],
            ],
            'Features' => [
                'Compound' => True,
                'Conditional' => True,
                'Identifiers' => True,
                'Calls' => True,
                'Members' => [
                    'Static' => True,
                    'Computed' => True,
                ],
                'Literals' => [
                    'Numeric' => True,
                    'NumericSeparator' => '',
                    'String' => True,
                    'Array' => True,
                ],
            ],
        ];
    }
}

// cSpell:words JSEP Oney
