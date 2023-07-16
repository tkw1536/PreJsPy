import { readFileSync } from 'fs'
import path from 'path'
import { PreJsPy } from './PreJsPy'
import type { Expression, PartialConfig } from './PreJsPy'

const BASE_PATH = path.join(__dirname, '..', '..', 'tests')

interface TestCase {
  config: PartialConfig<any, string, string>
  input: string
  output: Expression<any, string, string>
  message: string
}

class TestPreJsPy {
  /**
   * Runs all test cases from a given file.
   * @param fn
   */
  static testFile (fn: string): void {
    process.stdout.write('Running tests from ' + fn + ' ')

    // read all the tests
    const tests: TestCase[] = JSON.parse(readFileSync(path.join(BASE_PATH, fn), 'utf8'))

    // Create a new PreJSPy instance.
    const p = new PreJsPy()

    // and run all the test cases.
    tests.forEach((t) => this.runSingleFile(p, t))

    console.log(' OK.')
  }

  /**
  * Runs a single test case.
  *
  * @param instance instance to test on. *
  * @param config Configuration to apply to PreJsPy instance
  *
  *
  * @param inp Input to parse.
  * @type param string
  *
  * @param out Expected output.
  * @type out string
  *
  * @param message Message of test case.
  * @type message string
  */
  private static runSingleFile (instance: PreJsPy<any, string, string>, test: TestCase): void {
   instance.SetConfig(PreJsPy.GetDefaultConfig()) // reset the config to default
   instance.SetConfig(test.config) // set config
 
   process.stdout.write('.')
   const want = this.jsonSerialize(test.output)
   const got = this.jsonSerialize(instance.Parse(test.input))

   if (want != got) {
    console.log('!\nFail\n')

    process.stderr.write("Failed testcase " + test.message + ":\nGot:      " + got + "\nExpected: " + want + "\n")
    process.exit(1)
   }
 }

  /** deterministic version of JSON.stringify that takes key order into account */
  private static jsonSerialize(value: any): string {
    if (Array.isArray(value)) {
      return "[" + value.map(e => this.jsonSerialize(e)).join(",") + "]";
    }
    if (value === null) {
      return "null";
    }
    if (typeof value === "object") {
      const pairs = Object.keys(value).sort()
        .map(key => JSON.stringify(key) + ":" + this.jsonSerialize(value[key]));
      return "{" + pairs.join(",") + "}";
    }

    // regular JSON.stringify
    return JSON.stringify(value);
  }
}




// ======================
// RUN ALL THE TEST CASES
// ======================
console.log('Starting TypeScript tests ...')
console.log('Node Version: ' + process.version)
console.log('')

// SYMBOLIC
TestPreJsPy.testFile('constant_symbolic.json')
TestPreJsPy.testFile('identifier_symbolic.json')

// LITERALS
TestPreJsPy.testFile('number_literals.json')
TestPreJsPy.testFile('string_literals.json')
TestPreJsPy.testFile('array_literals.json')

// OPERATORS
TestPreJsPy.testFile('unary_ops.json')
TestPreJsPy.testFile('binary_ops.json')

// CALLS & COMPOUNDS
TestPreJsPy.testFile('call.json')
TestPreJsPy.testFile('compound.json')

// PRECEDENCES
TestPreJsPy.testFile('precedence.json')

console.log('')
console.log('Done.')
