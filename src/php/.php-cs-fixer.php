<?php

require 'vendor/autoload.php';

$finder = PhpCsFixer\Finder::create()
    ->exclude('vendor')
    ->in(__DIR__)
;

$config = new PhpCsFixer\Config();
return $config->setRules([
        '@Symfony' => true,
        '@Symfony:risky' => true,

        'array_indentation' => true,
        'array_syntax' => ['syntax' => 'short'],
        'comment_to_phpdoc' => [],
        'declare_strict_types' => true,
        'no_superfluous_elseif' => true,
        'psr_autoloading' => false,
        'strict_comparison' => true,
    ])
    ->setFinder($finder)
;