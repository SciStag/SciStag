#!/bin/bash
CUR_DIR=$( pwd; )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
echo "Moving to project root ${SCRIPT_DIR}..."
cd $SCRIPT_DIR
echo "Testing wheel installation and unit tests..."
poetry env remove --all
poetry env use python3.9
poetry lock
poetry install --sync
source ./run_test.sh
cd $CUR_DIR