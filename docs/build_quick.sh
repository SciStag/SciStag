#!/bin/bash
# Builds the documentation, without removing old garbage
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Remove garbage
echo "Building HTML documentation"
sphinx-build ${SCRIPT_DIR}/source/ ${SCRIPT_DIR}/source/_build/