.PHONY: all check format python pycheck pydeps pyformat typescript tsdeps php phpcheck pyformat phpdeps phpformat

all: python typescript php
check: pycheck tscheck phpcheck
format: pyformat tsformat phpformat


python:
	cd src/py/ && python test.py
pydeps:
	python3 -m pip install mypy black
pycheck:
	cd src/py && python3 -m black --check PreJsPy.py test.py
	cd src/py && python3 -m mypy --strict PreJsPy.py
pyformat:
	cd src/py && python3 -m black PreJsPy.py test.py

typescript:
	cd src/ts/ && yarn ts-node test
tsdeps:
	cd src/ts/ && yarn install --frozen-lockfile
tscheck:
	cd src/ts && yarn ts-standard PreJsPy.ts test.ts
	cd src/ts && yarn tsc --noEmit PreJsPy.ts
tsformat:
	cd src/ts && yarn ts-standard --fix PreJsPy.ts test.ts

php:
	cd src/php && php test.php
phpdeps:
	cd src/php && composer install
phpcheck:
	cd src/php && ./vendor/bin/php-cs-fixer fix --config=.php-cs-fixer.php --allow-risky=yes --format=txt --dry-run --diff
phpformat:
	cd src/php && ./vendor/bin/php-cs-fixer fix --config=.php-cs-fixer.php --allow-risky=yes