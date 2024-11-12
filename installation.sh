#!/bin/bash
# Run `chmod +x installation.sh` to make it executable.
venv_dir=".venv"

if [ -d "$venv_dir" ]; then
    echo "Virtual environment already exists."
else
    echo "Creating virtual environment..."
    python3 -m venv "$venv_dir"
fi
source .venv/bin/activate
pip install --upgrade pip
pip install poetry

if [ -f pyproject.toml ]; then
    echo "pyproject.toml exists."
else
    echo "pyproject.toml does not exist."
    poetry init --no-interaction \
                --name "aws-ec2-automator" \
                --author "Dae-young Kim <dkim1@childrensnational.org>" \
                --license "GPLv3" \
                --python ">=3.8" \
                --dependency "paramiko" \
                --dependency "python-dotenv" \
                --dependency "boto3"
    awk '/readme = "README\.md"/ {print; print "package-mode = false"; next}1'\
        pyproject.toml > pyproject.tmp && mv pyproject.tmp pyproject.toml
fi

poetry install --no-root