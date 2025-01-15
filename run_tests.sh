#!/usr/bin/env bash

set -euxo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
VENV_LOCATION="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_LOCATION" ]; then
  echo "No virtualenv detected..."
  echo "Creating one at $VENV_LOCATION..."
  python3 -m venv $VENV_LOCATION
  source "$VENV_LOCATION/bin/activate"

  # old pip versions may not be able to read pyproject.toml
  pip install --upgrade pip

  pip install -e "$SCRIPT_DIR/[dev]"
  echo "Virtualenv setup complete !"
else
  echo "Using virtualenv at $VENV_LOCATION..."
  source "$VENV_LOCATION/bin/activate"
fi

python3 -m pytest --log-cli-level=INFO "$@"