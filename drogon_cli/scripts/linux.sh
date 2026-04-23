#!/usr/bin/env bash

set -euo pipefail

ONLY_DEPS=0
SKIP_BUILD=0
VERBOSE=0

for arg in "$@"; do
  case "$arg" in
    --only-deps) ONLY_DEPS=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
    --verbose) VERBOSE=1 ;;
  esac
done

if [ "$VERBOSE" -eq 1 ]; then set -x; fi

log() { echo "[linux] $1"; }
fail() { echo "[linux] ERROR: $1" >&2; exit 1; }

# Detect Package Manager
if command -v apt-get >/dev/null; then
  PKG_MGR="apt"
  INSTALL_CMD="sudo apt-get install -y git cmake g++ libssl-dev uuid-dev"
  UPDATE_CMD="sudo apt-get update"
elif command -v dnf >/dev/null; then
  PKG_MGR="dnf"
  INSTALL_CMD="sudo dnf install -y git cmake gcc-c++ openssl-devel libuuid-devel"
  UPDATE_CMD="sudo dnf check-update || true"
elif command -v pacman >/dev/null; then
  PKG_MGR="pacman"
  INSTALL_CMD="sudo pacman -S --noconfirm git cmake gcc openssl util-linux"
  UPDATE_CMD="sudo pacman -Sy"
else
  fail "Unsupported package manager (apt, dnf, or pacman required)."
fi

log "Detected package manager: $PKG_MGR"
log "Updating package index..."
$UPDATE_CMD

log "Installing dependencies..."
$INSTALL_CMD

if [ "$ONLY_DEPS" -eq 1 ]; then exit 0; fi

BUILD_ROOT="${BUILD_ROOT:-$HOME/.drogon/cache}"
SOURCE_DIR="$BUILD_ROOT/drogon"
BUILD_DIR="$SOURCE_DIR/build"

mkdir -p "$BUILD_ROOT"

if [ -d "$SOURCE_DIR/.git" ]; then
  log "Updating source..."
  git -C "$SOURCE_DIR" fetch --all
  git -C "$SOURCE_DIR" reset --hard origin/master || git -C "$SOURCE_DIR" reset --hard origin/main
else
  log "Cloning Drogon..."
  git clone https://github.com/drogonframework/drogon.git "$SOURCE_DIR"
fi

git -C "$SOURCE_DIR" submodule update --init --recursive

if [ "$SKIP_BUILD" -eq 1 ]; then exit 0; fi

log "Building..."
cmake -S "$SOURCE_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j "$(nproc || echo 2)"
sudo cmake --install "$BUILD_DIR"

log "Done."
