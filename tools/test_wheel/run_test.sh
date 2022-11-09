#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR=$(realpath ${SCRIPT_DIR}"/../..";)
ENV_NAME=${ROOT_DIR}"/scistag/tests/.env"
export $(grep -v '^#' ${ENV_NAME} | xargs)
export SCISTAG_FULL_TEST=1
poetry run pytest --pyargs scistag.tests
unset $(grep -v '^#' ${ENV_NAME} | sed -E 's/(.*)=.*/\1/' | xargs)
