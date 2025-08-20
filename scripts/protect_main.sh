#!/usr/bin/env bash
set -euo pipefail
ORG_REPO=$(git remote get-url origin | sed -E 's#https://github.com/##; s/.git$//')
gh api -X PUT repos/$ORG_REPO/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":["CI"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f allow_force_pushes=false \
  -f allow_deletions=false \
  -f required_linear_history=true
echo "Branch protection applied to $ORG_REPO main"
