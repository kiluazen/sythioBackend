#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements without cache and with no binary for problematic packages
pip install --no-cache-dir --upgrade -r requirements.txt

echo "Build completed successfully!" 