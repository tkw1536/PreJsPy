# ------------------------------ #
# All of the supported languages #
# ------------------------------ #
LANGS = py ts php

# run tests
all: test

# @lang/deps install dependencies for all testing code
DEPS = $(patsubst %, @%/deps, $(LANGS))
deps: $(DEPS)

# @lang/test runs all of the tests
TEST = $(patsubst %, @%/test, $(LANGS))
test: $(TEST)

# @lang/format formats the source files
FORMAT = $(patsubst %, @%/format, $(LANGS))
format: $(FORMAT)

# @lang/lint is like format, but only checks if formatting is needed
LINT = $(patsubst %, @%/lint, $(LANGS))
lint: $(LINT)

# @lang/types runs type checking for the given language
TYPES = $(patsubst %, @%/types, $(LANGS))
types: $(TYPES)

# **all** targets are phony (don't tell anyone)
.PHONY: all deps $(DEPS) test $(TEST) format $(FORMAT) lint $(LINT) types $(TYPES)

# ------------------------------ #
# Python                         #
# ------------------------------ #

@py/deps:
	python3 -m pip install mypy black
@py/test:
	cd src/py/ && python test.py
@py/format:
	cd src/py && python3 -m black PreJsPy.py test.py
@py/lint:
	cd src/py && python3 -m black --check PreJsPy.py test.py
@py/types:
	cd src/py && python3 -m mypy --strict PreJsPy.py

# ------------------------------ #
# TypeScript                     #
# ------------------------------ #

@ts/deps:
	cd src/ts && yarn install --frozen-lockfile
@ts/test:
	cd src/ts && yarn ts-node test
@ts/format:
	cd src/ts && yarn ts-standard --fix PreJsPy.ts test.ts
@ts/lint:
	cd src/ts && yarn ts-standard PreJsPy.ts test.ts
@ts/types:
	cd src/ts && yarn tsc --noEmit PreJsPy.ts

# ------------------------------ #
# PHP                            #
# ------------------------------ #

@php/deps:
	cd src/php && composer install
@php/test:
	cd src/php && php test.php
@php/format:
	cd src/php && ./vendor/bin/php-cs-fixer fix --config=.php-cs-fixer.php --allow-risky=yes
@php/lint:
	cd src/php && ./vendor/bin/php-cs-fixer fix --config=.php-cs-fixer.php --allow-risky=yes --format=txt --dry-run --verbose --diff
@php/types:
	echo "Not implemented"
