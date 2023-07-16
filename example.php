<?php

include "./src/php/PreJsPy.php";

function run_example(string $expr) {
    $p = new PreJsPy();
    echo json_encode($p->Parse($expr), JSON_PRETTY_PRINT);
}

function main() {
    run_example('"Hello world"');
}

main();