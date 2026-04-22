$ErrorActionPreference = "Stop"

function Log($Message) {
    Write-Host "[windows] $Message"
}

function Fail($Message) {
    Write-Error "[windows] ERROR: $Message"
    exit 1
}

Log "Checking for vcpkg..."
$vcpkg = Get-Command vcpkg -ErrorAction SilentlyContinue
if (-not $vcpkg) {
    Write-Host "[windows] vcpkg was not found in PATH."
    Write-Host "[windows] Install vcpkg first, then re-run this installer."
    Write-Host "[windows] Quick start:"
    Write-Host "[windows]   git clone https://github.com/microsoft/vcpkg.git"
    Write-Host "[windows]   .\vcpkg\bootstrap-vcpkg.bat"
    Write-Host "[windows]   Add the vcpkg folder to PATH"
    Fail "vcpkg is required for Windows installation."
}

$triplet = if ($env:VCPKG_DEFAULT_TRIPLET) { $env:VCPKG_DEFAULT_TRIPLET } else { "x64-windows" }
Log "Installing Drogon with vcpkg (triplet: $triplet)..."
& vcpkg install "drogon:$triplet"

Log "Drogon installation finished successfully."
