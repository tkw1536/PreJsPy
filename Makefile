.PHONY: all python pycheck pydeps typescript tsdeps php phpcheck phpdeps 

all: python typescript php


python:
	cd src/py/ && python test.py
pydeps:
	python3 -m pip install mypy black
pycheck:
	cd src/py && python3 -m black --check PreJsPy.py test.py
	cd src/py && python3 -m mypy --strict PreJsPy.py

typescript:
	cd src/ts/ && yarn ts-node test
tsdeps:
	cd src/ts/ && yarn install --frozen-lockfile
tscheck:
	cd src/ts && yarn ts-standard PreJsPy.ts test.ts
	cd src/ts && yarn tsc --noEmit PreJsPy.ts

php:
	cd src/php && php test.php
phpdeps:
phpcheck: