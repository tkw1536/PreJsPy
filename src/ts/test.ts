import { readFileSync } from 'fs'
import path from 'path'
import { PreJsPy } from './PreJsPy'
import type { Expression, PartialConfig } from './PreJsPy'

const BASE_PATH = path.join(__dirname, '..', '..', 'tests')

interface TestCase {
  config: PartialConfig
  input: string
  output?: Expression
  error?: string
  message: string
}

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
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
  private static runSingleFile (instance: PreJsPy, test: TestCase): void {
    instance.SetConfig(PreJsPy.GetDefaultConfig()) // reset the config to default
    instance.SetConfig(test.config) // set config

    process.stdout.write('.')

    // figure out what we are expecting
    const wantErrorStr = JSON.stringify(test.error ?? null)
    const wantResult = test.output ?? null
    const wantResultStr = this.jsonSerialize(wantResult)

    // run the code and figure out what we got
    const [gotResult, gotError] = instance.TryParse(test.input)
    const gotResultStr = this.jsonSerialize(gotResult)
    const gotErrorStr = JSON.stringify(gotError?.message ?? null)

    // check that the errors are identical
    if (wantErrorStr !== gotErrorStr) {
      console.log('!\nFail\n')

      process.stderr.write('Failed testcase ' + test.message + ':\nGot Error:  ' + gotErrorStr + '\nWant Error: ' + wantErrorStr + '\n')
      process.exit(1)
    }

    // check that the results are identical
    if (wantResultStr !== gotResultStr) {
      console.log('!\nFail\n')

      process.stderr.write('Failed testcase ' + test.message + ':\nGot Result:      ' + gotResultStr + '\nExpected Result: ' + wantResultStr + '\n')
      process.exit(1)
    }
  }

  /** deterministic version of JSON.stringify that takes key order into account */
  private static jsonSerialize (value: any): string {
    if (Array.isArray(value)) {
      return '[' + value.map(e => this.jsonSerialize(e)).join(',') + ']'
    }
    if (value === null) {
      return 'null'
    }
    if (typeof value === 'object') {
      const pairs = Object.keys(value).sort()
        .map(key => JSON.stringify(key) + ':' + this.jsonSerialize(value[key]))
      return '{' + pairs.join(',') + '}'
    }

    // regular JSON.stringify
    return JSON.stringify(value)
  }
}

// ======================
// RUN ALL THE TEST CASES
// ======================
console.log('Starting TypeScript tests ...')
console.log('Node Version: ' + process.version)
console.log('')

const files: string[] = JSON.parse(readFileSync(path.join(BASE_PATH, '_manifest.json'), 'utf8'))
files.forEach(file => TestPreJsPy.testFile(file))

console.log('')
console.log('Done.')
