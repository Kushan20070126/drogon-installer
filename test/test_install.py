import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent dir to sys.path to import install.py
sys.path.append(str(Path(__file__).resolve().parent.parent))
import install


def test_validate_project_name():
    # Valid names
    install.handle_create(MagicMock(project_name="my_project", dry_run=True))
    install.handle_create(MagicMock(project_name="MyProject", dry_run=True))
    install.handle_create(MagicMock(project_name="project-123", dry_run=True))

    # Invalid names should fail
    with pytest.raises(SystemExit):
        install.handle_create(MagicMock(project_name="123project"))
    with pytest.raises(SystemExit):
        install.handle_create(MagicMock(project_name="my project"))
    with pytest.raises(SystemExit):
        install.handle_create(MagicMock(project_name="_start_with_underscore"))


@patch("platform.system")
def test_os_detection_linux(mock_system):
    mock_system.return_value = "Linux"
    args = MagicMock(only_deps=False, skip_build=False, verbose=False)
    scripts_dir = Path("scripts")
    script_path, command = install.resolve_install_command("Linux", scripts_dir, args)
    
    assert script_path.name == "linux.sh"
    assert "bash" in command


@patch("platform.system")
def test_os_detection_macos(mock_system):
    mock_system.return_value = "Darwin"
    args = MagicMock(only_deps=False, skip_build=False, verbose=False)
    scripts_dir = Path("scripts")
    script_path, command = install.resolve_install_command("Darwin", scripts_dir, args)
    
    assert script_path.name == "macos.sh"
    assert "bash" in command


@patch("platform.system")
def test_os_detection_windows(mock_system):
    mock_system.return_value = "Windows"
    args = MagicMock(only_deps=False, skip_build=False, verbose=False)
    scripts_dir = Path("scripts")
    script_path, command = install.resolve_install_command("Windows", scripts_dir, args)
    
    assert script_path.name == "windows.ps1"
    assert "powershell" in command


@patch("subprocess.run")
def test_dry_run_no_execution(mock_run):
    args = MagicMock(dry_run=True, verbose=False)
    install.run_command(["echo", "hello"], Path("."), args)
    mock_run.assert_not_called()


@patch("subprocess.run")
def test_verbose_logging(mock_run, capsys):
    mock_run.return_value = MagicMock(returncode=0)
    args = MagicMock(dry_run=False, verbose=True)
    install.run_command(["echo", "hello"], Path("."), args)
    captured = capsys.readouterr()
    assert "Running command: echo hello" in captured.out


def test_incompatible_flags():
    args = MagicMock(only_deps=True, skip_build=True)
    with pytest.raises(SystemExit):
        install.resolve_install_command("Linux", Path("scripts"), args)
