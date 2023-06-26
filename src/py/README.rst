=======
PreJsPy
=======

PreJsPy is highly configurable a precedence-based parser written in both Python (3.8+) and JavaScript (ES5+).
The default grammar is based on a subset of JavaScript but can be adapted to a lot of different scenarios.

.. code:: python

  >>> from PreJsPy import PreJsPy
  >>> parser = PreJsPy()
  >>> parser.parse("6 * 9 == 42")
  {'type': 'BinaryExpression', 'operator': '==', 'right': {'type': 'Literal', 'raw': '42', 'value': 42.0}, 'left': {'type': 'BinaryExpression', 'operator': '*', 'right': {'type': 'Literal', 'raw': '9', 'value': 9.0}, 'left': {'type': 'Literal', 'raw': '6', 'value': 6.0}}}

See https://github.com/tkw1536/PreJsPy for more detailed documentation.
