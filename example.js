var PreJsPy = require("./src/ts/PreJsPy");

/**
 * Parses a single expression and prints the result to stdout.
 * @param {string} expr Expression to parse.
 */
function run_example(expr){
    var p = new PreJsPy.PreJsPy();
    console.log(p.Parse(expr));
}

function main(){
    run_example('"Hello world"');
}

main();