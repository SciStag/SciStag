#/bin/bash
poetry run poetry export --with docu -f requirements.txt -o ./docs/requirements.txt --without-hashes