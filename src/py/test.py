import PreJsPy

import sys
import json
import os.path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypedDict, Optional

    class TestCase(TypedDict):
        config: "PreJsPy.PartialConfig"
        input: str
        output: Optional["PreJsPy.Expression"]
        error: Optional[str]
        message: str


BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "tests")


class TestPreJsPy(object):
    @classmethod
    def test_file(cls, fn):
        """
        Runs all tests stored in a given JSON file.

        :param fn: filename of file to read.
        """

        print("Running tests from {} ".format(fn), end="")

        # Read the test case file
        with open(os.path.join(BASE_PATH, fn), "r") as f:
            tests = json.load(f)

        # Create a new PreJSPy() instance.
        p = PreJsPy.PreJsPy()

        # and run all the test cases.
        for t in tests:
            cls.run_single_case(p, t)

        print(" OK")

    @classmethod
    def run_single_case(cls, instance: "PreJsPy.PreJsPy", test: "TestCase"):
        """Runs a single test case.
        :param instance: PreJsPy instance to test on.
        """

        instance.SetConfig(PreJsPy.PreJsPy.GetDefaultConfig())
        instance.SetConfig(test["config"])

        print(".", end="")

        # figure out what we are expecting
        wantErrorStr = cls.json_serialize(test["error"] if "error" in test else None)
        wantResult = test["output"] if "output" in test else None
        wantResultStr = cls.json_serialize(wantResult)

        # run the code and figure out what we got
        gotResult, gotError = instance.TryParse(test["input"])
        gotResultStr = cls.json_serialize(gotResult)
        gotErrorStr = cls.json_serialize(
            str(gotError) if gotError is not None else None
        )

        if gotErrorStr != wantErrorStr:
            print("!\nFailed\n")
            sys.stderr.write(
                "Failed testcase "
                + test["message"]
                + ":\nGot Error:  "
                + gotErrorStr
                + "\nWant Error: "
                + wantErrorStr
                + "\n"
            )
            sys.exit(1)

        if gotResultStr != wantResultStr:
            print("!\nFailed\n")
            sys.stderr.write(
                "Failed testcase "
                + test["message"]
                + ":\nGot Result:      "
                + gotResultStr
                + "\nExpected Result: "
                + wantResultStr
                + "\n"
            )
            sys.exit(1)

    @classmethod
    def json_serialize(cls, value):
        return json.dumps(cls.__value_normalize(value), sort_keys=True)

    @classmethod
    def __value_normalize(cls, value):
        if isinstance(value, int):
            # everything is a float!
            return float(value)
        if isinstance(value, list):
            return [cls.__value_normalize(v) for v in value]
        if isinstance(value, dict):
            return {k: cls.__value_normalize(v) for k, v in value.items()}
        return value


# ======================
# RUN ALL THE TEST CASES
# ======================
print("Starting Python tests ...")
print("Python Info: {}".format(sys.implementation))
print("")

# SYMBOLIC
TestPreJsPy.test_file("constant_symbolic.json")
TestPreJsPy.test_file("identifier_symbolic.json")

# LITERALS
TestPreJsPy.test_file("number_literals.json")
TestPreJsPy.test_file("string_literals.json")
TestPreJsPy.test_file("array_literals.json")

# OPERATORS
TestPreJsPy.test_file("unary_ops.json")
TestPreJsPy.test_file("binary_ops.json")

# CALLS & COMPOUNDS
TestPreJsPy.test_file("call.json")
TestPreJsPy.test_file("compound.json")

# PRECEDENCES
TestPreJsPy.test_file("precedence.json")

print("")
print("Done.")
