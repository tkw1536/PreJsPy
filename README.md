# PreJsPy
## What is this?
PreJsPy is highly configurable a precedence-based parser written in both Python and JavaScript. 
The default grammar is based on a subset of JavaScript but can be adapted to a lot of different scenarios. 

```
>>> parse("6 * 9 == 42")
{'type': 'BinaryExpression', 'operator': '==', 'right': {'type': 'Literal', 'raw': '42', 'value': 42.0}, 'left': {'type': 'BinaryExpression', 'operator': '*', 'right': {'type': 'Literal', 'raw': '9', 'value': 9.0}, 'left': {'type': 'Literal', 'raw': '6', 'value': 6.0}}}
```

```
> parse('6 * 9 == 42')
{ type: 'BinaryExpression',
  operator: '==',
  left: 
   { type: 'BinaryExpression',
     operator: '*',
     left: { type: 'Literal', value: 6, raw: '6' },
     right: { type: 'Literal', value: 9, raw: '9' } },
  right: { type: 'Literal', value: 42, raw: '42' } }
```

The JavaScript version of this library has been adapted from the JavaScript library JSEP which is (c) 2013 Stephen Oney, http://jsep.from.so/ and has been published under the terms of the MIT license. The code has been ported to Python and a lot of utility functions have been added. 

## Grammar Features

* Various types of literals
  * Numeric Literals (```42.001```)
    * decimal notation (```-42```)
    * exponential notation (```6.7E-10```)
  * Array Literals (```[1, 2, 3]```)
    * must be surrounded by square brackets
    * can be nested
  * String Literals (```"Hello world"```)
    * can be either double or single quotes
    * special characters can be escaped
  * Constants
    * such as ```true```, ```false``` and ```null```
    * special ```this``` constant
    * configurable: Arbitrary constants can be added
* Symbolic Values
  * Identifiers
    * may contain  $,\_ or alphanumeric chacraters but may not start with a number
    * can include property names and accessors, for example `foo`, `bar.baz`, `foo['bar'].baz`
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
    * can not be configured
* Call Expressions
  * must use round brackets
  * for example ```Math.cos(x)```

## API
The API in JavaScript and python are almost identical. The only differences come from the features of the languages themselves. 
### JavaScript API

```js
var parser = new PreJsPy(); // creates a new parser

parser.getConstants() // returns an object containing constants
parser.setConstants(dict) // sets the current constants know to the parser

parser.getThis() // gets the current constant representing this
parser.setThis(str) // sets the constant used for representing this

parser.getUnaryOperators() // gets an array of unary operators
parser.setUnaryOperators(ary) // sets an array of unary operators

parser.getBinaryOperators() // returns an object mapping binary operators to their precendency
parser.setBinaryOperators(ary) // sets the binary operators to precendence mapping

parser.parse(str) // parses a string into a AST
```

### Python API

```python
parser = PreJsPy() # creates a new parser

parser.constants # returns an object containing constants
parser.constants = d # sets the current constants know to the parser

parser.this # gets the current constant representing this
parser.this = s # sets the constant used for representing this

parser.unary_ops # gets an array of unary operators
parser.unary_ops = ary # sets an array of unary operators

parser.binary_ops # returns an object mapping binary operators to their precedence
parser.binary_ops = ary # sets the binary operators to precendence mapping

parser.parse(s) # parses a string into a AST
parser() # alternative to the above
```