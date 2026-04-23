# Drogon Ecosystem CLI (`drogon`)

A production-ready package manager for the Drogon C++ Framework. Behaves like `npm` for a seamless developer experience.

## Installation

### One-line Install (Linux/macOS)
```bash
curl -sS https://raw.githubusercontent.com/Kushan20070126/drogon-installer/main/bootstrap.sh | bash
```

### Local Setup
```bash
./bootstrap.sh
```

## Usage

### 1. Environment Health Check
```bash
drogon doctor
```

### 2. Install Drogon & Dependencies
```bash
drogon install
drogon install --only-deps
drogon install --skip-build
```
*Supports `apt`, `dnf`, `pacman` (Linux), `brew` (macOS), and `winget` (Windows).*

### 3. Create a New Project
```bash
drogon create my_app
cd my_app
```

### 4. Initialize `drogon.json`
```bash
drogon init
```

### 5. Run Scripts
Scripts are defined in `drogon.json`:
```json
{
  "scripts": {
    "build": "cmake -B build && cmake --build build",
    "dev": "drogon run build && ./build/my_app"
  }
}
```
Execute them:
```bash
drogon run build
drogon run dev
```

## Architecture
- **Home Directory**: `~/.drogon/`
- **Cache**: `~/.drogon/cache/` (Drogon source and builds)
- **Configuration**: `drogon.json` (Per-project scripts and metadata)
- **Logs**: `~/.drogon/logs/`

## Platform Support
- **Linux**: Debian/Ubuntu, Fedora/RHEL, Arch Linux.
- **macOS**: via Homebrew.
- **Windows**: via Winget and Visual Studio Build Tools.
