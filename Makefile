.PHONY: all python pytestdeps pycheck node

all: python node


python:
	cd src/py/ && python setup.py test
pytestdeps:
	python -m pip install mypy
pycheck:
	cd src/py/ && python -m mypy --strict PreJsPy.py

node:
	cd src/js/ && npm test
