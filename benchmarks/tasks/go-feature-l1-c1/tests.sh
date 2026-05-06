#!/usr/bin/env bash
set -euo pipefail

TARGET_REPO="${1:-${TARGET_REPO:-.}}"
cd "$TARGET_REPO"

./scripts/run_eval_case.sh go-feature-l1-c1
