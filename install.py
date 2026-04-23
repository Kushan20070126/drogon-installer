#!/usr/bin/env python3
"""
CLI for installing Drogon and creating Drogon projects.
Main orchestrator that dispatches to platform-specific scripts.
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
DEFAULT_RELEASE_VERSION = "v1"
MIN_PYTHON_VERSION = (3, 8)


def log(message: str) -> None:
    """Print a standardized log message."""
    print(f"[drogon-installer] {message}")


def warn(message: str) -> None:
    """Print a standardized warning message."""
    print(f"[drogon-installer] WARNING: {message}")


def fail(message: str, exit_code: int = 1) -> NoReturn:
    """Print a standardized error message and exit."""
    print(f"[drogon-installer] ERROR: {message}", file=sys.stderr)
    sys.exit(exit_code)


def run_command(command: list[str], cwd: Path, args: argparse.Namespace) -> None:
    """Run a shell command or print it if --dry-run is enabled."""
    cmd_str = " ".join(command)
    if args.dry_run:
        log(f"[dry-run] Would execute: {cmd_str}")
        return

    if args.verbose:
        log(f"Running command: {cmd_str}")

    try:
        completed = subprocess.run(command, cwd=str(cwd), check=False)
        if completed.returncode != 0:
            fail(
                f"Command failed with exit code {completed.returncode}: {cmd_str}",
                exit_code=completed.returncode,
            )
    except FileNotFoundError as exc:
        fail(f"Command failed to start: {exc}")


def check_environment() -> None:
    """Validate that the minimum environment requirements are met."""
    if sys.version_info < MIN_PYTHON_VERSION:
        fail(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required.")

    missing = []
    for tool in ["git", "cmake"]:
        if shutil.which(tool) is None:
            missing.append(tool)

    # Check for a compiler
    if platform.system() == "Windows":
        if shutil.which("cl.exe") is None and shutil.which("gcc") is None:
            # On Windows, we might not have them in PATH but winget/choco will handle it
            pass
    else:
        if shutil.which("g++") is None and shutil.which("clang++") is None:
            missing.append("a C++ compiler (g++ or clang++)")

    if missing:
        warn(f"Missing recommended tools: {', '.join(missing)}")
        log("The installation script will attempt to install missing dependencies.")


def resolve_install_command(system_name: str, scripts_dir: Path, args: argparse.Namespace) -> tuple[Path, list[str]]:
    """Determine the platform-specific script and arguments."""
    if args.only_deps and args.skip_build:
        fail("Use either --only-deps or --skip-build, not both.")

    script_map = {
        "Linux": ("linux.sh", ["bash"]),
        "Darwin": ("macos.sh", ["bash"]),
        "Windows": ("windows.ps1", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]),
    }

    if system_name not in script_map:
        fail(f"Unsupported operating system: {system_name}", exit_code=2)

    script_name, base_cmd = script_map[system_name]
    script_path = scripts_dir / script_name
    command = base_cmd + [str(script_path)]

    # Map Python flags to script flags
    if system_name == "Windows":
        if args.only_deps: command.append("-OnlyDeps")
        if args.skip_build: command.append("-SkipBuild")
        if args.verbose: command.append("-VerboseMode")
    else:
        if args.only_deps: command.append("--only-deps")
        if args.skip_build: command.append("--skip-build")
        if args.verbose: command.append("--verbose")

    return script_path, command


def handle_install(args: argparse.Namespace) -> None:
    """Handle the 'install' subcommand."""
    check_environment()
    project_root = Path(__file__).resolve().parent
    scripts_dir = project_root / "scripts"
    system_name = platform.system()

    log(f"Detected operating system: {system_name}")
    script_path, command = resolve_install_command(system_name, scripts_dir, args)

    if not script_path.exists():
        fail(f"Installer script not found: {script_path}")

    log(f"Starting install using: {script_path.name}")
    run_command(command, cwd=project_root, args=args)
    log("Install command completed successfully.")


def handle_create(args: argparse.Namespace) -> None:
    """Handle the 'create' subcommand."""
    if not PROJECT_NAME_RE.fullmatch(args.project_name):
        fail("Invalid project name. Use letters, numbers, underscores, or hyphens; must start with a letter.")

    if shutil.which("drogon_ctl") is None:
        fail("drogon_ctl not found in PATH. Please install Drogon first using 'drogon-installer install'.")

    command = ["drogon_ctl", "create", "project", args.project_name]
    log(f"Creating Drogon project: {args.project_name}")
    run_command(command, cwd=Path.cwd(), args=args)
    log(f"Project created successfully: {args.project_name}")


def build_exe(project_root: Path, output_dir: Path, version: str, args: argparse.Namespace) -> Path:
    """Build a Windows executable using PyInstaller."""
    if platform.system() != "Windows":
        fail("Windows .exe builds are supported only on Windows.")

    if shutil.which("pyinstaller") is None:
        fail("pyinstaller is required. Install it with: pip install pyinstaller")

    artifact_name = f"DM-{version}.exe"
    destination = output_dir / artifact_name

    log(f"Building executable: {artifact_name}")
    run_command(
        ["pyinstaller", "--onefile", "--clean", "--name", "drogon-installer", "install.py"],
        cwd=project_root,
        args=args,
    )

    if not args.dry_run:
        source_exe = project_root / "dist" / "drogon-installer.exe"
        if not source_exe.exists():
            fail(f"Expected executable not found: {source_exe}")
        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_exe, destination)

    return destination


def build_deb(project_root: Path, output_dir: Path, version: str, args: argparse.Namespace) -> Path:
    """Build a Debian package."""
    if platform.system() != "Linux":
        fail("Debian package builds are supported only on Linux.")

    if shutil.which("dpkg-deb") is None:
        fail("dpkg-deb is required.")

    artifact_name = f"DM-{version}.deb"
    destination = output_dir / artifact_name

    if args.dry_run:
        log(f"[dry-run] Would build Debian package: {artifact_name}")
        return destination

    # Simple version normalization for Debian
    package_version = version.lstrip("v")
    if not package_version or not package_version[0].isdigit():
        package_version = "1.0.0"

    with tempfile.TemporaryDirectory(prefix="drogon-deb-") as tmpdir:
        pkg_root = Path(tmpdir) / "pkg"
        bin_dir = pkg_root / "usr" / "bin"
        lib_dir = pkg_root / "usr" / "lib" / "drogon-installer"
        scripts_dir = lib_dir / "scripts"
        debian_dir = pkg_root / "DEBIAN"

        for d in [bin_dir, scripts_dir, debian_dir]:
            d.mkdir(parents=True, exist_ok=True)

        shutil.copy2(project_root / "install.py", lib_dir / "install.py")
        for s in ["linux.sh", "macos.sh", "windows.ps1"]:
            shutil.copy2(project_root / "scripts" / s, scripts_dir / s)

        launcher = bin_dir / "drogon-installer"
        launcher.write_text("#!/usr/bin/env bash\nexec python3 /usr/lib/drogon-installer/install.py \"$@\"\n")
        launcher.chmod(0o755)

        control = (
            "Package: drogon-installer\n"
            f"Version: {package_version}\n"
            "Architecture: all\n"
            "Maintainer: Drogon Installer <noreply@example.com>\n"
            "Description: CLI for installing Drogon framework\n"
        )
        (debian_dir / "control").write_text(control)

        run_command(["dpkg-deb", "--build", str(pkg_root), str(destination)], cwd=project_root, args=args)

    return destination


def build_dmg(project_root: Path, output_dir: Path, version: str, args: argparse.Namespace) -> Path:
    """Build a macOS DMG."""
    if platform.system() != "Darwin":
        fail("macOS .dmg builds are supported only on macOS.")

    if shutil.which("pyinstaller") is None or shutil.which("hdiutil") is None:
        fail("pyinstaller and hdiutil are required for DMG builds.")

    artifact_name = f"DM-{version}.dmg"
    destination = output_dir / artifact_name

    log(f"Building DMG: {artifact_name}")
    run_command(
        ["pyinstaller", "--onefile", "--clean", "--name", "drogon-installer", "install.py"],
        cwd=project_root,
        args=args,
    )

    if not args.dry_run:
        source_bin = project_root / "dist" / "drogon-installer"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            shutil.copy2(source_bin, tmp_path / "drogon-installer")
            (tmp_path / "drogon-installer").chmod(0o755)
            run_command(
                ["hdiutil", "create", "-volname", "DrogonInstaller", "-srcfolder", tmpdir, "-ov", "-format", "UDZO", str(destination)],
                cwd=project_root,
                args=args
            )

    return destination


def handle_release(args: argparse.Namespace) -> None:
    """Handle the 'release' subcommand."""
    project_root = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir).resolve()
    version = args.version
    system = platform.system()

    log(f"Targeting release version: {version}")
    output_dir.mkdir(parents=True, exist_ok=True)

    produced = []
    if "exe" in args.targets:
        if system == "Windows":
            produced.append(build_exe(project_root, output_dir, version, args))
        else:
            warn("Skipping .exe; must be on Windows.")

    if "deb" in args.targets:
        if system == "Linux":
            produced.append(build_deb(project_root, output_dir, version, args))
        else:
            warn("Skipping .deb; must be on Linux.")

    if "dmg" in args.targets:
        if system == "Darwin":
            produced.append(build_dmg(project_root, output_dir, version, args))
        else:
            warn("Skipping .dmg; must be on macOS.")

    if produced:
        log("Release artifacts created:")
        for p in produced:
            log(f" - {p}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="drogon-installer", description="Drogon Framework Installer CLI")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Install
    inst_p = subparsers.add_parser("install", help="Install Drogon framework")
    inst_p.add_argument("--only-deps", action="store_true", help="Install only system dependencies")
    inst_p.add_argument("--skip-build", action="store_true", help="Skip building Drogon source")
    inst_p.set_defaults(func=handle_install)

    # Create
    crea_p = subparsers.add_parser("create", help="Create a new Drogon project")
    crea_p.add_argument("project_name", help="Name of the project")
    crea_p.set_defaults(func=handle_create)

    # Release
    rel_p = subparsers.add_parser("release", help="Build release artifacts")
    rel_p.add_argument("--version", default=DEFAULT_RELEASE_VERSION, help="Release version label")
    rel_p.add_argument("--output-dir", default="release", help="Directory for artifacts")
    rel_p.add_argument("--targets", nargs="+", choices=["exe", "deb", "dmg"], default=["exe", "deb", "dmg"], help="Targets to build")
    rel_p.set_defaults(func=handle_release)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
