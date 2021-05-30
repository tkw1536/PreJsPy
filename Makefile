.PHONY: python node all

all: python node

python:
	cd src/py/ && python setup.py test
node:
	cd src/js/ && npm test
