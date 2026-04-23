#!/usr/bin/env bash

set -euo pipefail

log() { echo "[bootstrap] $1"; }
fail() { echo "[bootstrap] ERROR: $1" >&2; exit 1; }

log "Checking for python3..."
command -v python3 >/dev/null 2>&1 || fail "python3 is required."

log "Checking for pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
  log "pip not found. Attempting to install pip..."
  curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi

log "Installing drogon CLI globally via pip..."
# Installing from current directory
python3 -m pip install . --break-system-packages 2>/dev/null || python3 -m pip install .

log "Installation complete!"
log "Verifying 'drogon' command..."

if command -v drogon >/dev/null 2>&1; then
  log "✔ 'drogon' command is now globally available."
  drogon doctor
else
  warn "'drogon' command not found in PATH immediately."
  warn "You may need to restart your terminal or add your Python script directory to PATH."
  # Try running directly
  python3 -m drogon doctor
fi

log "Bootstrap finished!"
