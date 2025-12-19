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

TMP_FILE="$(mktemp)"

printf '%s' "$PAYLOAD" \
| jq -c --arg event "$EVENT_TYPE" '
  (.payload // .) as $raw

  | def final_action:
      if ($raw.action | type == "string")
      then ($event + "." + $raw.action)
      else $event
      end;

  {
    integration: "github",
    github: (
      {
        action: final_action,
        actor: ($raw.sender.login // ""),
        repo: ($raw.repository.name // ""),
        org: ($raw.organization.login // "")
      }

      + (if $raw.forced? then { forced: $raw.forced } else {} end)
      + (if $raw.ref? then { ref: $raw.ref } else {} end)
      + (if $raw.ref_type? then { ref_type: $raw.ref_type } else {} end)

      + (if $raw.pull_request? then {
          pull_request: {
            merged: $raw.pull_request.merged,
            title: $raw.pull_request.title,
            id: $raw.pull_request.id,
            user: { login: $raw.pull_request.user.login },
            base: { label: $raw.pull_request.base.label },
            merged_by: { login: $raw.pull_request.merged_by.login }
          }
        } else {} end)

      + (if $raw.check_run? then {
          check_run: {
            conclusion: $raw.check_run.conclusion,
            name: $raw.check_run.name
          }
        } else {} end)

      + (if $raw.check_suite? then {
          check_suite: {
            conclusion: $raw.check_suite.conclusion,
            name: $raw.check_suite.name
          }
        } else {} end)

      + (if $raw.deployment_status? then {
          deployment_status: {
            state: $raw.deployment_status.state
          }
        } else {} end)

      + (if $raw.workflow_job? then {
          workflow_job: {
            name: $raw.workflow_job.name,
            conclusion: $raw.workflow_job.conclusion,
            head_branch: $raw.workflow_job.head_branch
          }
        } else {} end)

      + (if $raw.repository?.visibility? then {
          repository: {
            visibility: $raw.repository.visibility
          }
        } else {} end)

      + (if $raw.organization?.login? then {
          organization: {
            login: $raw.organization.login
          }
        } else {} end)
    )
  }
' > "$TMP_FILE"

cat "$TMP_FILE" >> "$LOG_OUTPUT_FILE"
rm -f "$TMP_FILE"