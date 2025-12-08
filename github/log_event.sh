#!/bin/bash
set -euo pipefail

LOG_OUTPUT_FILE="logs/github.log"
mkdir -p "$(dirname "$LOG_OUTPUT_FILE")"

EVENT_TYPE="${1:-}"
PAYLOAD="${2:-}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq missing. I'm not doing this without jq." >&2
  exit 1
fi

CLEAN_PAYLOAD="$(printf '%s' "$PAYLOAD" | jq -c '.')"
TMP_FILE="$(mktemp)"

echo "$CLEAN_PAYLOAD" \
  | jq -c --arg event "$EVENT_TYPE" '
      . as $raw
      | def final_action:
          if ($raw.action|type=="string")
            then $event + "." + ($raw.action)
            else $event
          end;
      {
        integration: "github",
        github:
          ($raw
            + { action: final_action }
            + { actor: ($raw.sender.login // null) }
            + { repo: ($raw.repository.name // null) }
            + { org: ($raw.organization.login // null) }
          )
      }
    ' > "$TMP_FILE"

cat "$TMP_FILE" >> "$LOG_OUTPUT_FILE"
rm -f "$TMP_FILE"