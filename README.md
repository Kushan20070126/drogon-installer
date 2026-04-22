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
python3 install.py --help
```

### Install Drogon

```bash
python3 install.py install
python3 install.py install --only-deps
python3 install.py install --skip-build
python3 install.py install --verbose
```

### Create Project

```bash
python3 install.py create myapp
```

### Build Release Artifacts

```bash
# Build host-compatible release artifacts into ./release
python3 install.py release --version v1 --output-dir ./release

# Build only Linux deb package
python3 install.py release --version v1 --targets deb --output-dir ./release
```

## GitHub Actions Release Automation

- Workflow file: `.github/workflows/release.yml`
- Trigger on push to `main`, tag push like `v1`, or manual `workflow_dispatch`.
- Builds cross-platform artifacts automatically:
  - `DM-<version>.exe` (Windows runner)
  - `DM-<version>.deb` (Linux runner)
  - `DB-<version>.dmg` (macOS runner)
- On tag pushes (`v*`), artifacts are also attached to a GitHub Release.

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
- `release` artifact naming:
  - `DM-v1.exe` (built on Windows)
  - `DM-v1.deb` (built on Linux)
  - `DB-v1.dmg` (built on macOS)
