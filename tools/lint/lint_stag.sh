#!/bin/bash
# Executes the linter, logs the linting score and creates a badge to show the current score in the main readme
CUR_DIR=$( pwd; )
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
echo "Moving to project root ${ROOT_DIR}..."
cd $ROOT_DIR
rm -rf ./pylint
rm -f docs/source/generated/pylint.svg
mkdir ./docs/source/generated
mkdir ./pylint
pylint --output-format=text ./scistag | tee ./pylint/pylint.log || pylint-exit $?
PYLINT_SCORE=$(sed -n 's/^Your code has been rated at \([-0-9.]*\)\/.*/\1/p' ./pylint/pylint.log)
anybadge --label=Pylint --file=docs/source/generated/pylint.svg --value=$PYLINT_SCORE 2=red 4=orange 8=yellow 10=green
echo "Pylint score is $PYLINT_SCORE"
cd $CUR_DIR
echo "Moving to original directory ${CUR_DIR}..."
