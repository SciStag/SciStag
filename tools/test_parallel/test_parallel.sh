#!/bin/bash
CUR_DIR=$( pwd; )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
echo "Moving to project root ${ROOT_DIR}..."
cd ${ROOT_DIR}

poetry run pytest ./scistag/tests -n 8 --dist=loadfile

cd $CUR_DIR