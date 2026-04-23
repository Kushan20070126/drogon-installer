# drogon-installer Installation Guide

This guide explains how to install and use `drogon-installer` on Linux, macOS, and Windows.

## 1) Install From Source (Recommended for Contributors)

### Prerequisites

- Python 3.8+ available as `python3` (Linux/macOS) or `python` (Windows)
- Git

### Steps

```bash
git clone https://github.com/Kushan20070126/drogon-installer.git
cd drogon-installer
python3 install.py --help
```

On Windows PowerShell:

```powershell
git clone https://github.com/Kushan20070126/drogon-installer.git
cd drogon-installer
python install.py --help
```

## 2) Optional: Make `drogon-installer` a Global Command

Linux/macOS:

```bash
chmod +x install.py
sudo ln -sf "$(pwd)/install.py" /usr/local/bin/drogon-installer
drogon-installer --help
```

Windows (PowerShell, from repo root):

```powershell
python install.py --help
```

You can create a local alias if desired:

```powershell
Set-Alias drogon-installer python
# Use as: drogon-installer install.py install
```

## 3) Install Using Release Packages

Release artifacts are published in GitHub Releases:
- `DM-<version>.deb` for Linux
- `DM-<version>.exe` for Windows
- `DB-<version>.dmg` for macOS

### Linux (`.deb`)

```bash
sudo apt install ./DM-v1.deb
drogon-installer --help
```

### Windows (`.exe`)

From PowerShell in the folder containing the file:


```powershell
.\DM-v1.exe --help
.\DM-v1.exe install
```

### macOS (`.dmg`)

1. Open `DB-v1.dmg`.
2. Copy `drogon-installer` binary to a local path (example: `/usr/local/bin`).
3. Ensure executable permission:

```bash
chmod +x /usr/local/bin/drogon-installer
drogon-installer --help
```

## 4) First Commands to Run

Install Drogon:

```bash
drogon-installer install
```

Install only dependencies:

```bash
drogon-installer install --only-deps
```

Create a new Drogon project:

```bash
drogon-installer create myapp
```

## 5) Troubleshooting

- `drogon_ctl not found`: run `drogon-installer install` first, then open a new terminal.
- Linux/macOS permission issues: use `sudo` where required.
- Windows `vcpkg not found`: install vcpkg and add it to `PATH`, then rerun install.
- Command not found after install: verify your `PATH` includes `/usr/local/bin` (Linux/macOS) or the binary location.
