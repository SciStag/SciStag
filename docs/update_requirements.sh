#/bin/bash
poetry run poetry export -E docubuild -f requirements.txt -o ./docs/requirements.txt --without-hashes