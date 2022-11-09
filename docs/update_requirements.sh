#/bin/bash
poetry run poetry export --with docu -E "full" -f requirements.txt -o ./docs/requirements.txt --without-hashes