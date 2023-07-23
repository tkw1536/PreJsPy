import { readFileSync } from 'fs'
import path from 'path'
import { PreJsPy } from './PreJsPy'
import type { Expression, PartialConfig } from './PreJsPy'

interface TestCase {
  config: PartialConfig
  input: string
  output?: Expression
  error?: string
  message: string
}

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
class TestPreJsPy {
  private static readonly BASE_PATH = path.join(__dirname, '..', '..', 'tests')

  /**
   * Parses a json file from the tests directory
   * @param filename  name of file to read
   * @returns
   */
  static parseJSONFile (filename: string): any {
    return JSON.parse(readFileSync(path.join(this.BASE_PATH, filename), 'utf8'))
  }

  /**
   * Runs all test cases from a given file.
   * @param fn
   */
  static testFile (fn: string, N: number): void {
    process.stdout.write('Running tests from ' + fn + ' ')

    // read all the tests
    const tests: TestCase[] = this.parseJSONFile(fn)

    // Create a new PreJSPy instance.
    const p = new PreJsPy()

    // and run all the test cases.
    let total = 0.0
    tests.forEach((t) => { total += this.runSingleFile(p, t, N) })

    console.log(' OK (' + total.toFixed(10) + 'ms)')
  }

  /**
  * Runs a single test case.
  *
  * @param instance instance to test on. *
  * @param config Configuration to apply to PreJsPy instance
  *
  *
  * @param inp Input to parse.
  *
  * @param out Expected output.
  *
  * @param message Message of test case.
  */
  private static runSingleFile (instance: PreJsPy, test: TestCase, N: number): number {
    instance.SetConfig(this.parseJSONFile('_config.json')) // reset the config to default
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

    // do benchmarking!
    let bench = 0.0
    const input = test.input
    for (let i = 0; i < N; i++) {
      const start = performance.now()
      instance.TryParse(input)
      const end = performance.now()

      bench += (end - start) / 1000
    }
    return bench / N
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

const files: string[] = TestPreJsPy.parseJSONFile('_manifest.json')
files.forEach(file => TestPreJsPy.testFile(file, 10_000))

console.log('')
console.log('Done.')
