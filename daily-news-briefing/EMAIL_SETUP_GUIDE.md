# Email Setup Guide (Gmail)

Gmail requires an **App Password** — not your regular account password — for SMTP access.

## Steps

**1. Enable 2-Factor Authentication**
- Go to myaccount.google.com → Security → 2-Step Verification → Turn On

**2. Create an App Password**
- Go to myaccount.google.com → Security → App Passwords
- Select app: "Mail" / Select device: "Other (custom name)"
- Enter a name like "News Briefing Bot"
- Click Generate — copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

**3. Set environment variables**
```bash
export EMAIL_ADDRESS='your-account@gmail.com'
export EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'
```

**4. Test**
```bash
python -c "
from config_loader import load_config
from email_delivery import EmailDelivery
cfg = load_config()
d = EmailDelivery(cfg)
d.send('# Test\n\nThis is a test briefing.')
print('Done')
"
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `SMTPAuthenticationError` | Wrong App Password or 2FA not enabled |
| `Connection refused` | Check smtp_server / smtp_port in config.yaml |
| Email in spam | Add sender to contacts; use a recognizable sender_name |
| `No recipients configured` | Check `email_delivery.recipients` in config.yaml |
