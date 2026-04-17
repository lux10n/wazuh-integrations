## Wazuh <> Jira Integration

Wazuh is a powerful open-source security platform used for log analysis, threat detection, and incident response. While it supports a wide range of log sources, integrating Jira’s audit logs isn’t officially documented.

## Setup instructions - Manager

- If not already done, please add an agent.
- Add the rules in `jira-rules.xml` to the manager, and restart Wazuh.

## Setup instructions - Wazuh Agent

### Script configuration

1. Clone the repository

2. Create or edit `/path/to/integration/.jira-secrets`, set the following :

```bash
export JIRA_BASE_URL="https://api.atlassian.com/ex/jira/xxxxx" # will be either company.atlassian.com or api.atlassian.com
export JIRA_EMAIL="your_email@example.com"
export JIRA_API_TOKEN="ATATT3x..."
```

3. Install `python3`

4. Make sure the `requests` module is installed

### Ossec Configuration

As root :

1. Open ossec.conf (on Ubuntu):

```nano /var/ossec/etc/ossec.conf```

2. Add the following inside `<ossec_config>`: 

```xml
  <!-- To add to ossec.conf -->
  <!-- jira logs -->
  <localfile>
    <location>/path/to/integration/jira.log</location>
    <log_format>json</log_format>
  </localfile>
```


### Crontab configuration

1. Execute `sudo crontab -e`

2. Add the following :

```bash
    */10 * * * * /bin/bash -c 'source /path/to/integration/.jira-secrets && python3 /path/to/integration/jira.py'
```

### Logrotate configuration

As root :

1. Install logrotate

```apt install logrotate```

2. Create a file /etc/logrotate.d/jira Add the following :

```
/path/to/integration/jira.log {
    su root root
    size 10M
    rotate 3
    compress
    missingok
    notifempty
    copytruncate
}
```

2. Check using `logrotate -d /etc/logrotate.d/jira`
3. Apply configuration using `logrotate -f /etc/logrotate.d/jira`
