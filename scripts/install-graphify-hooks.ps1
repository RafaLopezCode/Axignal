# Install Graphify git hooks for this repository.
# AXIGNAL-scoped only. Requires the Graphify CLI (uv tool install graphifyy).

$ErrorActionPreference = "Stop"

if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) {
    Write-Error "graphify is not installed. Install with: uv tool install graphifyy"
}

Write-Output "Installing Graphify git hooks..."
graphify hook install
graphify hook status
Write-Output "Done."
