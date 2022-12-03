#/bin/bash
poetry run poetry export --with docu -E "common" -f requirements.txt -o ./docs/requirements.txt --without-hashes