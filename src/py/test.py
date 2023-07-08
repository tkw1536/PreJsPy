import unittest
import PreJsPy

import json
import os.path

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "tests")


class TestPreJsPy(unittest.TestCase):
    def test_a_constant_symbolic(self):
        self.load_file("constant_symbolic.json")

    def test_b_identifier_symbolic(self):
        self.load_file("identifier_symbolic.json")

    def test_c_number_literals(self):
        self.load_file("number_literals.json")

    def test_d_number_literals(self):
        self.load_file("string_literals.json")

    def test_e_number_literals(self):
        self.load_file("array_literals.json")

    def test_f_number_literals(self):
        self.load_file("unary_ops.json")

    def test_g_number_literals(self):
        self.load_file("binary_ops.json")

    def test_h_number_literals(self):
        self.load_file("call.json")

    def test_i_number_literals(self):
        self.load_file("compound.json")

    def test_j_number_literals(self):
        self.load_file("precedence.json")

    def load_file(self, fn):
        """
        Runs all tests stored in a given JSON file.

        :param fn: filename of file to read.
        """

        print("\nRunning tests from %s" % fn)

        # Read the test case file
        with open(os.path.join(BASE_PATH, fn), 'r') as f:
            tests = json.load(f)

        # Create a new PreJSPy() instance.
        p = PreJsPy.PreJsPy()

        # and run all the test cases.
        for t in tests:
            self.run_single_case(p, t["config"], t["input"], t["output"], t["message"])

    def run_single_case(self, instance, config, inp, out, message):
        """ Runs a single test case.
        :param instance: PreJsPy instance to test on.
        :type instance: PreJsPy.PreJsPy

        :param config: Configuration object to apply
        :type config: dict

        :param inp: Input to parse.
        :type inp: str

        :param out: Expected output.
        :type out: dict

        :param message: Message of test case.
        :type message: str
        """

        instance.SetConfig(PreJsPy.PreJsPy.GetDefaultConfig())
        instance.SetConfig(config)

        self.assertEqual(instance.Parse(inp), out, msg=message)

if __name__ == '__main__':
    print("Starting python tests ...")
    unittest.main()
    print("Done. ")
