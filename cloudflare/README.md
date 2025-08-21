## Wazuh <> Cloudflare Enterprise Integration

Wazuh is a powerful open-source security platform used for log analysis, threat detection, and incident response. While it supports a wide range of log sources, integrating Cloudflare’s security events and audit logs isn’t officially documented.

## Setup instructions - Manager

- If not already done, please add an agent.
- Add the rules in `cloudflare-rules.xml` to the manager, and restart Wazuh.

## Setup instructions - Wazuh Agent

### Script configuration

1. Clone the repository

2. Create or edit `/path/to/integration/.cloudflare-secrets`, set the following :

```bash
export CLOUDFLARE_ACCOUNT_ID="c****b"
export CLOUDFLARE_API_TOKEN="S****A"
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
  <!-- Cloudflare logs -->
  <localfile>
    <location>/path/to/integration/cloudflare.log</location>
    <log_format>json</log_format>
    <label key="@source">Cloudflare</label>
  </localfile>
```


### Crontab configuration

1. Execute `sudo crontab -e`

2. Add the following :

```bash
    */10 * * * * /bin/bash -c 'source /path/to/integration/.cloudflare-secrets && python3 /path/to/integration/cloudflare.py'
```

### Logrotate configuration

As root :

1. Install logrotate

```apt install logrotate```

2. Create a file /etc/logrotate.d/cloudflare. Add the following :

```
/path/to/integration/cloudflare.log {
    su root root
    size 10M
    rotate 3
    compress
    missingok
    notifempty
    copytruncate
}
```

2. Check using `logrotate -d /etc/logrotate.d/cloudflare`
3. Apply configuration using `logrotate -f /etc/logrotate.d/cloudflare`
