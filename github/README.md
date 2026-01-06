# GitHub Webhook <> Wazuh

A local webhook receiver using [`adnanh/webhook`](https://github.com/adnanh/webhook) to log GitHub events into a structured JSON file. Each event is recorded as a single-line JSON object for easy processing.

---

## Prerequisites

- macOS or Linux
- Bash shell (`#!/bin/bash`)
- [`jq`](https://stedolan.github.io/jq/) installed
- [`adnanh/webhook`](https://github.com/adnanh/webhook) installed

---

## Instructions 

### Webhook Configuration

1. **Create a webhook on Github's Organization Settings dashboard**

In the Event selector, choose which events you wish to receive, and set a secret for the webhook.

2. **Set up webhook receiver**

This setup assumes you already set up your network forwarding and any other configuration that should ensure webhook delivery.

Edit `hooks.json` to match your working directory and your webhook secret : 

```json
{
    ...
    "command-working-directory": "/path/to/wazuh-integrations/github",
    ...
    "secret": "your-secret-here",
    ...
}
```


Give `log_event.sh` execution rights : 
```bash
chmod +x /path/to/wazuh-integrations/github/log_event.sh
```

Test webhook configuration and reception :

Create a service that will start on boot :
```bash
nano /etc/systemd/system/github-webhook.service
```
In that file :
```ini
[Unit]
Description=GitHub Webhook Receiver
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/bin/webhook -hooks /path/to/wazuh-integrations/github/hooks.json -verbose
WorkingDirectory=/path/to/wazuh-integrations/github
Restart=always
RestartSec=3
User=youruser (or root)
Group=youruser (or root)

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Check configuration with :
```bash
sudo systemctl daemon-reload
sudo systemctl enable github-webhook.service
sudo systemctl start github-webhook.service
systemctl status github-webhook.service
```

If any error, check journal :
```bash 
journalctl -u github-webhook.service -f
```


### Ossec Configuration

Add the generated log file to Wazuh monitoring list.

As root :

1. Open ossec.conf (on Ubuntu):

```nano /var/ossec/etc/ossec.conf```

2. Add the following inside `<ossec_config>`: 

```xml
  <!-- To add to ossec.conf -->
  <!-- GitHub logs -->
  <localfile>
    <location>/path/to/wazuh-integrations/github/logs/github.log</location>
    <log_format>json</log_format>
  </localfile>
```

3. Restart Wazuh agent, and do some actions on GitHub.


## Security considerations

### HTTPS Configuration

1. From your CA, generate the following : 
    - a server key, 
    - a SSL certificate. The certificate file should be a concatenation of your server's certificate followed by the CA's certificate. 

2. Start webhook with the following arguments in your service file:

    ```ini
    ExecStart=/usr/bin/webhook -hooks /path/to/wazuh-integrations/github/hooks.json -secure -cert /path/to/cert.pem -key /path/to/key.pem -verbose 
    ```


### IP Whitelist ranges

GitHub's IP ranges for webhooks are, as of December 2025 :
- `192.30.252.0/22`
- `185.199.108.0/22`
- `140.82.112.0/20`
- `143.55.64.0/20`
- `2a0a:a440::/29`
- `2606:50c0::/3`


## Logrotate configuration

As root :

1. Install logrotate

```apt install logrotate```

2. If a file containing unified configuration already exists, just add the `/path/to/wazuh-integrations/github/logs/github.log` to the list of files to be rotated.

If not, Create a file named `/etc/logrotate.d/github`. Add the following :

```
/path/to/wazuh-integrations/github/logs/github.log {
    su root root
    size 10M
    rotate 3
    compress
    missingok
    notifempty
    copytruncate
}
```
2. Check using `logrotate -d /etc/logrotate.d/github`
3. Apply configuration using `logrotate -f /etc/logrotate.d/github`
