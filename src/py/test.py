import PreJsPy

import sys
import json
import os.path
import time

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from typing import TypedDict, Optional

    class TestCase(TypedDict):
        config: "PreJsPy.PartialConfig"
        input: str
        output: Optional["PreJsPy.Expression"]
        error: Optional[str]
        message: str


class TestPreJsPy(object):
    __BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "tests")

    @classmethod
    def read_json_file(cls, filename: str) -> Any:
        with open(os.path.join(cls.__BASE_PATH, filename), "r") as f:
            return json.load(f)

    @classmethod
    def test_file(cls, fn: str, N: int) -> float:
        """
        Runs all tests stored in a given JSON file.

        :param fn: filename of file to read.
        """

        print("Running tests from {} ".format(fn), end="")

        # Read the test case file
        tests = cls.read_json_file(fn)

        # Create a new PreJSPy() instance.
        p = PreJsPy.PreJsPy()

        # and run all the test cases.
        count = 0.0
        for t in tests:
            count += cls.run_single_case(p, t, N)

        print(" OK ({:.10f}ms)".format(count))

    @classmethod
    def run_single_case(
        cls, instance: "PreJsPy.PreJsPy", test: "TestCase", N: int
    ) -> float:
        """Runs a single test case.
        :param instance: PreJsPy instance to test on.
        """

        instance.SetConfig(cls.read_json_file("_config.json"))
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

        # do benchmarking
        bench = 0.0
        input = test["input"]
        for _ in range(N):
            start = time.time()
            instance.TryParse(input)
            end = time.time()
            bench += end - start
        return bench / N

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

files = TestPreJsPy.read_json_file("_manifest.json")
for file in files:
    TestPreJsPy.test_file(file, 10_000)

print("")
print("Done.")
