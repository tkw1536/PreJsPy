=======
PreJsPy
=======

.. image:: https://travis-ci.com/tkw1536/PreJsPy.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.com/tkw1536/PreJsPy

What is this?
=============

PreJsPy is highly configurable a precedence-based parser written in both Python and JavaScript.
The default grammar is based on a subset of JavaScript but can be adapted to a lot of different scenarios.

.. code:: python

  >>> from PreJsPy import PreJsPy
  >>> parser = PreJsPy()
  >>> parser.parse("6 * 9 == 42")
  {'type': 'BinaryExpression', 'operator': '==', 'right': {'type': 'Literal', 'raw': '42', 'value': 42.0}, 'left': {'type': 'BinaryExpression', 'operator': '*', 'right': {'type': 'Literal', 'raw': '9', 'value': 9.0}, 'left': {'type': 'Literal', 'raw': '6', 'value': 6.0}}}

.. code:: js

  > var PreJsPy = require('pre-js-py').PreJsPy;
  > parser = new PreJsPy()
  > parser.parse('6 * 9 == 42')
  { type: 'BinaryExpression',
    operator: '==',
    left:
     { type: 'BinaryExpression',
       operator: '*',
       left: { type: 'Literal', value: 6, raw: '6' },
       right: { type: 'Literal', value: 9, raw: '9' } },
    right: { type: 'Literal', value: 42, raw: '42' } }

The JavaScript version of this library has been adapted from the JavaScript library JSEP which is (c) 2013 Stephen Oney, http://jsep.from.so/ and has been published under the terms of the MIT license. The code has been ported to Python and a lot of utility functions have been added.

Grammar Features
=================

* Symbolic Values
   * Constants
      * such as ```true```, ```false``` and ```null```
      * configurable: Arbitrary constants can be added
   * Identifiers
      * may contain  $,\_ or alphanumeric chacraters but may not start with a number
      * can include property names and accessors, for example `foo`, `bar.baz`, `foo['bar'].baz`
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

API
===

The API in JavaScript and python are almost identical. The only differences come from the features of the languages themselves.

.. code:: javascript

  var parser = new PreJsPy(); // creates a new parser

  parser.getConstants() // returns an object containing constants
  parser.setConstants(d) // sets the current constants know to the parser

  parser.getUnaryOperators() // gets an array of unary operators
  parser.setUnaryOperators(ary) // sets an array of unary operators

  parser.getBinaryOperators() // returns an object mapping binary operators to their precedence
  parser.setBinaryOperators(ary) // sets the binary operators to precedence mapping

  parser.parse(s) // parses a string into a AST

.. code:: python

  parser = PreJsPy() # creates a new parser

  parser.getConstants() # returns an object containing constants
  parser.setConstants(d) # sets the current constants know to the parser

  parser.getUnaryOperators() # gets an array of unary operators
  parser.setUnaryOperators(ary) # sets an array of unary operators

  parser.getBinaryOperators() # returns an object mapping binary operators to their precedence
  parser.setBinaryOperators(ary) # sets the binary operators to precedence mapping

  parser.parse(s) # parses a string into a AST

Install
=======

This package is published on the
`Python Package Index <https://pypi.python.org/pypi/pre_js_py>`_
Installation can be done simply via pip:

.. code:: bash

   pip install pre_js_py

It is also published on
`Nodejs Package Manager <https://www.npmjs.com/package/pre-js-py>`_
Installation can be done simply via npm:

.. code:: bash

   npm install pre-js-py


License + Acknowledgements
==========================

This module and associated documentation is Copyright (c) Tom Wiesing 2016
and licensed under the MIT license, see `license <LICENSE>`_ for details.
