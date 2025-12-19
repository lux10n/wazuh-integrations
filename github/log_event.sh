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

      + (if $raw.check_run?.conclusion? then { check_run: { conclusion: $raw.check_run.conclusion } } else {} end)
      + (if $raw.check_run?.name? then { check_run: { name: $raw.check_run.name } } else {} end)

      + (if $raw.check_suite?.conclusion? then { check_suite: { conclusion: $raw.check_suite.conclusion } } else {} end)
      + (if $raw.check_suite?.name? then { check_suite: { name: $raw.check_suite.name } } else {} end)

      + (if $raw.ref_type? then { ref_type: $raw.ref_type } else {} end)
      + (if $raw.ref? then { ref: $raw.ref } else {} end)
      + (if $raw.forced? then { forced: $raw.forced } else {} end)

      + (if $raw.repository?.visibility? then { repository: { visibility: $raw.repository.visibility } } else {} end)

      + (if $raw.deployment_status?.state? then { deployment_status: { state: $raw.deployment_status.state } } else {} end)
      + (if $raw.deployment?.creator?.login? then { deployment: { creator: { login: $raw.deployment.creator.login } } } else {} end)

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

      + (if $raw.workflow_job? then {
          workflow_job: {
            name: $raw.workflow_job.name,
            conclusion: $raw.workflow_job.conclusion,
            head_branch: $raw.workflow_job.head_branch
          }
        } else {} end)

      + (if $raw.workflow? then { workflow: $raw.workflow } else {} end)

      + (if $raw.changes?.owner?.from?.user?.login?
          then { changes: { owner: { from: { user: { login: $raw.changes.owner.from.user.login }}}}}
          else {} end)

      + (if $raw.changes?.owner?.from?.organization?.login?
          then { changes: { owner: { from: { organization: { login: $raw.changes.owner.from.organization.login }}}}}
          else {} end)

      + (if $raw.changes?.login?.from?
          then { changes: { login: { from: $raw.changes.login.from }}}
          else {} end)

      + (if $raw.changes?.repository?.name?.from?
          then { changes: { repository: { name: { from: $raw.changes.repository.name.from }}}}
          else {} end)

      + (if $raw.organization?.login? then { organization: { login: $raw.organization.login } } else {} end)

      + (if $raw.invitation?.email? then { invitation: { email: $raw.invitation.email } } else {} end)
      + (if $raw.invitation?.inviter?.login? then { invitation: { inviter: { login: $raw.invitation.inviter.login }}} else {} end)

      + (if $raw.membership?.user?.login? then { membership: { user: { login: $raw.membership.user.login }}} else {} end)

      + (if $raw.requestor?.login? then { requestor: { login: $raw.requestor.login } } else {} end)
      + (if $raw.approver?.login? then { approver: { login: $raw.approver.login } } else {} end)

      + (if $raw.forkee?.name? then { forkee: { name: $raw.forkee.name } } else {} end)
      + (if $raw.member?.login? then { member: { login: $raw.member.login } } else {} end)
      + (if $raw.team?.name? then { team: { name: $raw.team.name } } else {} end)

      + (if $raw.number? then { number: $raw.number } else {} end)
      + (if $raw.pusher?.name? then { pusher: { name: $raw.pusher.name } } else {} end)

      + (if $raw.package? then {
          package: {
            package_type: $raw.package.package_type,
            name: $raw.package.name,
            version: $raw.package.version,
            registry: { name: $raw.package.registry.name }
          }
        } else {} end)

      + (if $raw.release? then {
          release: {
            name: $raw.release.name,
            tag_name: $raw.release.tag_name
          }
        } else {} end)

      + (if $raw.environment? then { environment: $raw.environment } else {} end)
    )
  }
' > "$TMP_FILE"

cat "$TMP_FILE" >> "$LOG_OUTPUT_FILE"
rm -f "$TMP_FILE"