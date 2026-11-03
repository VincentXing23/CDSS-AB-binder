#!/bin/sh
# Use the Python interpreter from the prepared locked environment.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "${PYTHON:-python3}" "$ROOT/cdss-ab/scripts/reproduce_snapshot.py" "$@"
