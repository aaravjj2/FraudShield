#!/usr/bin/env bash
CMD="${CLAUDE_TOOL_INPUT:-}"
if echo "$CMD" | grep -q "git push.*--force.*main\|git push.*-f.*main"; then
  echo "BLOCKED: force push to main"; exit 1; fi
if echo "$CMD" | grep -q "git add.*creditcard\.csv"; then
  echo "BLOCKED: do not commit creditcard.csv"; exit 1; fi
if echo "$CMD" | grep -qE "rm -rf (src|api|ml|dashboard|/)"; then
  echo "BLOCKED: destructive rm -rf"; exit 1; fi
exit 0
