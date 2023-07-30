<?php

declare(strict_types=1);

/**
 * (c) Tom Wiesing 2016-23, licensed under MIT license
 * This code is inspired by the JavaScript version JSEP
 * The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and
 * licensed under MIT.
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

abstract class Expression implements JsonSerializable
{
    public readonly ExpressionType $type;

    public function __construct(ExpressionType $type)
    {
        $this->type = $type;
    }

    public function jsonSerialize(): mixed
    {
        // get the properties of this object
        $reflect = new ReflectionClass($this);
        $props = $reflect->getProperties(ReflectionProperty::IS_PUBLIC | ReflectionProperty::IS_READONLY);

        $result = [];
        foreach ($props as $prop) {
            if (!$prop->isReadOnly() || !$prop->isPublic()) {
                continue;
            }
            $name = $prop->getName();
            // @phpstan-ignore-next-line variable.dynamicName
            $result[$name] = $this->$name;
        }

        return $result;
    }
}

class Compound extends Expression
{
    /** @var array<Expression> */
    public readonly array $body;

    /**
     * @param array<Expression> $body
     */
    public function __construct(array $body)
    {
        parent::__construct(ExpressionType::COMPOUND);
        $this->body = $body;
    }
}

class Identifier extends Expression
{
    public readonly string $name;

    public function __construct(string $name)
    {
        parent::__construct(ExpressionType::IDENTIFIER);
        $this->name = $name;
    }
}

class Member extends Expression
{
    public readonly bool $computed;
    public readonly Expression $object;
    public readonly Expression $property;

    public function __construct(Expression $object, Expression $property, bool $computed)
    {
        parent::__construct(ExpressionType::MEMBER_EXP);
        $this->object = $object;
        $this->property = $property;
        $this->computed = $computed;
    }
}

class Literal extends Expression
{
    public readonly mixed $value;
    public readonly string $raw;

    public function __construct(mixed $value, string $raw)
    {
        parent::__construct(ExpressionType::LITERAL);
        $this->value = $value;
        $this->raw = $raw;
    }
}

enum LiteralKind: string
{
    case String = 'string';
    case Number = 'number';
}

class StringLiteral extends Expression
{
    public readonly LiteralKind $kind;
    public readonly string $value;
    public readonly string $raw;

    public function __construct(string $value, string $raw)
    {
        parent::__construct(ExpressionType::LITERAL);
        $this->kind = LiteralKind::String;
        $this->value = $value;
        $this->raw = $raw;
    }
}

class NumericLiteral extends Expression
{
    public readonly LiteralKind $kind;
    public readonly float $value;
    public readonly string $raw;

    public function __construct(float $value, string $raw)
    {
        parent::__construct(ExpressionType::LITERAL);
        $this->kind = LiteralKind::Number;
        $this->value = $value;
        $this->raw = $raw;
    }
}

class Call extends Expression
{
    /** @var array<Expression> */
    public readonly array $arguments;
    public readonly Expression $callee;

    /**
     * @param array<Expression> $arguments
     */
    public function __construct(Expression $callee, array $arguments)
    {
        parent::__construct(ExpressionType::CALL_EXP);
        $this->callee = $callee;
        $this->arguments = $arguments;
    }
}

class Unary extends Expression
{
    public readonly string $operator;
    public readonly Expression $argument;

    public function __construct(string $operator, Expression $argument)
    {
        parent::__construct(ExpressionType::UNARY_EXP);
        $this->operator = $operator;
        $this->argument = $argument;
    }
}

class Binary extends Expression
{
    public readonly string $operator;
    public readonly Expression $left;
    public readonly Expression $right;

    public function __construct(string $operator, Expression $left, Expression $right)
    {
        parent::__construct(ExpressionType::BINARY_EXP);
        $this->operator = $operator;
        $this->left = $left;
        $this->right = $right;
    }
}

class Condition extends Expression
{
    public readonly Expression $test;
    public readonly Expression $consequent;
    public readonly Expression $alternate;

