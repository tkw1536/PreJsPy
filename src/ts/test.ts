import assert = require('assert')
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

/**
 * Runs all test cases from a given file.
 * @param fn
 */
function loadFile (fn: string): void {
  console.log('Running tests from ' + fn)

  // read all the tests
  const tests: TestCase[] = JSON.parse(readFileSync(path.join(BASE_PATH, fn), 'utf8'))

  // Create a new PreJSPy instance.
  const p = new PreJsPy()

  // and run all the test cases.
  tests.forEach((t) => runSingleFile(p, t))

  console.log('.\n')
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
function runSingleFile (instance: PreJsPy<any, string, string>, test: TestCase): void {
  instance.SetConfig(PreJsPy.GetDefaultConfig()) // reset the config to default
  instance.SetConfig(test.config) // set config
  assert.deepEqual(instance.Parse(test.input), test.output, test.message)
}

// ======================
// RUN ALL THE TEST CASES
// ======================
console.log('Starting TypeScript tests ...\n')

// SYMBOLIC
loadFile('constant_symbolic.json')
loadFile('identifier_symbolic.json')

// LITERALS
loadFile('number_literals.json')
loadFile('string_literals.json')
loadFile('array_literals.json')

// OPERATORS
loadFile('unary_ops.json')
loadFile('binary_ops.json')

// CALLS & COMPOUNDS
loadFile('call.json')
loadFile('compound.json')

// PRECEDENCES
loadFile('precedence.json')

console.log('OK')
