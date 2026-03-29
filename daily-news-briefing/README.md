# Daily News Briefing Generator

Automated daily news briefing with AI analysis. Fetches articles from NewsAPI and web sources, analyzes them with OpenAI GPT, tracks Twitter/X activity via free Nitter RSS, and delivers HTML email reports every morning at 7:00 AM PST.

**Cost:** ~$0.30–0.90/month (OpenAI only — news and Twitter are free).

---

## Features

- **Dual news sources:** NewsAPI (category/keyword/source modes) + BeautifulSoup web scraping fallback
- **AI analysis:** Per-article summary, impact, key points, sentiment score, and trend tagging
- **Twitter/X tracking:** Free Nitter RSS feeds — no API key, no cost
- **Smart filtering:** Keyword include/exclude with word-boundary matching
- **AI importance ranking:** 0-100 score, selects top 10 articles automatically
- **HTML email delivery:** Responsive template, color-coded sentiment, markdown attachment
- **Daily scheduling:** Runs at 7:00 AM PST, survives crashes, logs everything

---

## Installation

```bash
cd daily-news-briefing
pip install -r requirements.txt
```

---

## Configuration

All secrets go in environment variables — never in `config.yaml`:

```bash
export OPENAI_API_KEY='sk-...'
export NEWS_API_KEY='your-newsapi-key'        # get free key at newsapi.org
export EMAIL_ADDRESS='you@gmail.com'
export EMAIL_PASSWORD='your-gmail-app-password'  # see EMAIL_SETUP_GUIDE.md
```

Then customize `config.yaml` to set your preferred news sources, keywords, and recipients.

---

## Usage

**Run once manually:**
```bash
python briefing_generator.py
```

**Start the daily scheduler:**
```bash
./start_scheduler.sh
# or
python scheduler.py
```

**Run in background:**
```bash
nohup ./start_scheduler.sh > /dev/null 2>&1 &
```

---

## Project Structure

| File | Purpose |
|------|---------|
| `briefing_generator.py` | Main orchestrator — runs the full pipeline |
| `news_api_fetcher.py` | NewsAPI integration with 24-hour filtering |
| `news_fetcher.py` | Web scraping fallback (BeautifulSoup4) |
| `ai_news_analyzer.py` | Basic GPT analysis (summary, impact, key points) |
| `ai_news_analyzer_enhanced.py` | Enhanced analysis + sentiment + trend tracking |
| `x_fetcher.py` | Free Twitter/X via Nitter RSS feeds |
| `x_summarizer.py` | AI summarization of tweet activity |
| `content_filter.py` | Keyword include/exclude filtering |
| `news_ranker.py` | AI importance scoring (0-100) |
| `news_summarizer.py` | HTML meta-tag fallback summarizer |
| `email_delivery.py` | SMTP email with HTML template |
| `scheduler.py` | Daily 7 AM PST scheduler |
| `models.py` | `NewsArticle` and `Tweet` dataclasses |
| `config_loader.py` | YAML config + environment variable injection |
| `log_setup.py` | Rotating file + console logging |
| `config.yaml` | All non-secret configuration |
| `reports/` | Generated markdown reports (gitignored) |
| `logs/` | Application logs (gitignored) |

---

## AI Analysis Details

The enhanced analyzer (`ai_news_analyzer_enhanced.py`) produces for each article:

- **Summary** — 2-3 sentence digest
- **Impact** — why it matters
- **Key Points** — 2-3 bullet takeaways
- **Sentiment** — positive / negative / neutral / mixed
- **Sentiment Score** — -10 to +10
- **Emotional Tone** — e.g. optimistic, cautious, alarming
- **Trends** — 1-3 broader themes

Trend history is saved to `trends_history.json` and tracked over 30 days.

---

## Customization

**Change news categories** — edit `newsapi.categories` in `config.yaml`

**Add keywords** — add to `content_filter.include_keywords`

**Add Twitter accounts** — add entries under `x_twitter.accounts`

**Change analysis style** — set `ai_analysis.analysis_style` to `professional`, `casual`, `technical`, or `executive`

**Change recipients** — edit `email_delivery.recipients`

**Change run time** — edit `schedule.time` (24-hour format, PST)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No articles in report | Check `NEWS_API_KEY` env var; relax `content_filter` keywords |
| Email not sending | Verify `EMAIL_ADDRESS` / `EMAIL_PASSWORD`; see EMAIL_SETUP_GUIDE.md |
| Twitter section missing | All Nitter instances may be down — try again later |
| OpenAI errors | Verify `OPENAI_API_KEY`; check usage limits at platform.openai.com |
| Logs show scraping failures | Some sites block scrapers; disable them in `news_sources` |
