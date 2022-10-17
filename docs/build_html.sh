#!/bin/bash
# Builds the documentation
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Remove garbage
echo "Removing old build directory"
rm -rf ${SCRIPT_DIR}/source/_build
rm -rf ${SCRIPT_DIR}/source/_autosummary
echo "Building HTML documentation"
sphinx-build ${SCRIPT_DIR}/source/ ${SCRIPT_DIR}/source/_build/