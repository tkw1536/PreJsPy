# PreJsPy

[![Python Build Status](https://github.com/tkw1536/PreJsPy/actions/workflows/python.yml/badge.svg)](https://github.com/tkw1536/PreJsPy/actions/workflows/python.yml)
[![TypeScript Build Status](https://github.com/tkw1536/PreJsPy/actions/workflows/ts.yml/badge.svg)](https://github.com/tkw1536/PreJsPy/actions/workflows/ts.yml)
[![PHP Build Status](https://github.com/tkw1536/PreJsPy/actions/workflows/php.yml/badge.svg)](https://github.com/tkw1536/PreJsPy/actions/workflows/php.yml)

## What is this?

PreJsPy is highly configurable a precedence-based parser written in both
Python (3.8+), JavaScript (ES5+), PHP (8.1+) and other languages. The default grammar is based on a
subset of JavaScript but can be adapted to a lot of different scenarios.

```python

>>> from PreJsPy import PreJsPy
>>> parser = PreJsPy()
>>> parser.Parse("6 * 9 == 42")
{'type': 'BinaryExpression', 'operator': '==', 'right': {'type': 'Literal', 'raw': '42', 'value': 42.0}, 'left': {'type': 'BinaryExpression', 'operator': '*', 'right': {'type': 'Literal', 'raw': '9', 'value': 9.0}, 'left': {'type': 'Literal', 'raw': '6', 'value': 6.0}}}
```

```js
> var PreJsPy = require('pre-js-py').PreJsPy;
> parser = new PreJsPy()
> parser.{arse('6 * 9 == 42')
{ type: 'BinaryExpression',
  operator: '==',
  left:
   { type: 'BinaryExpression',
     operator: '*',
     left: { type: 'Literal', value: 6, raw: '6' },
     right: { type: 'Literal', value: 9, raw: '9' } },
  right: { type: 'Literal', value: 42, raw: '42' } }
```

```php
<?php
include "./src/php/PreJsPy.php";
$parser = new PreJsPy();
$parser->Parse("6 * 9 == 42");

// Serialized output:
// a:4:{s:4:"type";E:25:"ExpressionType:BINARY_EXP";s:8:"operator";s:2:"==";s:4:"left";a:4:{s:4:"type";r:2;s:8:"operator";s:1:"*";s:4:"left";a:4:{s:4:"type";E:22:"ExpressionType:LITERAL";s:4:"kind";s:6:"number";s:5:"value";d:6;s:3:"raw";s:1:"6";}s:5:"right";a:4:{s:4:"type";r:8;s:4:"kind";s:6:"number";s:5:"value";d:9;s:3:"raw";s:1:"9";}}s:5:"right";a:4:{s:4:"type";r:8;s:4:"kind";s:6:"number";s:5:"value";d:42;s:3:"raw";s:2:"42";}}
```

The JavaScript version of this library has been adapted from the
JavaScript library JSEP which is (c) 2013 Stephen Oney,
<http://jsep.from.so/> and has been published under the terms of the MIT
license. The code has been ported to Python and a lot of utility
functions have been added.

## Grammar Features

* Symbolic Values
   * Constants
      * such as ```true```, ```false``` and ```null```
      * configurable: Arbitrary constants can be added 
   * Identifiers
      * may contain  $,\_ or alphanumeric characters but may not start with a number
      * for example ```foo```
   * Accessors
      * can be static or computed ```foo.bar```, ```foo['bar']```
* Various types of literals
   * Numeric Literals (```42.001```)
      * decimal notation (```-42```)
      * exponential notation (```6.7E-10```)
   * String Literals (```"Hello world"```)
      * can be either double or single quotes
      * special characters can be escaped
   * Array Literals (```[1, 2, 3]```)
      * must be surrounded by square brackets
      * can be nested
* Multiple types of operators
   * Unary operators
      * by default ```-```, ```!```, ```~``` and ```+```
      * custom operators can be added, existing ones can be removed
   * Binary operators
      * precedence based
      * by default contains all JavaScript operators
      * custom ones can be added with custom precedences
      * brackets can be used to override precedences
   * JavaScript Conditional operator
      * single ternary operator ```a ? b : c```
* Call Expressions
   * must use round brackets
   * for example ```Math.cos(x)```

## API

The API in JavaScript and python are almost identical. The only
differences come from the features of the languages themselves.

``` javascript
var PreJsPy = require('pre-js-py').PreJsPy;

var parser = new PreJsPy(); // creates a new parser
var ast = parser.Parse(s); // parses a string into a AST.

var config = parser.GetConfig(); // returns a configuration object of the parser.
parser.setConfig(config); // sets configuration of the parser. May be partial.

PreJsPy.GetDefaultConfig(); // returns the default configuration for new parsers.
```

``` python
from PreJsPy import PreJsPy

parser = PreJsPy() # creates a new parser.
ast = parser.Parse(s) # parses a string into a AST,

config = parser.GetConfig() # returns a configuration object of the parser.
parser.SetConfig(config) # sets configuration of the parser. May be partial.

PreJsPy.GetDefaultConfig() # returns the default configuration for new parsers
```

Configuration passed to and from returned from `getConfig` configures the desired features of the parser.
A configuration passed to `setConfig` may be partial, in which case the previously configured settings are left intact.
A configuration returned from `getConfig` is always complete.

The default configuration (which explanations) is found below:

```json
{
   // Operators supported by the browser
   "Operators": {
      // The set of literals (i.e. constants) recognized by the parser.
      // Note that these cannot be used as identifiers.
      "Literals": { "true": true, "false": false, "null": null },

      // The set of unary operators recognized by the parser.
      // These all bind more tightly than binary operators.
      // For example, "- a || b" parses as "(-a) || b".
      "Unary": [ "-", "!", "~", "+" ],

      // A set of binary operators mapped to their precedence.
      // Higher precedence means higher binding power.
      // For example "a || b == c", parses as "(a || b) == c".
      "Binary": {
            "||": 1,
            "&&": 2,
            "|": 3,
            "^": 4,
            "&": 5,
            "==": 6,
            "!=": 6,
            "===": 6,
            "!==": 6,
            "<": 7,
            ">": 7,
            "<=": 7,
            ">=": 7,
            "<<": 8,
            ">>": 8,
            ">>>": 8,
            "+": 9,
            "-": 9,
            "*": 10,
            "/": 10,
            "%": 10
      }
   },

   // Enable, disable and customize features.
   "Features": {
      // Top-level comound expressions
      "Compound": true,
      // The tertiary operators "a ? b : c".
      "Tertiary": true,
      // Non-constant, non-quoted identifiers in the code.
      "Identifiers": true,
      // Function calls.
      "Calls": true,
      "Members": {
            // Static Member Accesses like "car.wheels"
            "Static": true,
            // Computed Member Accesses like "something[i + 1]"
            "Computed": true
      },
      "Literals": {
            // Numeric literals like "1.2"
            "Numeric": true,
            // An additional separator that can be included in numeric literals.
            // For example, "_" would allow numbers like "1_000_000".
            "NumericSeparator": "",
            // String literals, enclosed in double quotes.
            "String": true,
            // Array literals, like "[1,2,3]"
            "Array": true
      }
   }
}
```

## Install

This package is published on the [Python Package
Index](https://pypi.python.org/pypi/pre_js_py) Installation can be done
simply via pip:

```bash
pip install pre_js_py
```

It is also published on [Nodejs Package
Manager](https://www.npmjs.com/package/pre-js-py) Installation can be
done simply via npm:

```bash
npm install pre-js-py
```

## License + Acknowledgements

This module and associated documentation is Copyright (c) Tom Wiesing
2016 and licensed under the MIT license, see [license](LICENSE) for
details.
