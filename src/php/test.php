<?php

declare(strict_types=1);

include 'PreJsPy.php';

class TestPreJsPy
{
    public static string $BASE_PATH;
    public static function init()
    {
        self::$BASE_PATH = join('/', [dirname(__FILE__), '..', '..', 'tests']);
    }

    /**
     * Runs all tests stored in a given json file
     *
     * @param string $fn filename to load
     * @return void
     */
    public static function testFile(string $fn): void
    {
        echo 'Running tests from ' . $fn . ' ';

        // Read the test case file
        $tests = json_decode(file_get_contents(self::$BASE_PATH . '/' . $fn), true);

        // Create a new PreJSPy() instance.
        $p = new PreJsPy();

        // and run all the test cases.
        foreach ($tests as $t) {
            self::runSingleCase($p, $t);
        }
        echo " OK\n";
    }

    private static function runSingleCase(PreJsPy $instance, array $test)
    {
        $instance->SetConfig(PreJsPy::GetDefaultConfig());
        $instance->SetConfig($test['config']);

        echo '.';

        # figure out what we are expecting
        $wantErrorStr = self::jsonSerialize(array_key_exists('error', $test) ? $test['error'] : null);
        $wantResult = array_key_exists('output', $test) ? $test['output'] : null;
        $wantResultStr = self::jsonSerialize($wantResult);

        # run the code and figure out what we got
        [$gotResult, $gotError] = $instance->TryParse($test['input']);
        $gotResultStr = self::jsonSerialize($gotResult);
        $gotErrorStr = self::jsonSerialize(($gotError !== null) ? $gotError->getMessage() : null);

        if ($gotErrorStr !== $wantErrorStr) {
            echo "!\nFailed\n";
            echo 'Failed testcase ' . $test['message'] . ":\nGot Error:  ". $gotErrorStr . "\nWant Error: " . $wantErrorStr . "\n";

            die();
        }

        if ($gotResultStr != $wantResultStr) {
            echo "!\nFailed\n";
            echo 'Failed testcase ' . $test['message'] . ":\nGot Result:  ". $gotResultStr . "\nWant Result: " . $wantResultStr . "\n";

            die();
        }
    }

    /**
     * Calls json_encode on the normalized value
     *
     * @param mixed $value
     * @return string
     */
    private static function jsonSerialize(mixed $value): string
    {
        return json_encode(self::valueNormalize($value));
    }

    /**
     * Return a normalized copy of value.
     *
     * Sorts all arrays according to their keys, even recursively.
     *
     * @param mixed $value
     * @return mixed
     */
    private static function valueNormalize(mixed $value): mixed
    {
        // it's not an array => copy it!
        if (!is_array($value)) {
            return $value;
        }

        $value = array_map(function (mixed $value) {
            return self::valueNormalize($value);
        }, $value);
        ksort($value);
        return $value;
    }
}
TestPreJsPy::init();

echo "Starting php tests ...\n";
echo 'PHP Version: ' . phpversion() . "\n";
echo "\n";

// SYMBOLIC
TestPreJsPy::testFile('constant_symbolic.json');
TestPreJsPy::testFile('identifier_symbolic.json');

// LITERALS
TestPreJsPy::testFile('number_literals.json');
TestPreJsPy::testFile('string_literals.json');
TestPreJsPy::testFile('array_literals.json');

// OPERATORS
TestPreJsPy::testFile('unary_ops.json');
TestPreJsPy::testFile('binary_ops.json');

// CALLS & COMPOUNDS
TestPreJsPy::testFile('call.json');
TestPreJsPy::testFile('compound.json');

// PRECEDENCES
TestPreJsPy::testFile('precedence.json');

echo "\n";
echo "Done. \n";
