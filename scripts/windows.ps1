param(
    [switch]$OnlyDeps,
    [switch]$SkipBuild,
    [switch]$VerboseMode
)

$ErrorActionPreference = "Stop"

if ($VerboseMode) {
    $VerbosePreference = "Continue"
}

function Log($Message) {
    Write-Host "[windows] $Message"
}

function Fail($Message) {
    Write-Error "[windows] ERROR: $Message"
    exit 1
}

function Run-Command($Command, $Arguments) {
    if ($VerboseMode) {
        Log ("CMD> {0} {1}" -f $Command, ($Arguments -join " "))
    }

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        Fail ("Command failed: {0} {1}" -f $Command, ($Arguments -join " "))
    }
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

if ($OnlyDeps) {
    Log "Dependency-only mode enabled. On Windows, vcpkg manages dependencies with package installs."
    Log "No Drogon package installation was performed."
    exit 0
}

if ($SkipBuild) {
    Log "Skip-build mode enabled. Skipping Drogon package installation."
    exit 0
}

Log "Installing Drogon with vcpkg (triplet: $triplet)..."
Run-Command "vcpkg" @("install", "drogon:$triplet")

Log "Drogon installation finished successfully."
