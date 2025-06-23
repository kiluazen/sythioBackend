#!/usr/bin/env bash
# Exit on error
set -o errexit

export CARGO_HOME="$HOME/.cargo"
export RUSTUP_HOME="$HOME/.rustup"
mkdir -p "$CARGO_HOME" "$RUSTUP_HOME"

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements without cache and with no binary for problematic packages
pip install --prefer-binary --no-cache-dir --upgrade -r requirements.txt

echo "Build completed successfully!" 