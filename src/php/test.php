<?php

declare(strict_types=1);

include 'PreJsPy.php';

class TestPreJsPy
{
    private static string $BASE_PATH;

    public static function init()
    {
        self::$BASE_PATH = implode('/', [__DIR__, '..', '..', 'tests']);
    }

    /**
     * Parses a json file from the tests directory.
     *
     * @param string $filename name of file to read
     */
    public static function parseJSONFile(string $filename): mixed
    {
        return json_decode(file_get_contents(self::$BASE_PATH.'/'.$filename), true);
    }

    /**
     * Runs all tests stored in a given json file.
     *
     * @param string $fn filename to load
     * @param int    $N  number of times to run for benchmarking purposes
     */
    public static function testFile(string $fn, int $N): float
    {
        echo 'Running tests from '.$fn.' ';

        // Read the test case file
        $tests = self::parseJSONFile($fn);

        // Create a new PreJSPy() instance.
        $p = new PreJsPy();

        // and run all the test cases.
        $total = (float) 0;
        foreach ($tests as $t) {
            $time = self::runSingleCase($p, $t, $N);
            $total += $time ?? 0;
        }
        echo ' OK ('.number_format($total, 10, '.', ',') * 1000 ."ms)\n";

        return $total;
    }

    private static function runSingleCase(PreJsPy $instance, array $test, int $N): float
    {
        $instance->SetConfig(self::parseJSONFile('_config.json'));
        $instance->SetConfig($test['config']);

        echo '.';

        // figure out what we are expecting
        $wantErrorStr = self::jsonSerialize(array_key_exists('error', $test) ? $test['error'] : null);
        $wantResult = array_key_exists('output', $test) ? $test['output'] : null;
        $wantResultStr = self::jsonSerialize($wantResult);

        // run the code and figure out what we got
        [$gotResult, $gotError] = $instance->TryParse($test['input']);
        $gotResultStr = self::jsonSerialize($gotResult);
        $gotErrorStr = self::jsonSerialize((null !== $gotError) ? $gotError->getMessage() : null);

        if ($gotErrorStr !== $wantErrorStr) {
            echo "!\nFailed\n";
            echo 'Failed testcase '.$test['message'].":\nGot Error:  ".$gotErrorStr."\nWant Error: ".$wantErrorStr."\n";

            exit;
        }

        if ($gotResultStr !== $wantResultStr) {
            echo "!\nFailed\n";
            echo 'Failed testcase '.$test['message'].":\nGot Result:  ".$gotResultStr."\nWant Result: ".$wantResultStr."\n";

            exit;
        }

        // do benchmarking
        $bench = (float) 0;
        $input = $test['input'];
        for ($i = 0; $i < $N; ++$i) {
            $start = microtime(true);
            $instance->TryParse($input);
            $end = microtime(true);

            $bench += $end - $start;
        }

        return $bench / $N;
    }

    /**
     * Calls json_encode on the normalized value.
     */
    private static function jsonSerialize(mixed $value): string
    {
        return json_encode(self::valueNormalize($value));
    }

    /**
     * Return a normalized copy of value.
     *
     * Sorts all arrays according to their keys, even recursively.
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
echo 'PHP Version: '.\PHP_VERSION."\n";
echo "\n";

/** @var string[] */
$files = TestPreJsPy::parseJSONFile('_manifest.json');
foreach ($files as $file) {
    TestPreJsPy::testFile($file, 10_000);
}

echo "\n";
echo "Done. \n";
