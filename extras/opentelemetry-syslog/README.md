# Syslog → OpenTelemetry → Syslog

Leon F. has created a custom bash script that will follow the input file and transforming each new JSON line as it arrives. `tail -F` handles log rotation, and with line-buffering the output is immediate.

Here are the steps you can take to achieve the correct configuration:

1. Check that you have the proper tools installed. You should have tail, jq and stdbuf:
    
    ```bash
    [root@wazuh-server opentelemetry]# command -v tail; command -v jq; command -v stdbuf
    /usr/bin/tail
    /usr/bin/jq
    /usr/bin/stdbuf
    ```
    
2. Place the script wherever you desire and paste the following content:
    
    ```bash
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
          .. | objects | .stringValue? // empty
          | sub("^<[^>]+>"; "")    # drop <PRI>
          | gsub("\\\\"; "")       # remove backslashes
        ' >> "$DST"
    ```
    
    I have added the default paths based on your environment, although you are free to modify it at your will.
    
3. Give the script execution permissions. I have the following name and path for the script:
    
    ```bash
    chmod +x /var/log/fortigate/extract_syslog_realtime.sh
    ```
    
4. Create a systemd so that the script runs upon restart. This will ensure the script will run even on restarts of the server itself.
    1. Systemd creation
        
        ```bash
        [root@wazuh-server opentelemetry]# cat /etc/systemd/system/extract_syslog_realtime.service
        [Unit]
        Description=Opentelemetry JSON - syslog extractor for Wazuh
        After=network.target
        
        [Service]
        Type=simple
        ExecStart=/bin/bash /var/log/fortigate/extract_syslog_realtime.sh \
          /var/log/fortigate/syslog.log \
          /var/log/fortigate/syslog_extracted.log
        Restart=always
        RestartSec=2
        ## Writes go to the journal by default; adjust if you want separate logs.
        
        [Install]
        WantedBy=multi-user.target
        ```
        
    2. Systemd registration for autostart
        
        ```bash
        systemctl daemon-reload
        systemctl enable --now extract_syslog_realtime.service
        systemctl start extract_syslog_realtime.service
        systemctl status extract_syslog_realtime.service
        ```
        
5. Edit the `/var/ossec/etc/ossec.conf` file on the agent and replace the `<localfile>` snippet:
    1. Configuration editing
        
        ```xml
        <localfile>
          <location>/var/log/fortigate/syslog_extracted.log</location> <!-- replace from /var/log/fortigate/syslog.log -->
          <log_format>syslog</log_format>
        </localfile>
        ```
        
    2. Agent reload
        
        ```bash
         systemctl restart wazuh-agent 
        ```
        

With this you should be able to visualize alerts appear on the dashboard.

Looking forward to your response.