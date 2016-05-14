var PreJsPy = require("./src/js/PreJsPy.js");


/**
 * Parses a single expression and prints the result to stdout.
 * @param {string} expr Expression to parse.
 */
function run_example(expr){
    var p = new PreJsPy.PreJsPy();
    console.log(p.parse(expr));
}

/**
 * Utility function to create a test case.
 *
 * @param inp {string} Input to use.
 * @param msg {string} Message for test case.
 */
function make_testcase(inp, msg) {
    var p = PreJsPy.PreJsPy();
    var out = p.parse(inp);

    console.log('{\n    "input": '+JSON.stringify(inp)+',\n    "output": '+JSON.stringify(out)+',\n    "message": '+JSON.stringify(msg)+'\n}');
}


function main(){
    run_example('"Hello world"');
}

main();