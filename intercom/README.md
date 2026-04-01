## Wazuh <> Intercom Enterprise Integration

Wazuh is a powerful open-source security platform used for log analysis, threat detection, and incident response. While it supports a wide range of log sources, integrating Intercom’s security events and audit logs isn’t officially documented.

## Setup instructions - Manager

- If not already done, please add an agent.
- Add the rules in `intercom-rules.xml` to the manager, and restart Wazuh.

## Setup instructions - Wazuh Agent

### Script configuration

1. Clone the repository

2. Create or edit `/path/to/integration/.intercom-secrets`, set the following :

```bash
export INTERCOM_API_TOKEN="f****1"
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
  <!-- intercom logs -->
  <localfile>
    <location>/path/to/integration/intercom.log</location>
    <log_format>json</log_format>
    <label key="@source">intercom</label>
  </localfile>
```


### Crontab configuration

1. Execute `sudo crontab -e`

2. Add the following :

```bash
    */10 * * * * /bin/bash -c 'source /path/to/integration/.intercom-secrets && python3 /path/to/integration/intercom.py'
```

### Logrotate configuration

As root :

1. Install logrotate

```apt install logrotate```

2. Create a file /etc/logrotate.d/intercom Add the following :

```
/path/to/integration/intercom.log {
    su root root
    size 10M
    rotate 3
    compress
    missingok
    notifempty
    copytruncate
}
```

2. Check using `logrotate -d /etc/logrotate.d/intercom`
3. Apply configuration using `logrotate -f /etc/logrotate.d/intercom`
