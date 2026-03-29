# Twitter/X Setup Guide

This system uses **Nitter RSS feeds** — completely free, no API key, no registration.

## How It Works

Nitter is an open-source Twitter frontend. Many public instances expose RSS feeds at:
```
https://nitter.net/{username}/rss
```

The system tries 4 instances automatically and uses the first that responds:
1. https://nitter.net
2. https://nitter.poast.org
3. https://nitter.privacydev.net
4. https://nitter.1d4.us

If all fail, the Twitter section is omitted from the report (not an error).

## Cost Comparison

| Option | Cost | Limits |
|--------|------|--------|
| Nitter RSS (this system) | **FREE** | Varies by instance uptime |
| Twitter Basic API | $100/month | 10,000 reads/month |
| Twitter Pro API | $5,000/month | Higher limits |

## Configuration

Add accounts to `config.yaml`:
```yaml
x_twitter:
  enabled: true
  accounts:
    - username: "elonmusk"
      display_name: "Elon Musk"
      max_tweets: 50
      exclude_replies: false
      exclude_retweets: false
      enabled: true
```

**Options:**
- `exclude_replies: true` — skip tweets starting with `@`
- `exclude_retweets: true` — skip tweets starting with `RT @`
- `max_tweets: 50` — cap per account (last 24 hours only)

## Forcing a Specific Nitter Instance

```yaml
x_twitter:
  nitter_instance: "https://nitter.net"
```

## Troubleshooting

**Twitter section missing from report**
→ All Nitter instances may be down. Check https://status.d420.de/ for instance status. This is normal occasionally — just wait for the next day's run.

**Wrong tweets fetched**
→ Verify the username is correct (case-insensitive). Check if the account is private.

**FAQ**

*Is this legal?* Nitter only accesses public tweets. It's equivalent to reading twitter.com in a browser.

*Will it always be free?* Nitter instances are community-maintained and occasionally go offline. The system handles this gracefully.
