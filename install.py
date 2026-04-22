#!/usr/bin/env python3
"""CLI for installing Drogon and creating Drogon projects."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
