#!/bin/bash
set -e


# If we are on travis, run only tests for specific languages
if [ "$TRAVIS" == "true" ]; then
    if [ ! -z "$TRAVIS_NODE_VERSION" ]; then
        node src/js/test.js
    fi
    if [ ! -z "$TRAVIS_PYTHON_VERSION" ]; then
        python src/py/test.py
    fi
# Else we are local and run both tests
else
    node src/js/test.js
    python src/py/test.py
fi
