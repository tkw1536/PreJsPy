var assert = require("assert");

var fs = require("fs");
var path = require("path");
var parse = require("./PreJsPy.js");

var BASE_PATH = path.join(__dirname, '..', '..', 'tests');

/**
 * Runs all test cases from a given file.
 * @param fn
 */
function load_file(fn){

    console.log("Running tests from "+fn);

    // read all the tests
    var tests = JSON.parse(fs.readFileSync(path.join(BASE_PATH, fn), 'utf8'));

    // Create a new PreJSPy instance.
    var p = new parse.PreJsPy()

    // and run all the test cases.
    tests.forEach(function(t){
        run_single_case(p, t["input"], t["output"], t["message"]);
    });

    console.log(".\n");
}

/**
 * Runs a single test case.
 *
 * @param instance PreJsPy instance to test on.
 * @type instance
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
function run_single_case(instance, inp, out, message){
    assert.deepEqual(instance.parse(inp), out, message);
}


// ======================
// RUN ALL THE TEST CASES
// ======================
console.log("Starting JavaScript tests ...\n");

// SYMBOLIC
load_file("constant_symbolic.json");
load_file("identifier_symbolic.json");

// LITERALS
load_file("number_literals.json");
load_file("string_literals.json");
load_file("array_literals.json");

// OPERATORS
load_file("unary_ops.json");
load_file("binary_ops.json");

// CALLS & COMPOUNDS
load_file("call.json");
load_file("compound.json");

// PRECEDENCES
load_file("precedence.json");

console.log("OK");
