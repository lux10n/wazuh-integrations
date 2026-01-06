#!/usr/bin/env bash
## Follows a JSON log, extracts the embedded syslog line, and appends to an output file.
## Usage:
##   otlp_syslog_follow.sh [/path/to/input.log] [/path/to/output.log]
## Defaults:
##   input : /var/log/fortigate/syslog.log
##   output: /var/log/fortigate/syslog_extracted.log

set -euo pipefail

SRC="${1:-/var/log/fortigate/syslog.log}"
DST="${2:-/var/log/fortigate/syslog_extracted.log}"

mkdir -p "$(dirname "$DST")"
touch "$DST"  # ensure it exists (helps Wazuh start tailing early)

## Follow from the end (-n 0) and across rotations (-F).
## stdbuf/jq --unbuffered ensures near-instant writes to $DST.
exec tail -n 0 -F "$SRC" \
  | stdbuf -oL -eL jq -r --unbuffered '
      .resourceLogs[]?
      | .scopeLogs[]?
      | .logRecords[]?
      | .body.stringValue? // empty
      | sub("^<[^>]+>"; "")   # drop <PRI> like <188>
    ' >> "$DST"