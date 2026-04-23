#!/usr/bin/env bash

set -euo pipefail

log() { echo "[bootstrap] $1"; }
fail() { echo "[bootstrap] ERROR: $1" >&2; exit 1; }

log "Checking for python3..."
command -v python3 >/dev/null 2>&1 || fail "python3 is required."

# Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
  log "uv not found. Installing uv (fast Python package manager)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source uv for the current session
  export PATH="$HOME/.local/bin:$PATH"
fi

log "Installing drogon CLI via uv..."

# Method: uv tool install
# This installs the CLI into an isolated env but puts the 'drogon' binary in ~/.local/bin
if [ -d ".git" ] || [ -f "pyproject.toml" ]; then
    log "Installing from local source..."
    uv tool install . --force
else
    log "Installing from GitHub repository..."
    uv tool install git+https://github.com/Kushan20070126/drogon-installer.git --force
fi

log "Installation complete!"
log "Verifying 'drogon' command..."

# Ensure ~/.local/bin is in PATH for this session
export PATH="$HOME/.local/bin:$PATH"

if command -v drogon >/dev/null 2>&1; then
  log "✔ 'drogon' command is now globally available."
  drogon doctor
else
  warn "'drogon' command not found in PATH immediately."
  log "Please add ~/.local/bin to your PATH by adding this to your ~/.bashrc:"
  echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

log "Bootstrap finished! Try running: drogon doctor"
