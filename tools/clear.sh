#!/bin/bash
# Builds the documentation, without removing old garbage
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Remove garbage
echo "Clearing documentation and coverage"
rm -rf ${SCRIPT_DIR}/../_autosummary || true
rm -rf ${SCRIPT_DIR}/../htmlcov || true
rm -rf ${SCRIPT_DIR}/../logs || true
rm -rf ${SCRIPT_DIR}/../temp || true
rm -rf ${SCRIPT_DIR}/../.stscache || true
rm -rf ${SCRIPT_DIR}/../.pytest_cache || true
rm -rf ${SCRIPT_DIR}/../.dist || true