import platform
import subprocess
import sys

def run(cmd):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit("Command failed")

os_name = platform.system()

if os_name == "Linux":
    run("bash scripts/linux.sh")
elif os_name == "Darwin":
    run("bash scripts/macos.sh")
elif os_name == "Windows":
    run("powershell -ExecutionPolicy Bypass -File scripts/windows.ps1")
else:
    sys.exit("Unsupported OS")