#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
chmod +x "$REPO_ROOT/.githooks/pre-push"
git config core.hooksPath .githooks
echo "Hook path set to .githooks — pre-push org-term scan is active."
