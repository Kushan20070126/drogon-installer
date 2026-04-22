#!/usr/bin/env python3
"""CLI for installing Drogon and creating Drogon projects."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
DEFAULT_RELEASE_VERSION = "v1"


def log(message: str) -> None:
    print(f"[drogon-installer] {message}")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"[drogon-installer] ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def run_command(command: list[str], cwd: Path, verbose: bool) -> None:
    if verbose:
        log(f"Running command: {' '.join(command)}")
    try:
        completed = subprocess.run(command, cwd=str(cwd), check=False)
    except FileNotFoundError as exc:
        fail(f"Command failed to start: {exc}")
    if completed.returncode != 0:
        fail(
            f"Command failed with exit code {completed.returncode}: {' '.join(command)}",
            exit_code=completed.returncode,
        )


def ensure_command_exists(name: str, message: str) -> None:
    if shutil.which(name) is None:
        fail(message)


def warn(message: str) -> None:
    print(f"[drogon-installer] WARNING: {message}")


def resolve_install_command(system_name: str, scripts_dir: Path, args: argparse.Namespace) -> tuple[Path, list[str]]:
    if args.only_deps and args.skip_build:
        fail("Use either --only-deps or --skip-build, not both.")

    if system_name == "Linux":
        script_path = scripts_dir / "linux.sh"
        command = ["bash", str(script_path)]
        if args.only_deps:
            command.append("--only-deps")
        if args.skip_build:
            command.append("--skip-build")
        if args.verbose:
            command.append("--verbose")
        return script_path, command

    if system_name == "Darwin":
        script_path = scripts_dir / "macos.sh"
        command = ["bash", str(script_path)]
        if args.only_deps:
            command.append("--only-deps")
        if args.skip_build:
            command.append("--skip-build")
        if args.verbose:
            command.append("--verbose")
        return script_path, command

    if system_name == "Windows":
        script_path = scripts_dir / "windows.ps1"
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ]
        if args.only_deps:
            command.append("-OnlyDeps")
        if args.skip_build:
            command.append("-SkipBuild")
        if args.verbose:
            command.append("-VerboseMode")
        return script_path, command

    fail(f"Unsupported operating system: {system_name}", exit_code=2)
    raise RuntimeError("unreachable")


def handle_install(args: argparse.Namespace) -> None:
    project_root = Path(__file__).resolve().parent
    scripts_dir = project_root / "scripts"
    system_name = platform.system()

    log(f"Detected operating system: {system_name}")
    script_path, command = resolve_install_command(system_name, scripts_dir, args)
    if not script_path.exists():
        fail(f"Installer script not found: {script_path}")

    log(f"Starting install using: {script_path.name}")
    run_command(command, cwd=project_root, verbose=args.verbose)
    log("Install command completed successfully.")


def validate_project_name(name: str) -> None:
    if not PROJECT_NAME_RE.fullmatch(name):
        fail("Invalid project name. Use letters, numbers, underscores, or hyphens; must start with a letter.")


def handle_create(args: argparse.Namespace) -> None:
    validate_project_name(args.project_name)
    if shutil.which("drogon_ctl") is None:
        fail("drogon_ctl not found in PATH. Install Drogon first.")

    command = ["drogon_ctl", "create", "project", args.project_name]
    log(f"Creating Drogon project: {args.project_name}")
    run_command(command, cwd=Path.cwd(), verbose=False)
    log(f"Project created successfully: {args.project_name}")


def build_exe(project_root: Path, output_dir: Path, artifact_name: str, verbose: bool) -> Path:
    if platform.system() != "Windows":
        fail("Windows .exe builds are supported only on Windows.")

    ensure_command_exists(
        "pyinstaller",
        "pyinstaller is required for exe builds. Install it with: pip install pyinstaller",
    )

    log("Building executable with PyInstaller...")
    run_command(
        ["pyinstaller", "--onefile", "--clean", "--name", "drogon-installer", "install.py"],
        cwd=project_root,
        verbose=verbose,
    )
    source_exe = project_root / "dist" / "drogon-installer.exe"
    if not source_exe.exists():
        fail(f"Expected executable not found: {source_exe}")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / artifact_name
    shutil.copy2(source_exe, destination)
    log(f"Executable build completed: {destination}")
    return destination


def normalize_debian_version(version: str) -> str:
    # Debian versions should start with a digit. Keep user-friendly release labels for filenames.
    if version and version[0].isdigit():
        return version

    normalized = version.lstrip("vV")
    if normalized and normalized[0].isdigit():
        return normalized

    digits = "".join(ch for ch in version if ch.isdigit() or ch == ".")
    if digits and digits[0].isdigit():
        return digits

    return "1.0.0"


def build_deb(project_root: Path, output_dir: Path, artifact_name: str, release_version: str, verbose: bool) -> Path:
    if platform.system() != "Linux":
        fail("Debian package builds are supported only on Linux.")

    ensure_command_exists("dpkg-deb", "dpkg-deb is required to build a .deb package.")
    ensure_command_exists("python3", "python3 is required to package drogon-installer.")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_deb = output_dir / artifact_name
    package_version = normalize_debian_version(release_version)
    if package_version != release_version:
        warn(f"Using Debian package version '{package_version}' for metadata (derived from '{release_version}').")

    with tempfile.TemporaryDirectory(prefix="drogon-installer-deb-") as tmpdir:
        package_root = Path(tmpdir) / "pkgroot"
        debian_dir = package_root / "DEBIAN"
        bin_dir = package_root / "usr" / "bin"
        lib_dir = package_root / "usr" / "lib" / "drogon-installer"
        scripts_dir = lib_dir / "scripts"

        debian_dir.mkdir(parents=True, exist_ok=True)
        bin_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(project_root / "install.py", lib_dir / "install.py")
        shutil.copy2(project_root / "scripts" / "linux.sh", scripts_dir / "linux.sh")
        shutil.copy2(project_root / "scripts" / "macos.sh", scripts_dir / "macos.sh")
        shutil.copy2(project_root / "scripts" / "windows.ps1", scripts_dir / "windows.ps1")

        launcher = bin_dir / "drogon-installer"
        launcher.write_text(
            "#!/usr/bin/env bash\nexec python3 /usr/lib/drogon-installer/install.py \"$@\"\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)

        control_text = (
            "Package: drogon-installer\n"
            f"Version: {package_version}\n"
            "Section: devel\n"
            "Priority: optional\n"
            "Architecture: all\n"
            "Depends: python3\n"
            "Maintainer: drogon-installer <noreply@example.com>\n"
            "Description: CLI tool for installing Drogon and creating Drogon projects\n"
        )
        (debian_dir / "control").write_text(control_text, encoding="utf-8")
        (debian_dir / "control").chmod(0o644)

        log("Building Debian package...")
        run_command(
            ["dpkg-deb", "--build", str(package_root), str(output_deb)],
            cwd=project_root,
            verbose=verbose,
        )

    log(f"Debian package build completed: {output_deb}")
    return output_deb


def build_dmg(project_root: Path, output_dir: Path, artifact_name: str, verbose: bool) -> Path:
    if platform.system() != "Darwin":
        fail("macOS .dmg builds are supported only on macOS.")

    ensure_command_exists(
        "pyinstaller",
        "pyinstaller is required for dmg builds. Install it with: pip install pyinstaller",
    )
    ensure_command_exists("hdiutil", "hdiutil is required for dmg builds (available on macOS).")

    log("Building macOS binary with PyInstaller...")
    run_command(
        ["pyinstaller", "--onefile", "--clean", "--name", "drogon-installer", "install.py"],
        cwd=project_root,
        verbose=verbose,
    )

    source_bin = project_root / "dist" / "drogon-installer"
    if not source_bin.exists():
        fail(f"Expected macOS binary not found: {source_bin}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_dmg = output_dir / artifact_name

    with tempfile.TemporaryDirectory(prefix="drogon-installer-dmg-") as tmpdir:
        stage_dir = Path(tmpdir) / "stage"
        stage_dir.mkdir(parents=True, exist_ok=True)
        staged_bin = stage_dir / "drogon-installer"
        shutil.copy2(source_bin, staged_bin)
        staged_bin.chmod(0o755)

        log("Creating dmg artifact...")
        run_command(
            [
                "hdiutil",
                "create",
                "-volname",
                "drogon-installer",
                "-srcfolder",
                str(stage_dir),
                "-ov",
                "-format",
                "UDZO",
                str(output_dmg),
            ],
            cwd=project_root,
            verbose=verbose,
        )

    log(f"DMG build completed: {output_dmg}")
    return output_dmg


def handle_build(args: argparse.Namespace) -> None:
    project_root = Path(__file__).resolve().parent
    target = args.target

    if target == "exe":
        build_exe(
            project_root=project_root,
            output_dir=project_root / "dist",
            artifact_name="drogon-installer.exe",
            verbose=args.verbose,
        )
        return

    if target == "deb":
        build_deb(
            project_root=project_root,
            output_dir=project_root / "dist",
            artifact_name="drogon-installer_legacy.deb",
            release_version="1.0.0",
            verbose=args.verbose,
        )
        return

    if target == "apt":
        deb_file = build_deb(
            project_root=project_root,
            output_dir=project_root / "dist",
            artifact_name="drogon-installer_legacy.deb",
            release_version="1.0.0",
            verbose=args.verbose,
        )
        log("Installing package with apt...")
        run_command(["sudo", "apt", "install", "-y", str(deb_file)], cwd=project_root, verbose=args.verbose)
        log("apt install completed successfully.")
        return

    fail(f"Unsupported build target: {target}")


def handle_release(args: argparse.Namespace) -> None:
    project_root = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    version = args.version
    targets = args.targets

    produced: list[Path] = []
    log(f"Release target directory: {output_dir}")
    log(f"Release version label: {version}")

    for target in targets:
        if target == "exe":
            if platform.system() != "Windows":
                warn("Skipping .exe build on non-Windows host. Build this target on Windows.")
                continue
            produced.append(build_exe(project_root, output_dir, f"DM-{version}.exe", args.verbose))
            continue

        if target == "deb":
            if platform.system() != "Linux":
                warn("Skipping .deb build on non-Linux host. Build this target on Linux.")
                continue
            produced.append(build_deb(project_root, output_dir, f"DM-{version}.deb", version, args.verbose))
            continue

        if target == "dmg":
            if platform.system() != "Darwin":
                warn("Skipping .dmg build on non-macOS host. Build this target on macOS.")
                continue
            produced.append(build_dmg(project_root, output_dir, f"DB-{version}.dmg", args.verbose))
            continue

        fail(f"Unsupported release target: {target}")

    if not produced:
        fail("No artifacts were built on this host. Run release builds on the correct OS for each target.")

    log("Release artifacts built:")
    for path in produced:
        log(f" - {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drogon-installer",
        description="Install Drogon or create a new Drogon project.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install Drogon on this machine.")
    install_parser.add_argument("--only-deps", action="store_true", help="Install system dependencies only.")
    install_parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Install dependencies and fetch source, but skip building Drogon.",
    )
    install_parser.add_argument("--verbose", action="store_true", help="Print all executed commands.")
    install_parser.set_defaults(func=handle_install)

    create_parser = subparsers.add_parser("create", help="Create a new Drogon project.")
    create_parser.add_argument("project_name", help="Name of the project to create.")
    create_parser.set_defaults(func=handle_create)

    build_parser = subparsers.add_parser("build", help="Build installer artifacts (.exe, .deb, or apt install).")
    build_parser.add_argument("target", choices=["exe", "deb", "apt"], help="Build target.")
    build_parser.add_argument("--verbose", action="store_true", help="Print all executed commands.")
    build_parser.set_defaults(func=handle_build)

    release_parser = subparsers.add_parser(
        "release",
        help="Build release artifacts with versioned names (DM-*.exe, DM-*.deb, DB-*.dmg).",
    )
    release_parser.add_argument(
        "--version",
        default=DEFAULT_RELEASE_VERSION,
        help="Release label used in artifact names (default: v1).",
    )
    release_parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "release"),
        help="Output directory for release artifacts.",
    )
    release_parser.add_argument(
        "--targets",
        nargs="+",
        choices=["exe", "deb", "dmg"],
        default=["exe", "deb", "dmg"],
        help="Artifacts to build.",
    )
    release_parser.add_argument("--verbose", action="store_true", help="Print all executed commands.")
    release_parser.set_defaults(func=handle_release)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
