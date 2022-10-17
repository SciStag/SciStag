#!/bin/bash
# Builds the wheel to prepare it for the next release
CUR_DIR=$( pwd; )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
rm -rf ./dist
echo "Moving to project root ${ROOT_DIR}..."
cd $ROOT_DIR
poetry build
cd $CUR_DIR
echo "Moving to original directory ${CUR_DIR}..."
