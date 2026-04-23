#!/usr/bin/env bash

set -euo pipefail

ONLY_DEPS=0
SKIP_BUILD=0
VERBOSE=0

# Standardized flag parsing
for arg in "$@"; do
  case "$arg" in
    --only-deps)
      ONLY_DEPS=1
      ;;
    --skip-build)
      SKIP_BUILD=1
      ;;
    --verbose)
      VERBOSE=1
      ;;
    *)
      echo "[macos] ERROR: Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ "$VERBOSE" -eq 1 ]; then
  set -x
fi

log() {
  echo "[macos] $1"
}

fail() {
  echo "[macos] ERROR: $1" >&2
  exit 1
}

# Ensure Homebrew exists
command -v brew >/dev/null 2>&1 || fail "Homebrew not found. Install it from https://brew.sh/"

BUILD_ROOT="${BUILD_ROOT:-$HOME/.cache/drogon-installer}"
SOURCE_DIR="$BUILD_ROOT/drogon"
BUILD_DIR="$SOURCE_DIR/build"

log "Updating Homebrew..."
brew update

log "Installing dependencies (git, cmake, openssl)..."
brew install git cmake openssl

if [ "$ONLY_DEPS" -eq 1 ]; then
  log "Dependency-only mode. Done."
  exit 0
fi

mkdir -p "$BUILD_ROOT"

if [ -d "$SOURCE_DIR/.git" ]; then
  log "Drogon source exists. Updating..."
  git -C "$SOURCE_DIR" fetch --all
  git -C "$SOURCE_DIR" reset --hard origin/master || git -C "$SOURCE_DIR" reset --hard origin/main
else
  log "Cloning Drogon repository..."
  git clone https://github.com/drogonframework/drogon.git "$SOURCE_DIR"
fi

log "Updating submodules..."
git -C "$SOURCE_DIR" submodule update --init --recursive

if [ "$SKIP_BUILD" -eq 1 ]; then
  log "Skip-build mode. Done."
  exit 0
fi

log "Configuring build..."
mkdir -p "$BUILD_DIR"
cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release

CPU_COUNT="$(sysctl -n hw.ncpu || echo 2)"
log "Building with $CPU_COUNT jobs..."
cmake --build "$BUILD_DIR" -j "$CPU_COUNT"

log "Installing globally..."
sudo cmake --install "$BUILD_DIR"

log "Drogon installation complete."
