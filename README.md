# Anime Telegram Report

Daily Telegram bot report that:
- fetches anime news from RSS feeds
- scores items by relevance to your watchlist
- sends the top 10 to Telegram
- includes a daily motivational line
- leaves a placeholder for schedule sync

## Files
- `send_report.py`
- `.github/workflows/anime_report.yml`
- `requirements.txt`

## Setup

1. Create a Telegram bot with `@BotFather`.
2. Message your bot once in Telegram.
3. Get your chat ID:
   `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
4. Create a GitHub repo and upload these files.
5. Add GitHub Actions secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `NEWSAPI_KEY` (optional)
6. Run the workflow manually once from GitHub Actions.

## Notes
- The workflow cron is set to `0 11 * * *`, which is 7:00 AM Eastern during daylight time.
- If you want schedule syncing, wire a calendar source into `get_schedule_text()`.
- `NEWSAPI_KEY` is optional. Without it, the script still uses RSS feeds.

## Customize
Edit `WATCHLIST`, `TITLE_ALIASES`, `RSS_FEEDS`, and `MOTIVATION_LINES` in `send_report.py`.
