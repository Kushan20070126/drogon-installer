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

function Install-Winget($Package) {
    Log "Ensuring $Package is installed via winget..."
    # Check if command exists first
    $cmd = $Package.Split('.')[0] # Rough check
    if ($Package -match "Git") { $cmd = "git" }
    if ($Package -match "CMake") { $cmd = "cmake" }
    
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Log "$cmd is already installed."
    } else {
        Log "Installing $Package..."
        winget install --id $Package --silent --accept-package-agreements --accept-source-agreements
    }
}

Log "Validating environment..."
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Fail "winget not found. Please install Windows Package Manager or use a modern Windows 10/11 version."
}

log "Installing dependencies..."
Install-Winget "Git.Git"
Install-Winget "Kitware.CMake"
Install-Winget "Microsoft.VisualStudio.2022.BuildTools"

if ($OnlyDeps) {
    Log "Dependency-only mode. Done."
    exit 0
}

$BuildRoot = Join-Path $HOME ".cache\drogon-installer"
$SourceDir = Join-Path $BuildRoot "drogon"
$BuildDir = Join-Path $SourceDir "build"

if (-not (Test-Path $BuildRoot)) {
    New-Item -ItemType Directory -Path $BuildRoot -Force
}

if (Test-Path (Join-Path $SourceDir ".git")) {
    Log "Drogon source exists. Updating..."
    Set-Location $SourceDir
    git fetch --all
    git reset --hard origin/master
} else {
    Log "Cloning Drogon repository..."
    git clone https://github.com/drogonframework/drogon.git $SourceDir
}

Set-Location $SourceDir
Log "Updating submodules..."
git submodule update --init --recursive

if ($SkipBuild) {
    Log "Skip-build mode. Done."
    exit 0
}

Log "Configuring build..."
if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir -Force
}

# On Windows, we often need to specify the generator if multiple VS versions exist
cmake -S $SourceDir -B $BuildDir -DCMAKE_BUILD_TYPE=Release

Log "Building..."
cmake --build $BuildDir --config Release -j $env:NUMBER_OF_PROCESSORS

Log "Installing..."
# Global install on Windows might need admin
cmake --install $BuildDir --config Release

Log "Drogon installation complete."
