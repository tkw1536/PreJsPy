#!/bin/bash
set -e


# If we are on travis, run only tests for specific languages
if [ "$TRAVIS" == "true" ]; then
    if [ ! -z "$TRAVIS_NODE_VERSION" ]; then
        pushd src/js/ && npm test && popd
    fi
    if [ ! -z "$TRAVIS_PYTHON_VERSION" ]; then
        pushd src/py/ && python setup.py test && popd
    fi
# Else we are local and run both tests
else
    pushd src/js/ && npm test && popd
    pushd src/py/ && python setup.py test && popd
fi