    public function __construct(Expression $test, Expression $consequent, Expression $alternate)
    {
        parent::__construct(ExpressionType::CONDITIONAL_EXP);
        $this->test = $test;
        $this->consequent = $consequent;
        $this->alternate = $alternate;
    }
}

class Ary extends Expression
{
    /** @var array<Expression> */
    public readonly array $elements;

    /**
     * @param array<Expression> $elements
     */
    public function __construct(array $elements)
    {
        parent::__construct(ExpressionType::ARRAY_EXP);
        $this->elements = $elements;
    }
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
     * @param string $expr  Expression that was originally parsed
     * @param int    $index Index of position in the expression where the error occurred
     */
    public function __construct(string $error, string $expr, int $index)
    {
        $this->error = $error;
        $this->expr = $expr;
        $this->index = $index;

        parent::__construct('Index '.(string) $index.' of '.json_encode($expr).': '.$error, 0, null);
    }
}

/**
 * Represents a single instance of the PreJsPy parser.
 *
 * @phpstan-type Config array{"Operators":array{"Literals":array<string,mixed>,"Unary":array<string>,"Binary":array<string,int>},"Features":array{"Compound":bool,"Conditional":bool,"Identifiers":bool,"Calls":bool,"Members":array{"Static":bool,"Computed":bool},"Literals":array{"Numeric":bool,"NumericSeparator":string,"String":bool,"Array":bool}}}
 * @phpstan-type PartialConfig array{"Operators"?:array{"Literals"?:array<string,mixed>,"Unary"?:array<string>,"Binary"?:array<string,int>},"Features"?:array{"Compound"?:bool,"Conditional"?:bool,"Identifiers"?:bool,"Calls"?:bool,"Members"?:array{"Static"?:bool,"Computed"?:bool},"Literals"?:array{"Numeric"?:bool,"NumericSeparator"?:string,"String"?:bool,"Array"?:bool}}}
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
     * Creates a parser error with a given message and a given index.
     */
    private function error(string $message): ParsingError
    {
        return new ParsingError($message, implode('', $this->expr), $this->index);
    }

    // =======================
    // STATIC HELPER FUNCTIONS
    // =======================

    /**
     * Checks if a character is a decimal digit.
     *
     * @param string $ch character to check
     */
    private static function isDecimalDigit(string $ch): bool
    {
        return $ch >= '0' && $ch <= '9';
    }

    /**
     * Checks if a character is the start of an identifier.
     *
     * @param string $ch character to check
     */
    private static function isIdentifierStart(string $ch): bool
    {
        return
            ('$' === $ch)
            || ('_' === $ch)
            || ($ch >= 'a' && $ch <= 'z')
            || ($ch >= 'A' && $ch <= 'Z')
            || (ord($ch) >= 128) // non-ascii
        ;
    }

    /**
     * Checks if a character is part of an identifier.
     *
     * @param string $ch character to check
     */
    private static function isIdentifierPart(string $ch): bool
    {
        return
            ('$' === $ch)
            || ('_' === $ch)
            || ($ch >= 'a' && $ch <= 'z')
            || ($ch >= 'A' && $ch <= 'Z')
            || ($ch >= '0' && $ch <= '9')
            || (ord($ch) >= 128) // non-ascii
        ;
    }

    #region "Config"

    /** @var Config */
    private array $config;
    private int $unaryOperatorLength;
    private int $binaryOperatorLength;

    /**
     * Creates a new PreJsPy instance.
     */
    public function __construct()
    {
        $this->config = self::GetDefaultConfig();
        $this->SetConfig($this->config);
    }

    /**
     * Sets the config used by this parser.
     *
     * @param PartialConfig|null $config (Possibly partial) configuration to use
     *
     * @return Config
     */
    public function SetConfig(array|null $config): array
    {
        if (null !== $config) {
            self::assign($this->config, $config, 'Operators', 'Literals');
            self::assign($this->config, $config, 'Operators', 'Unary');
            self::assign($this->config, $config, 'Operators', 'Binary');
            self::assign($this->config, $config, 'Features', 'Compound');
            self::assign($this->config, $config, 'Features', 'Conditional');
            self::assign($this->config, $config, 'Features', 'Identifiers');
            self::assign($this->config, $config, 'Features', 'Calls');
            self::assign($this->config, $config, 'Features', 'Members', 'Computed');
            self::assign($this->config, $config, 'Features', 'Members', 'Static');
            self::assign($this->config, $config, 'Features', 'Literals', 'Array');
            self::assign($this->config, $config, 'Features', 'Literals', 'Numeric');
            self::assign($this->config, $config, 'Features', 'Literals', 'NumericSeparator');
            self::assign($this->config, $config, 'Features', 'Literals', 'String');

            $this->unaryOperatorLength = self::maxArrayValueLen($this->config['Operators']['Unary']);
            $this->binaryOperatorLength = self::maxObjectKeyLen($this->config['Operators']['Binary']);
        }

        return $this->GetConfig();
    }

    /**
     * Gets the current config used by this parser.
     *
     * @return Config
     */
    public function GetConfig(): array
    {
        return self::clone($this->config);
    }

    /**
     * Assigns a specific nested property from source to dest.
     * The value is cloned.
     *
     * This is roughly equivalent to
     *
     * $dest[$path[0]]...[$path[n]] = self::clone($source[$path[0]]...[$path[n]])
     *
     * with appropriate existence checks.
     *
     * @param array<mixed> $dest   dest the destination element to assign into
     * @param array<mixed> $source source the source object to assign from
     * @param string       $path   path the names of properties to navigate through
     */
    private function assign(array &$dest, array &$source, string ...$path): void
    {
        // skip if we have no elements
        if (0 === count($path)) {
            return;
        }

        // find the source and dest properties
        $destProp = &$dest;
        $sourceProp = &$source;

        // iterate through to the penultimate element
        foreach (array_slice($path, 0, -1) as $element) {
            if (!is_array($destProp) || !array_key_exists($element, $destProp)) {
                return;
            }
            if (!is_array($sourceProp) || !array_key_exists($element, $sourceProp)) {
                return;
            }
            $destProp = &$destProp[$element];
            $sourceProp = &$sourceProp[$element];
        }

        // check the last element
        $element = end($path);
        if (!is_array($destProp) || !array_key_exists($element, $destProp)) {
            return;
        }
        if (!is_array($sourceProp) || !array_key_exists($element, $sourceProp)) {
            return;
        }

        // and assign the clone
        $destProp[$element] = self::clone($sourceProp[$element]);
    }

    /**
     * Clone makes a deep clone of an array-like object.
     * Unlike the clone builtin, it recurses into array values.
     * Non-arrays are not cloned, and returned as-is.
     *
     * @template T array
     *
     * @param T $obj Object to clone
     *
     * @return T
     */
    private function clone(mixed $obj): mixed
    {
        if (is_array($obj)) {
            /** @var T */
            $clone = array_map(fn ($x) => $this->clone($x), $obj);

            return $clone;
        }

        return $obj;
    }

    /**
     * Gets the longest key length of an object.
     *
     * @param array<string,mixed> $o object to iterate over
     */
    private static function maxObjectKeyLen(array $o): int
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
     * Gets the maximum length of the member of an array.
     *
     * @param array<string> $ary array to iterate over
     */
    private static function maxArrayValueLen(array $ary): int
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

    #endregion

    #region "State"

    private int $index = 0;
    private int $length = 0;
    /** @var string[] */
    private array $expr = [];

    /**
     * Resets internal state to be able to parse expression.
     *
     * @return void
     */
    private function reset(string $expr)
    {
        $this->index = 0;
        $this->expr = mb_str_split($expr, 1, 'UTF-8');
        $this->length = count($this->expr);
    }

    /**
     * Returns the current character or "" if the end of the string was reached.
     */
    private function char(): string
    {
        return $this->expr[$this->index] ?? '';
    }

    /**
     * Returns $count characters of the input string, starting at the current character.
     */
    private function chars(int $count): string
    {
        return implode('', array_slice($this->expr, $this->index, $count));
    }

    /**
     * Returns the string of characters starting at $start up to (but not including) the current character.
     */
    private function charsFrom(int $start): string
    {
        return implode('', array_slice($this->expr, $start, $this->index - $start));
    }

    #endregion

    /**
     * Parses an expression into a parse tree.
     * If an error occurs, raises a ParsingError.
     *
     * @param string $expr Expression to parse
     */
    public function Parse(string $expr): Expression
    {
        $result = $this->gobble($expr);
        if ($result instanceof ParsingError) {
            throw $result;
        }

        return $result;
    }

    /**
     * Parses an expression into a parse tree.
     * If successfull, returns [$result, null].
     * If an error occurs, returns [null, $error].
     *
     * @param string $expr Expression to parse
     *
     * @return array{0:Expression,1:null}|array{0:null,1:ParsingError}
     */
    public function TryParse(string $expr): array
    {
        $result = $this->gobble($expr);
        if ($result instanceof ParsingError) {
            return [null, $result];
        }

        return [$result, null];
    }

    /**
     * Gobbles the given source string.
     */
    private function gobble(string $expr): Expression|ParsingError
    {
        $this->reset($expr); // setup the state properly
        $result = $this->gobbleCompound();
        $this->reset(''); // don't keep the last parsed expression in memory

        return $result;
    }

    public function gobbleCompound(): Expression|ParsingError
    {
        /** @var array<Expression> */
        $nodes = [];

        while ($this->index < $this->length) {
            $ch = $this->char();

            // Expressions can be separated by semicolons, commas, or just inferred without any separators
            if (self::CHAR_SEMICOLON === $ch || self::CHAR_COMMA === $ch) {
                continue;
            }

            // Try to gobble each expression individually
            $node = $this->gobbleExpression();
            if ($node instanceof ParsingError) {
                return $node;
            }
            if (null === $node) {
                break;
            }

            $nodes[] = $node;
        }

        // didn't find an expression => something went wrong
        if ($this->index < $this->length) {
            return $this->error('Unexpected '.json_encode($this->char()));
        }

        // If there is only one expression, return it as is
        if (1 === count($nodes)) {
            return $nodes[0];
        }

        // do not allow compound expressions if they are not enabled
        if (!$this->config['Features']['Compound']) {
            return $this->error('Unexpected compound expression');
        }

        return new Compound($nodes);
    }

    /**
     * Advances the index to the next non-space character.
     *
     * @return string the next non-space character
     */
    private function skipSpaces(): string
    {
        while (true) {
            $ch = $this->char();
            if (!(self::CHAR_SPACE === $ch || self::CHAR_TAB === $ch)) {
                return $ch;
            }
            ++$this->index;
        }
    }

    /**
     * Main parsing function to parse any kind of expression.
     */
    private function gobbleExpression(): Expression|ParsingError|null
    {
        // gobble a binary expression
        $test = $this->gobbleBinaryExpression();

        // only continue if there is a chance of finding a conditional
        if ((!$this->config['Features']['Conditional']) || null === $test || $test instanceof ParsingError) {
            return $test;
        }

        // not a conditional expression => return immediately
        $ch = $this->skipSpaces();
        if (self::CHAR_QUESTIONMARK !== $ch) {
            return $test;
        }

        // conditional expression: test ? consequent : alternate
        ++$this->index;

        $consequent = $this->gobbleExpression();
        if ($consequent instanceof ParsingError) {
            return $consequent;
        }
        if (null === $consequent) {
            return $this->error('Expected expression');
        }

        // need a ':' for the second part of the alternate
        $ch = $this->skipSpaces();
        if (self::CHAR_COLON !== $ch) {
            return $this->error('Expected '.json_encode(self::CHAR_COLON));
        }

        ++$this->index;

        $alternate = $this->gobbleExpression();
        if ($alternate instanceof ParsingError) {
            return $alternate;
        }
        if (null === $alternate) {
            return $this->error('Expected expression');
        }

        return new Condition($test, $consequent, $alternate);
    }

    /**
     * Search for the operation portion of the string (e.g. `+`, `===`)
     * Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
     * and move down from 3 to 2 to 1 character until a matching binary operation is found
     * then, return that binary operation.
     */
    private function gobbleBinaryOp(): string|null
    {
        $this->skipSpaces();

        $tc_len = $this->binaryOperatorLength;
        while ($tc_len > 0) {
            $to_check = $this->chars($tc_len);
            if (array_key_exists($to_check, $this->config['Operators']['Binary'])) {
                $this->index += $tc_len;

                return $to_check;
            }
            --$tc_len;
        }

        return null;
    }

    /**
     * This function is responsible for gobbling an individual expression,
     * e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`.
     */
    public function gobbleBinaryExpression(): Expression|ParsingError|null
    {
        // Get the leftmost token of a binary expression or bail out
        $left = $this->gobbleToken();
        if ($left instanceof ParsingError) {
            return $left;
        }
        if (null === $left) {
            return null;
        }

        $exprs = [$left]; // a list of expressions
        $ops = []; // and a list of binary operators between them

        // Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
        while (true) {
            $value = $this->gobbleBinaryOp();
            if (null === $value) {
                break;
            }

            $precedence = $this->config['Operators']['Binary'][$value];
            if (0 === $precedence) {
                break;
            }

            // Reduce: make a binary expression from the three topmost entries.
            while ((count($ops) > 0) && $precedence < end($ops)['precedence']) {
                // the code maintains invariance count(ops) === count(exprs) + 1
                // so the array_pop()s are safe because count(ops.length) >= 1 and count(exprs) >= 2
                $right = array_pop($exprs);
                $left = array_pop($exprs);
                $op = array_pop($ops);

                if (null === $left) {
                    // precondition guarantees that this will never happen
                    throw new Error('never reached');
                }

                $exprs[] = new Binary($op['value'], $left, $right);
            }

            // gobble the next token in the tree
            $node = $this->gobbleToken();
            if ($node instanceof ParsingError) {
                return $node;
            }
            if (null === $node) {
                return $this->error('Expected expression after '.json_encode($value));
            }
            $exprs[] = $node;

            // and store the info about the operator
            $ops[] = ['value' => $value, 'precedence' => $precedence];
        }

        $i = count($exprs) - 1;
        $j = count($ops) - 1;
        $node = $exprs[$i];
        while ($i > 0 && $j >= 0) {
            $node = new Binary($ops[$j]['value'], $exprs[$i - 1], $node);
            --$j;
            --$i;
        }

        return $node;
    }

    /**
     * An individual part of a binary expression:
     * e.g. `foo.bar(baz)`, `1`, `'abc'`, `(a % 2)` (because it's in parenthesis).
     */
    public function gobbleToken(): Expression|ParsingError|null
    {
        $ch = $this->skipSpaces();

        // numeric literals
        if ($this->config['Features']['Literals']['Numeric'] && (self::isDecimalDigit($ch) || self::CHAR_PERIOD === $ch)) {
            return $this->gobbleNumericLiteral();
        }

        // single or double quoted strings
        if ($this->config['Features']['Literals']['String'] && (self::CHAR_SINGLE_QUOTE === $ch || self::CHAR_DOUBLE_QUOTE === $ch)) {
            return $this->gobbleStringLiteral($ch);
        }

        // array literal
        if ($this->config['Features']['Literals']['Array'] && self::CHAR_OPEN_BRACKET === $ch) {
            return $this->gobbleArray();
        }

        $tc_len = $this->unaryOperatorLength;
        while ($tc_len > 0) {
            $to_check = $this->chars($tc_len);
            if (in_array($to_check, $this->config['Operators']['Unary'], true)) {
                $this->index += $tc_len;

                $argument = $this->gobbleToken();
                if ($argument instanceof ParsingError) {
                    return $argument;
                }

                if (null === $argument) {
                    return $this->error('Expected argument for unary expression');
                }

                return new Unary($to_check, $argument);
            }

            --$tc_len;
        }

        if (self::isIdentifierStart($ch) || self::CHAR_OPEN_PARENTHESES === $ch) {
            return $this->gobbleVariable($ch);
        }

        return null;
    }

    /**
     * Gobbles a contiguous sequence of decimal numbers, possibly separated with numeric separators.
     * The returned string does not include numeric separators.
     */
    private function gobbleDecimal(): string
    {
        // Fast path: No separator enabled case: no numeric separator
        $separator = $this->config['Features']['Literals']['NumericSeparator'];
        if ('' === $separator) {
            $start = $this->index;
            while (self::isDecimalDigit($this->char())) {
                ++$this->index;
            }

            return $this->charsFrom($start);
        }

        // slow path: need to check for separator
        $number = '';
        while (true) {
            $ch = $this->char();
            if (self::isDecimalDigit($ch)) {
                $number .= $ch;
            } elseif ($ch !== $separator) {
                break;
            }
            ++$this->index;
        }

        return $number;
    }

    /**
     * Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
     * keep track of everything in the numeric literal and then calling `parseFloat` on that string.
     */
    private function gobbleNumericLiteral(): NumericLiteral|ParsingError
    {
        $start = $this->index;

        // gobble the number itself
        $number = $this->gobbleDecimal();

        $ch = $this->char();
        if (self::CHAR_PERIOD === $ch) {
            // can start with a decimal marker
            $number .= '.';
            ++$this->index;

            $number .= $this->gobbleDecimal();
        }

        $ch = $this->char();
        if ('e' === $ch || 'E' === $ch) { // exponent marker
            $number .= $ch;
            ++$this->index;

            $ch = $this->char();
            if ('+' === $ch || '-' === $ch) {
                // exponent sign
                $number .= $ch;
                ++$this->index;
            }

            // exponent itself
            $exponent = $this->gobbleDecimal();
            if ('' === $exponent) {
                return $this->error('Expected exponent after '.json_encode($number.$this->char()));
            }

            $number .= $exponent;
        }

        $ch = $this->char();
        // Check to make sure this isn't a variable name that start with a number (123abc)
        if (self::isIdentifierStart($ch)) {
            return $this->error('Variable names cannot start with a number like '.json_encode($number.$ch));
        }

        // parse the float value and get the literal (if needed)
        $value = (float) $number;
        if ('' !== $this->config['Features']['Literals']['NumericSeparator']) {
            $number = $this->charsFrom($start);
        }

        return new NumericLiteral($value, $number);
    }

    /**
     * Parses a string literal, staring with single or double quotes with basic support for escape codes.
     *
     * e.g. `'hello world'`, `'this is\nJSEP'`
     *
     * @param string $quote the quote character
     */
    private function gobbleStringLiteral(string $quote): StringLiteral|ParsingError
    {
        $s = '';

        $start = $this->index;
        ++$this->index;

        $closed = false;

        while ($this->index < $this->length) {
            $ch = $this->char();
            ++$this->index;

            if ($ch === $quote) {
                $closed = true;
                break;
            }

            if ('\\' === $ch) {
                // Check for all of the common escape codes
                $ch = $this->char();
                ++$this->index;

                if ('n' === $ch) {
                    $s .= "\n";
                } elseif ('r' === $ch) {
                    $s .= "\r";
                } elseif ('t' === $ch) {
                    $s .= "\t";
                } elseif ('b' === $ch) {
                    $s .= "\b";
                } elseif ('f' === $ch) {
                    $s .= "\f";
                } elseif ('v' === $ch) {
                    $s .= "\x0B";
                } elseif ('\\' === $ch) {
                    $s .= '\\';
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
            return $this->error('Unclosed quote after '.json_encode($s));
        }

        return new StringLiteral($s, $this->charsFrom($start));
    }

    /**
     * Gobbles only identifiers
     * e.g.: `foo`, `_value`, `$x1`
     * Also, this function checks if that identifier is a literal:
     * (e.g. `true`, `false`, `null`).
     */
    private function gobbleIdentifier(string $ch): Identifier|Literal|ParsingError
    {
        // can't gobble an identifier if the first character isn't the start of one.
        if ('' === $ch) {
            return $this->error('Expected literal');
        }

        if (!self::isIdentifierStart($ch)) {
            return $this->error('Unexpected '.json_encode($ch));
        }

        // record where the identifier starts
        $start = $this->index;
        ++$this->index;

        // continue scanning the literal
        while ($this->index < $this->length) {
            $ch = $this->char();
            if (!self::isIdentifierPart($ch)) {
                break;
            }
            ++$this->index;
        }

        // if the identifier is a known literal, return it!
        $identifier = $this->charsFrom($start);
        if (array_key_exists($identifier, $this->config['Operators']['Literals'])) {
            return new Literal($this->config['Operators']['Literals'][$identifier], $identifier);
        }

        // if identifiers are disabled, we can bail out
        if (!$this->config['Features']['Identifiers']) {
            return $this->error('Unknown literal '.json_encode($identifier));
        }

        // found the identifier
        return new Identifier($identifier);
    }

    /**
     * Gobbles a list of arguments within the context of a function call
     * or array literal. This function also assumes that the opening character
     * `(` or `[` has already been gobbled, and gobbles expressions and commas
     * until the terminator character `)` or `]` is encountered.
     * e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`.
     *
     * @return array<Expression>
     */
    private function gobbleArguments(string $start, string $end): array|ParsingError
    {
        /** @var array<Expression> */
        $args = [];

        $closed = false; // is the expression closed?
        $hadComma = false; // did we have a comma in the last iteration?

        while ($this->index < $this->length) {
            $ch = $this->skipSpaces();

            if ($ch === $end) {
                $closed = true;
                ++$this->index;
                break;
            }

            // between expressions
            if (self::CHAR_COMMA === $ch) {
                if ($hadComma) {
                    return $this->error('Duplicate '.json_encode(self::CHAR_COMMA));
                }
                $hadComma = true;
                ++$this->index;
                continue;
            }

            // check that there was a comma (if we expected one)
            $wantsComma = count($args) > 0;
            if ($wantsComma !== $hadComma) {
                if ($wantsComma) {
                    return $this->error('Expected '.json_encode(self::CHAR_COMMA));
                } else {
                    return $this->error('Unexpected '.json_encode(self::CHAR_COMMA));
                }
            }

            $node = $this->gobbleExpression();
            if ($node instanceof ParsingError) {
                return $node;
            }
            if ((null === $node) || (ExpressionType::COMPOUND === $node->type)) {
                return $this->error('Expected '.json_encode(self::CHAR_COMMA));
            }

            $args[] = $node;
            $hadComma = false;
        }

        if (!$closed) {
            return $this->error('Unclosed '.json_encode($start));
        }

        return $args;
    }

    /**
     * Gobble a non-literal variable name. This variable name may include properties
     * e.g. `foo`, `bar.baz`, `foo['bar'].baz`
     * It also gobbles function calls:
     * e.g. `Math.acos(obj.angle)`.
     *
     * @param string $ch the current character
     */
    private function gobbleVariable(string $ch): Expression|ParsingError|null
    {
        // parse a group or identifier first
        /** @var ParsingError|null */
        $node = null;
        if (self::CHAR_OPEN_PARENTHESES === $ch) {
            $group = $this->gobbleGroup();
            if ($group instanceof ParsingError) {
                return $group;
            }
            $node = $group;
        } else {
            $identifier = $this->gobbleIdentifier($ch);
            if ($identifier instanceof ParsingError) {
                return $identifier;
            }
            $node = $identifier;
        }
        if (null === $node) {
            return null;
        }

        // then iterate over operations applied to it
        while (true) {
            $ch = $this->skipSpaces();

            ++$this->index;

            // access via .
            if ($this->config['Features']['Members']['Static'] && self::CHAR_PERIOD === $ch) {
                $ch = $this->skipSpaces();

                $property = $this->gobbleIdentifier($ch);
                if ($property instanceof ParsingError) {
                    return $property;
                }

                $node = new Member($node, $property, false);

                continue;
            }

            // access via []s
            if ($this->config['Features']['Members']['Computed'] && self::CHAR_OPEN_BRACKET === $ch) {
                $prop = $this->gobbleExpression();
                if ($prop instanceof ParsingError) {
                    return $prop;
                }
                if (null === $prop) {
                    return $this->error('Expected expression');
                }

                $node = new Member($node, $prop, true);

                $ch = $this->skipSpaces();
                if (self::CHAR_CLOSE_BRACKET !== $ch) {
                    return $this->error('Unclosed '.json_encode(self::CHAR_OPEN_BRACKET));
                }

                ++$this->index;

                continue;
            }

            // call via ()s
            if ($this->config['Features']['Calls'] && self::CHAR_OPEN_PARENTHESES === $ch) {
                $args = $this->gobbleArguments(self::CHAR_OPEN_PARENTHESES, self::CHAR_CLOSE_PARENTHESES);
                if ($args instanceof ParsingError) {
                    return $args;
                }
                $node = new Call($node, $args);
                continue;
            }

            // Done
            --$this->index;
            break;
        }

        return $node;
    }

    /**
     * Responsible for parsing a group of things within parentheses `()`
     * This function assumes that it needs to gobble the opening parenthesis
     * and then tries to gobble everything within that parenthesis, assuming
     * that the next thing it should see is the close parenthesis. If not,
     * then the expression probably doesn't have a `)`.
     */
    private function gobbleGroup(): Expression|ParsingError|null
    {
        ++$this->index;

        $expr = $this->gobbleExpression();
        if ($expr instanceof ParsingError) {
            return $expr;
        }

        $ch = $this->skipSpaces();
        if (self::CHAR_CLOSE_PARENTHESES !== $ch) {
            return $this->error('Unclosed '.json_encode(self::CHAR_OPEN_PARENTHESES));
        }

        ++$this->index;

        return $expr;
    }

    /**
     * Responsible for parsing Array literals `[1, 2, 3]`
     * This function assumes that it needs to gobble the opening bracket
     * and then tries to gobble the expressions as arguments.
     */
    private function gobbleArray(): Ary|ParsingError
    {
        ++$this->index;

        $elements = $this->gobbleArguments(self::CHAR_OPEN_BRACKET, self::CHAR_CLOSE_BRACKET);
        if ($elements instanceof ParsingError) {
            return $elements;
        }

        return new Ary($elements);
    }

    /**
     * Gets the default configuration.
     *
     * @return Config
     */
    public static function GetDefaultConfig(): array
    {
        return [
            'Operators' => [
                'Literals' => [
                    'true' => true,
                    'false' => false,
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
                'Compound' => true,
                'Conditional' => true,
                'Identifiers' => true,
                'Calls' => true,
                'Members' => [
                    'Static' => true,
                    'Computed' => true,
                ],
                'Literals' => [
                    'Numeric' => true,
                    'NumericSeparator' => '',
                    'String' => true,
                    'Array' => true,
                ],
            ],
        ];
    }
}

// cSpell:words JSEP Oney
