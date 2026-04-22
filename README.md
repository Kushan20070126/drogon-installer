# drogon-installer

`drogon-installer` is a simple, reproducible cross-platform CLI installer for the
[Drogon C++ web framework](https://github.com/drogonframework/drogon).

It detects your operating system and runs the correct install script for:
- Linux (Debian/Ubuntu with `apt`)
- macOS (with Homebrew)
- Windows (with PowerShell + vcpkg)

## Project Structure

```text
drogon-installer/
  install.py
  scripts/
    linux.sh
    macos.sh
    windows.ps1
  README.md
```

## Usage

From the project root:

```bash
python3 install.py
```

## What the Installer Does

### Linux (`scripts/linux.sh`)
- Installs dependencies with `apt`: `git`, `cmake`, `g++`, `libssl-dev`, `uuid-dev`
- Clones (or updates) the Drogon repository
- Initializes submodules
- Builds Drogon with CMake
- Installs Drogon globally

### macOS (`scripts/macos.sh`)
- Installs dependencies with Homebrew: `git`, `cmake`, `openssl`
- Clones (or updates) the Drogon repository
- Initializes submodules
- Builds Drogon with CMake
- Installs Drogon globally

### Windows (`scripts/windows.ps1`)
- Checks for `vcpkg` in `PATH`
- If missing, prints setup instructions and exits with an error
- Installs Drogon via `vcpkg install drogon:x64-windows` (or uses `VCPKG_DEFAULT_TRIPLET`)

## Notes

- The Python launcher uses only the standard library.
- Installation scripts print step-by-step logs and fail fast on errors.
- Linux and macOS installers require `sudo` for global installation.
