# Quick Start

## 4-Step Setup

**1. Install dependencies**
```bash
cd daily-news-briefing
pip install -r requirements.txt
```

**2. Set environment variables**
```bash
export OPENAI_API_KEY='sk-...'
export NEWS_API_KEY='your-key'       # free at newsapi.org/register
export EMAIL_ADDRESS='you@gmail.com'
export EMAIL_PASSWORD='xxxx xxxx xxxx xxxx'  # Gmail App Password
```

**3. Edit recipients in `config.yaml`**
```yaml
email_delivery:
  recipients:
    - "you@example.com"
```

**4. Run it**
```bash
python briefing_generator.py
```

---

## Common Tasks

| Task | Command |
|------|---------|
| Run once now | `python briefing_generator.py` |
| Start daily scheduler | `./start_scheduler.sh` |
| View latest report | `cat reports/news_briefing_$(date +%Y-%m-%d).md` |
| View logs | `tail -f logs/briefing.log` |
| Disable Twitter | Set `x_twitter.enabled: false` in config.yaml |
| Disable email | Set `email_delivery.enabled: false` in config.yaml |

---

## Cost Estimate

| Service | Cost |
|---------|------|
| NewsAPI | FREE (developer tier) |
| Twitter/Nitter | FREE (no API key) |
| OpenAI gpt-4o-mini | ~$0.30–0.90/month |
| **Total** | **~$0.30–0.90/month** |

---

## Troubleshooting

**"No articles remaining after filtering/ranking"**
→ Your `include_keywords` may be too restrictive. Add more keywords or set `content_filter.enabled: false` temporarily.

**Email not arriving**
→ Check spam folder. Confirm you're using a Gmail App Password (not your regular password). See EMAIL_SETUP_GUIDE.md.

**Twitter section empty**
→ Nitter instances may be temporarily down. This is expected occasionally — the report will still send without the Twitter section.
