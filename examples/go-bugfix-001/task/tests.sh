#!/usr/bin/env bash
set -euo pipefail

TARGET_REPO="${1:-${TARGET_REPO:-.}}"
cd "$TARGET_REPO"

go test ./...
