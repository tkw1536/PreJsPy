// (c) Tom Wiesing 2016, licensed under MIT license
// This code is heavily based on the JavaScript version JSEP
// The original code is (c) 2013 Stephen Oney, http://jsep.from.so/ and licensed under MIT

(function (root) {

    var COMPOUND = 'Compound',
        IDENTIFIER = 'Identifier',
        MEMBER_EXP = 'MemberExpression',
        LITERAL = 'Literal',
        THIS_EXP = 'ThisExpression',
        CALL_EXP = 'CallExpression',
        UNARY_EXP = 'UnaryExpression',
        BINARY_EXP = 'BinaryExpression',

        CONDITIONAL_EXP = 'ConditionalExpression',
        ARRAY_EXP = 'ArrayExpression';

    // LIST OF CHAR CODES
    var PERIOD_CODE = 46, // '.'
        COMMA_CODE = 44, // ','
        SQUOTE_CODE = 39, // single quote
        DQUOTE_CODE = 34, // double quotes
        OPAREN_CODE = 40, // (
        CPAREN_CODE = 41, // )
        OBRACK_CODE = 91, // [
        CBRACK_CODE = 93, // ]
        QUMARK_CODE = 63, // ?
        SEMCOL_CODE = 59, // ;
        COLON_CODE = 58; // :

    // =======================
    // STATIC HELPER FUNCTIONS
    // =======================

    /**
     * Throws a parser error with a given message and a given index.
     * @param message {string} Message of error to throw.
     * @param index {number} Character index at which the error should be thrown.
     */
    var throwError = function (message, index) {
        var error = new Error(message + ' at character ' + index);
        error.index = index;
        error.description = message;
        throw error;
    };

    /**
     * Utility function that creates a binary expression to be returned.
     * @param operator {string} Operator to use for binary expression.
     * @param left {object} Left expression to use for the binary expression.
     * @param right {object] Right expression to use for the binary expression.
     * @returns {object}
     */
    var createBinaryExpression = function (operator, left, right) {
        return {
            type: BINARY_EXP,
            operator: operator,
            left: left,
            right: right
        };
    };

    // TODO: Create utility functions for all the other return values also
    // just so that we are consistent.

    /**
     * Gets the longest key length of an object
     * @param o {object} Object to iterate over
     * @returns {number}
     */
    var getMaxKeyLen = function (o) {
        var max_len = 0, len;
        for (var key in o) {
            if ((len = key.length) > max_len && o.hasOwnProperty(key)) {
                max_len = len;
            }
        }
        return max_len;
    };

    /**
     * Gets the maximum length of the member of any members of an array.
     * @param ary {Array} Array to iterate over.
     * @returns {number}
     */
    var getMaxMemLen = function (ary) {
        var max_len = 0;

        for (var i = 0; i < ary.length; i++) {
            if (ary[i].length > max_len) {
                max_len = ary[i].length;
            }
        }

        return max_len;
    };

    /**
     * Checks if a character is a decimal digit.
     * @param ch {number} Code of character to check.
     * @returns {boolean}
     */
    var isDecimalDigit = function (ch) {
        return (ch >= 48 && ch <= 57); // 0...9
    };

    /**
     * Checks if a character is the start of an identifier.
     * @param ch {number} Code of character to check.
     * @returns {boolean}
     */
    var isIdentifierStart = function (ch) {
        return (ch === 36) || (ch === 95) || // `$` and `_`
            (ch >= 65 && ch <= 90) || // A...Z
            (ch >= 97 && ch <= 122); // a...z
    };

    /**
     * Checks if a character is part of an identifier.
     * @param ch {number} Code of character to check.
     * @returns {boolean}
     */
    var isIdentifierPart = function (ch) {
        return (ch === 36) || (ch === 95) || // `$` and `_`
            (ch >= 65 && ch <= 90) || // A...Z
            (ch >= 97 && ch <= 122) || // a...z
            (ch >= 48 && ch <= 57); // 0...9
    };

    /**
     * Represents a single instance of the PreJSPy Parser.
     * @constructor
     */
    var PreJsPy = function () {
        var self = this;


        // ==================
        // SETTERS && GETTERS
        // ==================

        /**
         * Gets the constants to be used by this parser.
         *
         * @return {object}
         */
        this.getConstants = function () {
            return __literals;
        };

        /**
         * Gets the constants to be used by this parser.
         *
         * @return {object}
         */
        this.setConstants = function (dict) {
            __literals = dict;
            return __literals;
        };

        /**
         * Gets the unary operators known to this parser.
         * @returns {string[]}
         */
        this.getUnaryOperators = function () {
            return __unary_ops;
        };

        /**
         * Gets the length of the maximal unary operator.
         * @returns {number}
         */
        this.getMaxUnaryOperatorsLength = function () {
            return __max_unop_len;
        };

        /**
         * Sets the unary operators known to this parser.
         * @param ary {string[]} List of unary operators to set.
         */
        this.setUnaryOperators = function (ary) {
            __unary_ops = ary;
            __max_unop_len = getMaxMemLen(__unary_ops);
        };

        /**
         * Gets the binary operators known to this parser.
         * @returns {object}
         */
        this.getBinaryOperators = function () {
            return __binary_ops;
        };

        /**
         * Gets the length of the maximal binary operator.
         * @returns {number}
         */
        this.getMaxBinaryOperatorsLength = function() {
            return __max_binop_len;
        };

        /**
         * Sets the binary operators known to this parser.
         * @param dict {object} Dictionary of binary operators to set.
         */
        this.setBinaryOperators = function (dict) {
            __binary_ops = dict;
            __max_binop_len = getMaxKeyLen(__binary_ops);
        };

        /**
         * Gets a boolean indicating if the tertiary operator is enabled or
         * not.
         * @returns {boolean}
         */
        this.getTertiaryOperatorEnabled = function () {
            return __tertiary;
        };

        /**
         *
         * @param e {boolean} State of the tertiary operator to set.
         */
        this.setTertiaryOperatorEnabled = function (e) {
            __tertiary = e;
        };

        // =========
        // INIT CODE
        // =========

        // Intitialise a set of literal constants for the parser.
        var __literals;
        this.setConstants({
            'true': true,
            'false': false,
            'null': null
        });

        // Set a list of unary operators
        var __unary_ops;
        var __max_unop_len;
        this.setUnaryOperators(['-', '!', '~', '+']);

        // Set a list of binary operators and their preferences.
        // See http://en.wikipedia.org/wiki/Order_of_operations#Programming_language
        var __binary_ops;
        var __max_binop_len;
        this.setBinaryOperators({
            '||': 1, '&&': 2, '|': 3, '^': 4, '&': 5,
            '==': 6, '!=': 6, '===': 6, '!==': 6,
            '<': 7, '>': 7, '<=': 7, '>=': 7,
            '<<': 8, '>>': 8, '>>>': 8,
            '+': 9, '-': 9,
            '*': 10, '/': 10, '%': 10
        });

        // enable the tertiary operator
        var __tertiary;
        this.setTertiaryOperatorEnabled(true);



        // ============
        // MISC HELPERS
        // ============

        /**
         * Returns the precedence of a binary operator or `0` if it isn't a binary operator.
         * @param op_val {string} Value of operator to lookup.
         * @returns {number}
         */
        var binaryPrecedence = function (op_val) {
            return self.getBinaryOperators()[op_val] || 0;
        };

        // =======
        // Parsing
        // =======

        /**
         * Parses an expression expression into a parse tree.
         * @param expr {string} Expression to parse.
         * @returns {object}
         */
        this.parse = function (expr) {
            // `index` stores the character number we are currently at while `length` is a constant
            // All of the gobbles below will modify `index` as we move along
            var index = 0,
                charAtFunc = expr.charAt,
                charCodeAtFunc = expr.charCodeAt,
                exprI = function (i) {
                    return charAtFunc.call(expr, i);
                },
                exprICode = function (i) {
                    return charCodeAtFunc.call(expr, i);
                },
                length = expr.length,

                // Push `index` up to the next non-space character
                gobbleSpaces = function () {
                    var ch = exprICode(index);
                    // space or tab
                    while (ch === 32 || ch === 9) {
                        ch = exprICode(++index);
                    }
                },

                // The main parsing function. Much of this code is dedicated to ternary expressions
                gobbleExpression = function () {
                    var test = gobbleBinaryExpression(),
                        consequent, alternate;
                    gobbleSpaces();
                    if (exprICode(index) === QUMARK_CODE) {
                        // Ternary expression: test ? consequent : alternate
                        index++;
                        consequent = gobbleExpression();
                        if (!consequent) {
                            throwError('Expected expression', index);
                        }
                        gobbleSpaces();
                        if (exprICode(index) === COLON_CODE) {
                            index++;
                            alternate = gobbleExpression();
                            if (!alternate) {
                                throwError('Expected expression', index);
                            }
                            if (!self.getTertiaryOperatorEnabled()){
                                throwError('Unexpected tertiary operator',
                                    index);
                            }
                            return {
                                type: CONDITIONAL_EXP,
                                test: test,
                                consequent: consequent,
                                alternate: alternate
                            };
                        } else {
                            throwError('Expected :', index);
                        }
                    } else {
                        return test;
                    }
                },

                // Search for the operation portion of the string (e.g. `+`, `===`)
                // Start by taking the longest possible binary operations (3 characters: `===`, `!==`, `>>>`)
                // and move down from 3 to 2 to 1 character until a matching binary operation is found
                // then, return that binary operation
                gobbleBinaryOp = function () {
                    gobbleSpaces();
                    var biop, to_check = expr.substr(index, self.getMaxBinaryOperatorsLength()), tc_len = to_check.length;
                    while (tc_len > 0) {
                        if (self.getBinaryOperators().hasOwnProperty(to_check)) {
                            index += tc_len;
                            return to_check;
                        }
                        to_check = to_check.substr(0, --tc_len);
                    }
                    return false;
                },

                // This function is responsible for gobbling an individual expression,
                // e.g. `1`, `1+2`, `a+(b*2)-Math.sqrt(2)`
                gobbleBinaryExpression = function () {
                    var ch_i, node, biop, prec, stack, biop_info, left, right, i;

                    // First, try to get the leftmost thing
                    // Then, check to see if there's a binary operator operating on that leftmost thing
                    left = gobbleToken();
                    biop = gobbleBinaryOp();

                    // If there wasn't a binary operator, just return the leftmost node
                    if (!biop) {
                        return left;
                    }

                    // Otherwise, we need to start a stack to properly place the binary operations in their
                    // precedence structure
                    biop_info = {value: biop, prec: binaryPrecedence(biop)};

                    right = gobbleToken();
                    if (!right) {
                        throwError("Expected expression after " + biop, index);
                    }
                    stack = [left, biop_info, right];

                    // Properly deal with precedence using [recursive descent](http://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)
                    while ((biop = gobbleBinaryOp())) {
                        prec = binaryPrecedence(biop);

                        if (prec === 0) {
                            break;
                        }
                        biop_info = {value: biop, prec: prec};

                        // Reduce: make a binary expression from the three topmost entries.
                        while ((stack.length > 2) && (prec <= stack[stack.length - 2].prec)) {
                            right = stack.pop();
                            biop = stack.pop().value;
                            left = stack.pop();
                            node = createBinaryExpression(biop, left, right);
                            stack.push(node);
                        }

                        node = gobbleToken();
                        if (!node) {
                            throwError("Expected expression after " + biop, index);
                        }
                        stack.push(biop_info, node);
                    }

                    i = stack.length - 1;
                    node = stack[i];
                    while (i > 1) {
                        node = createBinaryExpression(stack[i - 1].value, stack[i - 2], node);
                        i -= 2;
                    }
                    return node;
                },

                // An individual part of a binary expression:
                // e.g. `foo.bar(baz)`, `1`, `"abc"`, `(a % 2)` (because it's in parenthesis)
                gobbleToken = function () {
                    var ch, to_check, tc_len;

                    gobbleSpaces();
                    ch = exprICode(index);

                    if (isDecimalDigit(ch) || ch === PERIOD_CODE) {
                        // Char code 46 is a dot `.` which can start off a numeric literal
                        return gobbleNumericLiteral();
                    } else if (ch === SQUOTE_CODE || ch === DQUOTE_CODE) {
                        // Single or double quotes
                        return gobbleStringLiteral();
                    } else if (ch === OBRACK_CODE) {
                        return gobbleArray();
                    } else {
                        to_check = expr.substr(index, self.getMaxUnaryOperatorsLength());
                        tc_len = to_check.length;
                        while (tc_len > 0) {
                            if (self.getUnaryOperators().indexOf(to_check) != -1) {
                                index += tc_len;
                                return {
                                    type: UNARY_EXP,
                                    operator: to_check,
                                    argument: gobbleToken()
                                };
                            }
                            to_check = to_check.substr(0, --tc_len);
                        }

                        if (isIdentifierStart(ch) || ch === OPAREN_CODE) { // open parenthesis
                            // `foo`, `bar.baz`
                            return gobbleVariable();
                        }
                    }

                    return false;
                },
                // Parse simple numeric literals: `12`, `3.4`, `.5`. Do this by using a string to
                // keep track of everything in the numeric literal and then calling `parseFloat` on that string
                gobbleNumericLiteral = function () {
                    var number = '', ch, chCode;
                    while (isDecimalDigit(exprICode(index))) {
                        number += exprI(index++);
                    }

                    if (exprICode(index) === PERIOD_CODE) { // can start with a decimal marker
                        number += exprI(index++);

                        while (isDecimalDigit(exprICode(index))) {
                            number += exprI(index++);
                        }
                    }

                    ch = exprI(index);
                    if (ch === 'e' || ch === 'E') { // exponent marker
                        number += exprI(index++);
                        ch = exprI(index);
                        if (ch === '+' || ch === '-') { // exponent sign
                            number += exprI(index++);
                        }
                        while (isDecimalDigit(exprICode(index))) { //exponent itself
                            number += exprI(index++);
                        }
                        if (!isDecimalDigit(exprICode(index - 1))) {
                            throwError('Expected exponent (' + number + exprI(index) + ')', index);
                        }
                    }


                    chCode = exprICode(index);
                    // Check to make sure this isn't a variable name that start with a number (123abc)
                    if (isIdentifierStart(chCode)) {
                        throwError('Variable names cannot start with a number (' +
                            number + exprI(index) + ')', index);
                    } else if (chCode === PERIOD_CODE) {
                        throwError('Unexpected period', index);
                    }

                    return {
                        type: LITERAL,
                        value: parseFloat(number),
                        raw: number
                    };
                },

                // Parses a string literal, staring with single or double quotes with basic support for escape codes
                // e.g. `"hello world"`, `'this is\nJSEP'`
                gobbleStringLiteral = function () {
                    var str = '', quote = exprI(index++), closed = false, ch;

                    while (index < length) {
                        ch = exprI(index++);
                        if (ch === quote) {
                            closed = true;
                            break;
                        } else if (ch === '\\') {
                            // Check for all of the common escape codes
                            ch = exprI(index++);
                            switch (ch) {
                                case 'n':
                                    str += '\n';
                                    break;
                                case 'r':
                                    str += '\r';
                                    break;
                                case 't':
                                    str += '\t';
                                    break;
                                case 'b':
                                    str += '\b';
                                    break;
                                case 'f':
                                    str += '\f';
                                    break;
                                case 'v':
                                    str += '\x0B';
                                    break;
                                case '\\':
                                    str += '\\';
                                    break;

                                // default: just add the character literally.
                                default:
                                    str += ch;
                            }
                        } else {
                            str += ch;
                        }
                    }

                    if (!closed) {
                        throwError('Unclosed quote after "' + str + '"', index);
                    }

                    return {
                        type: LITERAL,
                        value: str,
                        raw: quote + str + quote
                    };
                },

                // Gobbles only identifiers
                // e.g.: `foo`, `_value`, `$x1`
                // Also, this function checks if that identifier is a literal:
                // (e.g. `true`, `false`, `null`) or `this`
                gobbleIdentifier = function () {
                    var ch = exprICode(index), start = index, identifier;

                    if (isIdentifierStart(ch)) {
                        index++;
                    } else {
                        throwError('Unexpected ' + exprI(index), index);
                    }

                    while (index < length) {
                        ch = exprICode(index);
                        if (isIdentifierPart(ch)) {
                            index++;
                        } else {
                            break;
                        }
                    }
                    identifier = expr.slice(start, index);

                    if (self.getConstants().hasOwnProperty(identifier)) {
                        return {
                            type: LITERAL,
                            value: self.getConstants()[identifier],
                            raw: identifier
                        };
                    } else {
                        return {
                            type: IDENTIFIER,
                            name: identifier
                        };
                    }
                },

                // Gobbles a list of arguments within the context of a function call
                // or array literal. This function also assumes that the opening character
                // `(` or `[` has already been gobbled, and gobbles expressions and commas
                // until the terminator character `)` or `]` is encountered.
                // e.g. `foo(bar, baz)`, `my_func()`, or `[bar, baz]`
                gobbleArguments = function (termination) {
                    var ch_i, args = [], node;
                    while (index < length) {
                        gobbleSpaces();
                        ch_i = exprICode(index);
                        if (ch_i === termination) { // done parsing
                            index++;
                            break;
                        } else if (ch_i === COMMA_CODE) { // between expressions
                            index++;
                        } else {
                            node = gobbleExpression();
                            if (!node || node.type === COMPOUND) {
                                throwError('Expected comma', index);
                            }
                            args.push(node);
                        }
                    }
                    return args;
                },

                // Gobble a non-literal variable name. This variable name may include properties
                // e.g. `foo`, `bar.baz`, `foo['bar'].baz`
                // It also gobbles function calls:
                // e.g. `Math.acos(obj.angle)`
                gobbleVariable = function () {
                    var ch_i, node;
                    ch_i = exprICode(index);

                    if (ch_i === OPAREN_CODE) {
                        node = gobbleGroup();
                    } else {
                        node = gobbleIdentifier();
                    }
                    gobbleSpaces();
                    ch_i = exprICode(index);
                    while (ch_i === PERIOD_CODE || ch_i === OBRACK_CODE || ch_i === OPAREN_CODE) {
                        index++;
                        if (ch_i === PERIOD_CODE) {
                            gobbleSpaces();
                            node = {
                                type: MEMBER_EXP,
                                computed: false,
                                object: node,
                                property: gobbleIdentifier()
                            };
                        } else if (ch_i === OBRACK_CODE) {
                            node = {
                                type: MEMBER_EXP,
                                computed: true,
                                object: node,
                                property: gobbleExpression()
                            };
                            gobbleSpaces();
                            ch_i = exprICode(index);
                            if (ch_i !== CBRACK_CODE) {
                                throwError('Unclosed [', index);
                            }
                            index++;
                        } else if (ch_i === OPAREN_CODE) {
                            // A function call is being made; gobble all the arguments
                            node = {
                                type: CALL_EXP,
                                'arguments': gobbleArguments(CPAREN_CODE),
                                callee: node
                            };
                        }
                        gobbleSpaces();
                        ch_i = exprICode(index);
                    }
                    return node;
                },

                // Responsible for parsing a group of things within parentheses `()`
                // This function assumes that it needs to gobble the opening parenthesis
                // and then tries to gobble everything within that parenthesis, assuming
                // that the next thing it should see is the close parenthesis. If not,
                // then the expression probably doesn't have a `)`
                gobbleGroup = function () {
                    index++;
                    var node = gobbleExpression();
                    gobbleSpaces();
                    if (exprICode(index) === CPAREN_CODE) {
                        index++;
                        return node;
                    } else {
                        throwError('Unclosed (', index);
                    }
                },

                // Responsible for parsing Array literals `[1, 2, 3]`
                // This function assumes that it needs to gobble the opening bracket
                // and then tries to gobble the expressions as arguments.
                gobbleArray = function () {
                    index++;
                    return {
                        type: ARRAY_EXP,
                        elements: gobbleArguments(CBRACK_CODE)
                    };
                },

                nodes = [], ch_i, node;

            while (index < length) {
                ch_i = exprICode(index);

                // Expressions can be separated by semicolons, commas, or just inferred without any
                // separators
                if (ch_i === SEMCOL_CODE || ch_i === COMMA_CODE) {
                    index++; // ignore separators
                } else {
                    // Try to gobble each expression individually
                    if ((node = gobbleExpression())) {
                        nodes.push(node);
                        // If we weren't able to find a binary expression and are out of room, then
                        // the expression passed in probably has too much
                    } else if (index < length) {
                        throwError('Unexpected "' + exprI(index) + '"', index);
                    }
                }
            }

            // If there's only one expression just try returning the expression
            if (nodes.length === 1) {
                return nodes[0];
            } else {
                return {
                    type: COMPOUND,
                    body: nodes
                };
            }
        };
    };

    // also put it into the global context
    root.PreJsPy = PreJsPy;

    // In Node.JS environments
    if (typeof module !== 'undefined' && module.exports) {
        exports.PreJsPy = module.exports.PreJsPy = PreJsPy;
    } else {
        exports.PreJsPy = PreJsPy;
    }
}(this));
