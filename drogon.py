#!/usr/bin/env python3
"""
Drogon Ecosystem CLI - A production-ready package manager for Drogon.
Behaves like npm for C++ Drogon development.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Any

# Constants
CLI_NAME = "drogon"
DEFAULT_RELEASE_VERSION = "v1"
MIN_PYTHON_VERSION = (3, 8)
PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
DROGON_HOME = Path.home() / ".drogon"
CACHE_DIR = DROGON_HOME / "cache"
LOGS_DIR = DROGON_HOME / "logs"
CONFIG_FILE = "drogon.json"


def log(message: str) -> None:
    print(f"[{CLI_NAME}] {message}")


def warn(message: str) -> None:
    print(f"[{CLI_NAME}] WARNING: {message}")


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"[{CLI_NAME}] ERROR: {message}", file=sys.stderr)
    sys.exit(exit_code)


def run_command(command: list[str], cwd: Path, args: argparse.Namespace, shell: bool = False) -> None:
    """Execute a command or log it if --dry-run is active."""
    cmd_str = " ".join(command) if not shell else str(command[0])
    if args.dry_run:
        log(f"[dry-run] Would execute: {cmd_str}")
        return

    if args.verbose:
        log(f"Running command: {cmd_str}")

    try:
        # For 'run' command, we might want to see output directly
        completed = subprocess.run(
            command if not shell else cmd_str,
            cwd=str(cwd),
            check=False,
            shell=shell
        )
        if completed.returncode != 0:
            fail(
                f"Command failed with exit code {completed.returncode}: {cmd_str}",
                exit_code=completed.returncode,
            )
    except FileNotFoundError as exc:
        fail(f"Command failed to start: {exc}")


def ensure_dirs() -> None:
    """Ensure ~/.drogon directories exist."""
    for d in [CACHE_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def handle_doctor(args: argparse.Namespace) -> None:
    """Check environment health."""
    log("Checking environment...")
    results = []
    
    # Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    results.append(("Python", py_ver, sys.version_info >= MIN_PYTHON_VERSION))
    
    # Git
    git_path = shutil.which("git")
    results.append(("Git", git_path or "Missing", git_path is not None))
    
    # CMake
    cmake_path = shutil.which("cmake")
    results.append(("CMake", cmake_path or "Missing", cmake_path is not None))
    
    # Compiler
    if platform.system() == "Windows":
        cl_path = shutil.which("cl.exe") or shutil.which("gcc")
        results.append(("Compiler", cl_path or "Missing", cl_path is not None))
    else:
        cpp_path = shutil.which("g++") or shutil.which("clang++")
        results.append(("Compiler", cpp_path or "Missing", cpp_path is not None))

    # drogon_ctl
    ctl_path = shutil.which("drogon_ctl")
    results.append(("drogon_ctl", ctl_path or "Not Installed", ctl_path is not None))

    healthy = True
    for tool, status, ok in results:
        mark = "✔" if ok else "✘"
        print(f"  {mark} {tool:<12}: {status}")
        if not ok:
            healthy = False

    if healthy:
        log("Environment is healthy!")
    else:
        warn("Some components are missing. Run 'drogon install' to fix.")


def handle_init(args: argparse.Namespace) -> None:
    """Initialize a new drogon.json in the current directory."""
    if Path(CONFIG_FILE).exists():
        fail(f"{CONFIG_FILE} already exists.")
    
    default_config = {
        "name": Path.cwd().name,
        "version": "0.1.0",
        "scripts": {
            "dev": "cmake -B build && cmake --build build && ./build/" + Path.cwd().name,
            "build": "cmake -B build && cmake --build build"
        }
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(default_config, f, indent=2)
    log(f"Initialized {CONFIG_FILE}")


def handle_run(args: argparse.Namespace) -> None:
    """Run a script defined in drogon.json."""
    if not Path(CONFIG_FILE).exists():
        fail(f"No {CONFIG_FILE} found. Run 'drogon init' first.")
    
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    
    scripts = config.get("scripts", {})
    script_cmd = scripts.get(args.script_name)
    
    if not script_cmd:
        fail(f"Unknown script: {args.script_name}. Available: {', '.join(scripts.keys())}")
    
    log(f"Running script '{args.script_name}': {script_cmd}")
    run_command([script_cmd], cwd=Path.cwd(), args=args, shell=True)


def get_scripts_dir() -> Path:
    """Find the 'scripts' directory relative to the installer's location."""
    # When installed via pip, scripts might be in the package data
    base_path = Path(__file__).resolve().parent
    scripts_dir = base_path / "scripts"
    if scripts_dir.exists():
        return scripts_dir
    # Fallback if scripts are packaged inside an Egg or Zip (less common now but good to have)
    return base_path

