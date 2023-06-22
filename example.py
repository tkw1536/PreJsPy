# in production, use the PreJsPy module
from src.py import PreJsPy

import json


def run_example(expr):
    """
    Parses a single expression and prints the result to stdout.

    :param expr: Expression to parse.
    :type expr: str
    """

    p = PreJsPy.PreJsPy()
    print(p.parse(expr))


def make_testcase(inp, msg):
    """
    Utility function to create a test case.

    :param inp: Input to use.
    :type inp: str

    :param msg: Message for test case.
    :type msg: str
    """

    p = PreJsPy.PreJsPy()
    out = p.parse(inp)

    print("""{
    "input": %s,
    "output": %s,
    "message": %s
}""" % (json.dumps(inp), json.dumps(out), json.dumps(msg)))


def main():
    """
    Main entry point for the example.
    """

    run_example('"Hello world"')


if __name__ == '__main__':
    main()
