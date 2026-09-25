param(
    [Parameter(Mandatory = $false)]
    [string]$Root = $env:P0_SOURCE01B_ROOT
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    throw 'Set P0_SOURCE01B_ROOT to a task-local directory outside the repository.'
}

$resolvedRoot = [System.IO.Path]::GetFullPath($Root)
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$repoPrefix = $repoRoot.TrimEnd('\') + '\'
if ($resolvedRoot.Equals($repoRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $resolvedRoot.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The candidate environment root must be outside the AXIGNAL repository.'
}

$env:UV_CACHE_DIR = Join-Path $resolvedRoot 'uv-cache'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $resolvedRoot 'browsers'
$null = New-Item -ItemType Directory -Force -Path $resolvedRoot

$candidateNames = @('scrapling', 'crawlee', 'crawl4ai', 'scrapy', 'playwright')
foreach ($candidateName in $candidateNames) {
    $candidateDir = Join-Path $resolvedRoot $candidateName
    $pythonPath = Join-Path $candidateDir '.venv\Scripts\python.exe'
    $lockPath = Join-Path $PSScriptRoot ("candidates\$candidateName\requirements.lock")
    $null = New-Item -ItemType Directory -Force -Path $candidateDir
    uv venv --clear --python 3.12 (Join-Path $candidateDir '.venv')
    if ($LASTEXITCODE -ne 0) { throw "Failed to create $candidateName environment." }
    uv pip sync --require-hashes --python $pythonPath $lockPath
    if ($LASTEXITCODE -ne 0) { throw "Failed to sync $candidateName from its hash-locked requirements." }
}

$controllerDir = Join-Path $resolvedRoot 'controller'
$controllerPython = Join-Path $controllerDir '.venv\Scripts\python.exe'
$controllerLock = Join-Path $PSScriptRoot 'controller-requirements.lock'
$null = New-Item -ItemType Directory -Force -Path $controllerDir
uv venv --clear --python 3.12 (Join-Path $controllerDir '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Failed to create benchmark controller environment.' }
uv pip sync --require-hashes --python $controllerPython $controllerLock
if ($LASTEXITCODE -ne 0) { throw 'Failed to sync benchmark controller requirements.' }

& (Join-Path $resolvedRoot 'playwright\.venv\Scripts\python.exe') -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw 'Failed to install pinned Playwright Chromium.' }
& (Join-Path $resolvedRoot 'scrapling\.venv\Scripts\patchright.exe') install chromium
if ($LASTEXITCODE -ne 0) { throw 'Failed to install pinned Patchright Chromium.' }

Write-Output "Candidate environments and browser binaries are under $resolvedRoot"
