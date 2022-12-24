#!/bin/bash
# Creates a coverage report as html. Execute in project root as workdir
CUR_DIR=$( pwd; )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
echo "Moving to project root ${ROOT_DIR}..."
cd $ROOT_DIR
echo "Executing unit tests and creating coverage report..."
export TEST_RELEASE=1
export TEST_GIT_INTEGRITY=1
poetry run pytest --cov=. --dist=loadfile -n auto ./scistag/tests
# poetry run coverage run -m pytest ./scistag/tests
# poetry run coverage report -m
poetry run coverage html
cd $CUR_DIR
echo "Moving to original directory ${CUR_DIR}..."
