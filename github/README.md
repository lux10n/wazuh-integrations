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

In the Event selector, choose which events you wish to receive.

2. **Set up webhook receiver**

This setup assumes you already set up your network forwarding and any other configuration that should ensure webhook delivery.

Edit `hooks.json` to match your working directory : 

```json
{
    ...
    "command-working-directory": "/path/to/wazuh-integrations/github",
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