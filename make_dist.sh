#!/bin/bash

# make distribution packages for PhyPraKit (pyhton3)


# pip executables to try out
PIP_EXEC="pip3"
PY_EXEC="python3"

echo "Using pip executable '$PIP_EXEC' ..."

# Build the source distribution
$PY_EXEC setup.py sdist
#$PY_EXEC setup.py bdist_wheel
$PY_EXEC setup.py bdist_wheel --universal # py2 and py3

# Install using pip
#$PIP_EXEC install PhyPraKit --no-index --find-links dist
