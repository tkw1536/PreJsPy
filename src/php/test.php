<?php

include "PreJsPy.php";

class TestPreJsPy {
    public static string $BASE_PATH;
    public static function init() {
        self::$BASE_PATH = join('/', [dirname(__FILE__), '..', '..', 'tests']);
    }
    
    /**
     * Runs all tests stored in a given json file
     *
     * @param string $fn filename to load
     * @return void
     */
    public static function test_file(string $fn): void {
        echo "Running tests from " . $fn . " ";

        // Read the test case file
        $tests = json_decode(file_get_contents(self::$BASE_PATH . '/' . $fn), TRUE);
        
        // Create a new PreJSPy() instance.
        $p = new PreJsPy();

        // and run all the test cases.
        foreach ($tests as $t) {
            self::run_single_case($p, $t["config"], $t["input"], $t["output"], $t["message"]);
        }
        echo " OK\n";
    }

    private static function run_single_case(PreJsPy $instance, array $config, string $inp, array $out, string $message) {
        $instance->SetConfig(PreJsPy::GetDefaultConfig());
        $instance->SetConfig($config);

        echo ".";

        // do a quick and dirty comparison using json_encode
        $got = self::json_serialize($instance->Parse($inp));
        $want = self::json_serialize($out);
        if ($want !== $got) {
            echo "!\nFailed!\n\n";
            die("Failed testcase $message:\nGot:      $got\nExpected: $want\n");
        }
    }

    /**
     * Calls json_encode on the normalized value
     *
     * @param mixed $value
     * @return string
     */
    private static function json_serialize(mixed $value): string {
        return json_encode(self::value_normalize($value));
    }

    /**
     * Return a normalized copy of value.
     * 
     * Sorts all arrays according to their keys, even recursively. 
     *
     * @param mixed $value
     * @return mixed
     */
    private static function value_normalize(mixed $value): mixed {
        // it's not an array => copy it!
        if (!is_array($value)) {
            return $value;
        }

        $value = array_map(function(mixed $value) { return self::value_normalize($value); }, $value);
        ksort($value);
        return $value;
    }
}
TestPreJsPy::init();

echo "Starting php tests ...\n";
echo "PHP Version: " . phpversion() . "\n";
echo "\n";

// SYMBOLIC
TestPreJsPy::test_file('constant_symbolic.json');
TestPreJsPy::test_file('identifier_symbolic.json');

// LITERALS
TestPreJsPy::test_file('number_literals.json');
TestPreJsPy::test_file('string_literals.json');
TestPreJsPy::test_file('array_literals.json');

// OPERATORS
TestPreJsPy::test_file('unary_ops.json');
TestPreJsPy::test_file('binary_ops.json');

// CALLS & COMPOUNDS
TestPreJsPy::test_file('call.json');
TestPreJsPy::test_file('compound.json');

// PRECEDENCES
TestPreJsPy::test_file('precedence.json');

echo "\n";
echo "Done. \n";