def handle_install(args: argparse.Namespace) -> None:
    """Install Drogon and its dependencies."""
    ensure_dirs()
    scripts_dir = get_scripts_dir()
    system_name = platform.system()

    log(f"Detected OS: {system_name}")
    
    script_map = {
        "Linux": ("linux.sh", ["bash"]),
        "Darwin": ("macos.sh", ["bash"]),
        "Windows": ("windows.ps1", ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]),
    }

    if system_name not in script_map:
        fail(f"Unsupported OS: {system_name}")

    script_name, base_cmd = script_map[system_name]
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        fail(f"Script not found at: {script_path}")

    command = base_cmd + [str(script_path)]
    
    # ... rest of handle_install ...
    
    # Pass flags to script
    env_vars = os.environ.copy()
    env_vars["BUILD_ROOT"] = str(CACHE_DIR)
    
    if system_name == "Windows":
        if args.only_deps: command.append("-OnlyDeps")
        if args.skip_build: command.append("-SkipBuild")
        if args.verbose: command.append("-VerboseMode")
    else:
        if args.only_deps: command.append("--only-deps")
        if args.skip_build: command.append("--skip-build")
        if args.verbose: command.append("--verbose")

    log(f"Starting install via {script_name}...")
    run_command(command, cwd=project_root, args=args)
    log("Installation complete.")


def handle_create(args: argparse.Namespace) -> None:
    """Create a new Drogon project."""
    if not PROJECT_NAME_RE.fullmatch(args.project_name):
        fail("Invalid project name.")

    if shutil.which("drogon_ctl") is None:
        fail("drogon_ctl not found. Run 'drogon install' first.")

    log(f"Creating project: {args.project_name}")
    run_command(["drogon_ctl", "create", "project", args.project_name], cwd=Path.cwd(), args=args)
    
    # Auto-init drogon.json in the new project
    project_dir = Path.cwd() / args.project_name
    if project_dir.exists() and not (project_dir / CONFIG_FILE).exists():
        os.chdir(project_dir)
        handle_init(args)
        log(f"Project {args.project_name} ready. 'cd {args.project_name} && drogon run build'")


def build_deb(project_root: Path, output_dir: Path, version: str, args: argparse.Namespace) -> Path:
    """Packaging logic for .deb"""
    if platform.system() != "Linux": fail("Debian builds require Linux.")
    artifact = output_dir / f"DM-{version}.deb"
    if args.dry_run: return artifact
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "DEBIAN").mkdir()
        (tmp / "usr/bin").mkdir(parents=True)
        (tmp / "usr/lib/drogon-cli").mkdir(parents=True)
        
        shutil.copy2(__file__, tmp / "usr/lib/drogon-cli/drogon.py")
        # Copy scripts too
        shutil.copytree(project_root / "scripts", tmp / "usr/lib/drogon-cli/scripts")
        
        launcher = tmp / "usr/bin/drogon"
        launcher.write_text("#!/usr/bin/env bash\npython3 /usr/lib/drogon-cli/drogon.py \"$@\"\n")
        launcher.chmod(0o755)
        
        (tmp / "DEBIAN/control").write_text(f"Package: drogon\nVersion: {version.lstrip('v')}\nArchitecture: all\nMaintainer: Drogon\nDescription: Drogon CLI\n")
        subprocess.run(["dpkg-deb", "--build", tmpdir, str(artifact)], check=True)
    return artifact

# ... Simplified build_exe and build_dmg for brevity as they follow similar patterns ...

def main() -> None:
    parser = argparse.ArgumentParser(prog=CLI_NAME, description="Drogon Package Manager")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # install
    p_inst = subparsers.add_parser("install", help="Install Drogon and dependencies")
    p_inst.add_argument("--only-deps", action="store_true")
    p_inst.add_argument("--skip-build", action="store_true")
    p_inst.set_defaults(func=handle_install)

    # create
    p_crea = subparsers.add_parser("create", help="Create new project")
    p_crea.add_argument("project_name")
    p_crea.set_defaults(func=handle_create)

    # init
    p_init = subparsers.add_parser("init", help="Initialize drogon.json")
    p_init.set_defaults(func=handle_init)

    # run
    p_run = subparsers.add_parser("run", help="Run project scripts")
    p_run.add_argument("script_name")
    p_run.set_defaults(func=handle_run)

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Check environment")
    p_doc.set_defaults(func=handle_doctor)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
