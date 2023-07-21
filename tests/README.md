# Test Cases

This directory contains test cases for PreJsPy.
The files are are shared between languages.

A manifest of all files can be found in `_manifest.json`.
This file is automatically read by all the testing code to find all other test files.

Each file is encoded in json, and contains an array of test cases.
Each test case looks like (typescript syntax):

```typescript
interface TestCase {
  // the configuration to apply for the testcase
  // applied on top of the default config
  config: PreJsPy.PartialConfig

  // the input string
  input: string
  
  // the expected output or the error message
  // the error should only be the error string
  // exactly one should be provided
  output?: PreJsPy.Expression
  error?: string

  // test case message (for debugging)
  message: string
}
```

The default configuration to be applied before each test case can be found in `_config.json`.
FIXME: Do this!