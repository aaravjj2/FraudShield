#!/usr/bin/env bash
if git diff --cached --name-only | grep -qE 'creditcard\.csv|\.env$|\.pem$|\.key$'; then
  echo "BLOCKED: sensitive file detected"; exit 1; fi
echo "✓ Pre-commit passed"
