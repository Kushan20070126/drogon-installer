#!/usr/bin/env bash

set -euo pipefail

ONLY_DEPS=0
SKIP_BUILD=0
VERBOSE=0

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
      echo "[linux] ERROR: Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ "$VERBOSE" -eq 1 ]; then
  set -x
fi

log() {
  echo "[linux] $1"
}

fail() {
  echo "[linux] ERROR: $1" >&2
  exit 1
}

command -v apt-get >/dev/null 2>&1 || fail "apt-get not found. This installer supports Debian/Ubuntu Linux."

BUILD_ROOT="${BUILD_ROOT:-$HOME/.cache/drogon-installer}"
SOURCE_DIR="$BUILD_ROOT/drogon"
BUILD_DIR="$SOURCE_DIR/build"

log "Updating apt package index..."
sudo apt-get update

log "Installing build dependencies..."
sudo apt-get install -y git cmake g++ libssl-dev uuid-dev

if [ "$ONLY_DEPS" -eq 1 ]; then
  log "Dependency-only mode enabled. Skipping repository clone and build."
  exit 0
fi

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

if [ "$SKIP_BUILD" -eq 1 ]; then
  log "Skip-build mode enabled. Dependencies and source setup completed."
  exit 0
fi

log "Configuring build with CMake..."
mkdir -p "$BUILD_DIR"
cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release

CPU_COUNT="$(getconf _NPROCESSORS_ONLN || echo 2)"
log "Building Drogon with $CPU_COUNT parallel jobs..."
cmake --build "$BUILD_DIR" -j "$CPU_COUNT"

log "Installing Drogon globally..."
sudo cmake --install "$BUILD_DIR"

log "Drogon installation finished successfully."
