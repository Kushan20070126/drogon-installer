#!/usr/bin/env bash

set -euo pipefail

log() {
  echo "[macos] $1"
}

fail() {
  echo "[macos] ERROR: $1" >&2
  exit 1
}

command -v brew >/dev/null 2>&1 || fail "Homebrew is required. Install it from https://brew.sh/"

BUILD_ROOT="${BUILD_ROOT:-$HOME/.cache/drogon-installer}"
SOURCE_DIR="$BUILD_ROOT/drogon"
BUILD_DIR="$SOURCE_DIR/build"

log "Updating Homebrew metadata..."
brew update

log "Installing build dependencies..."
brew install git cmake openssl

mkdir -p "$BUILD_ROOT"

if [ -d "$SOURCE_DIR/.git" ]; then
  log "Existing Drogon source found. Updating repository..."
  git -C "$SOURCE_DIR" fetch --tags --prune
  git -C "$SOURCE_DIR" pull --ff-only
else
  log "Cloning Drogon repository..."
  git clone https://github.com/drogonframework/drogon.git "$SOURCE_DIR"
fi

log "Initializing git submodules..."
git -C "$SOURCE_DIR" submodule update --init --recursive

log "Configuring build with CMake..."
mkdir -p "$BUILD_DIR"
cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release

CPU_COUNT="$(sysctl -n hw.ncpu || echo 2)"
log "Building Drogon with $CPU_COUNT parallel jobs..."
cmake --build "$BUILD_DIR" -j "$CPU_COUNT"

log "Installing Drogon globally..."
sudo cmake --install "$BUILD_DIR"

log "Drogon installation finished successfully."
