#!/usr/bin/env bash
# Install Graphify git hooks for this repository.
# AXIGNAL-scoped only. Requires the Graphify CLI (uv tool install graphifyy).
set -euo pipefail

if ! command -v graphify >/dev/null 2>&1; then
  echo "graphify is not installed. Install with: uv tool install graphifyy" >&2
  exit 1
fi

echo "Installing Graphify git hooks..."
graphify hook install
graphify hook status
echo "Done."
