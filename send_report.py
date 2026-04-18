import os
import re
import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
import xml.etree.ElementTree as ET

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "").strip()

# Keep this list aligned with your anime tastes.
WATCHLIST = [
    "That Time I Got Reincarnated as a Slime",
    "Witch Hat Atelier",
    "Cautious Hero",
    "Saving 80,000 Gold in Another World for My Retirement",
    "Jujutsu Kaisen",
    "One Piece",
    "Classroom of the Elite",
    "Fire Force",
    "Frieren",
    "Shangri-La Frontier",
    "Solo Leveling",
    "Assassination Classroom",
    "The Beginning After the End",
    "Gachiakuta",
    "My Hero Academia",
    "Black Clover",
    "Hell's Paradise",
    "Dr. STONE",
    "To Your Eternity",
    "Mashle",
    "Kaiju No. 8",
    "Attack on Titan",
    "The Rising of the Shield Hero",
    "Goblin Slayer",
    "Tokyo Ghoul",
    "Overlord",
    "Wind Breaker",
    "Dragon Ball Daima",
    "The Apothecary Diaries",
    "Mushoku Tensei",
    "Tokyo Revengers",
    "Reign of the Seven Spellblades",
    "Psycho-Pass",
    "Moriarty the Patriot",
    "Blue Lock",
    "Fullmetal Alchemist Brotherhood",
    "86 EIGHTY-SIX",
    "Horimiya",
    "My Dress-Up Darling",
    "Fate/Zero",
    "Sword Art Online",
    "Demon Slayer",
    "Haikyu!!",
]

# Preferred high-signal RSS sources. Add or remove as you like.
RSS_FEEDS = [
    "https://www.crunchyroll.com/newsrss",
    "https://www.animenewsnetwork.com/all/rss.xml",
    "https://feeds.feedburner.com/otakumode",
]

MOTIVATION_LINES = [
    "Keep stacking tiny wins. Side quests still level the character.",
    "Progress is rarely loud. Quiet momentum still moves mountains.",
    "You do not need perfect conditions to make real progress today.",
    "A steady routine can hit harder than a burst of inspiration.",
    "Even one completed task can change the shape of a day.",
    "Small steps count. A staircase is just persistence wearing shoes.",
    "Protect your focus like it is a rare drop.",
]

TITLE_ALIASES = {
    "That Time I Got Reincarnated as a Slime": ["tensura", "slime"],
    "Frieren": ["frieren"],
    "Jujutsu Kaisen": ["jujutsu kaisen", "jjk"],
    "One Piece": ["one piece"],
    "Classroom of the Elite": ["classroom of the elite"],
    "Fire Force": ["fire force", "enen no shouboutai"],
    "Shangri-La Frontier": ["shangri-la frontier"],
    "Solo Leveling": ["solo leveling"],
    "The Beginning After the End": ["the beginning after the end", "tbate"],
    "My Hero Academia": ["my hero academia", "mha", "boku no hero"],
    "Black Clover": ["black clover"],
    "Hell's Paradise": ["hell's paradise", "jigokuraku"],
    "Dr. STONE": ["dr. stone"],
    "To Your Eternity": ["to your eternity", "fumetsu no anata e"],
    "Mashle": ["mashle"],
    "Kaiju No. 8": ["kaiju no. 8", "kaiju no 8"],
    "Attack on Titan": ["attack on titan", "aot", "shingeki no kyojin"],
    "The Rising of the Shield Hero": ["shield hero", "the rising of the shield hero"],
    "Goblin Slayer": ["goblin slayer"],
    "Tokyo Ghoul": ["tokyo ghoul"],
    "Overlord": ["overlord"],
    "Wind Breaker": ["wind breaker"],
    "Dragon Ball Daima": ["dragon ball daima"],
    "The Apothecary Diaries": ["the apothecary diaries", "kusuriya no hitorigoto"],
    "Mushoku Tensei": ["mushoku tensei"],
    "Tokyo Revengers": ["tokyo revengers"],
    "Psycho-Pass": ["psycho-pass", "psychopass"],
    "Moriarty the Patriot": ["moriarty the patriot"],
    "Blue Lock": ["blue lock"],
    "Fullmetal Alchemist Brotherhood": ["fullmetal alchemist", "fmab", "brotherhood"],
    "86 EIGHTY-SIX": ["86", "eighty-six", "eighty six"],
    "Horimiya": ["horimiya"],
    "My Dress-Up Darling": ["my dress-up darling", "dress-up darling", "sono bisque doll"],
    "Fate/Zero": ["fate/zero", "fate zero"],
    "Sword Art Online": ["sword art online", "sao"],
    "Demon Slayer": ["demon slayer", "kimetsu no yaiba"],
    "Haikyu!!": ["haikyu", "haikyuu"],
    "Witch Hat Atelier": ["witch hat atelier"],
    "Cautious Hero": ["cautious hero"],
    "Saving 80,000 Gold in Another World for My Retirement": ["saving 80,000 gold"],
    "Assassination Classroom": ["assassination classroom"],
    "Gachiakuta": ["gachiakuta"],
    "Reign of the Seven Spellblades": ["reign of the seven spellblades", "nanatsu no maken"],
}

def now_et():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return datetime.now()

def safe_get(url, **kwargs):
    headers = {
        "User-Agent": "anime-telegram-report/1.0 (+https://github.com/)"
    }
    timeout = kwargs.pop("timeout", 20)
    return requests.get(url, headers=headers, timeout=timeout, **kwargs)

def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()

def parse_rss_date(value: str):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def fetch_rss_items():
    items = []
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            resp = safe_get(feed_url)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                description = strip_html(item.findtext("description") or "")
                pub_date = parse_rss_date(item.findtext("pubDate") or "")

                if not title or not link:
                    continue

                key = (title.lower(), link.lower())
                if key in seen:
                    continue
                seen.add(key)

                items.append({
                    "title": title,
                    "url": link,
                    "description": description,
                    "published_at": pub_date,
                    "source": feed_url,
                })
        except Exception:
            continue

    return items

def fetch_newsapi_items():
    # Optional: wider net if you add NEWSAPI_KEY in GitHub secrets.
    if not NEWSAPI_KEY:
        return []

    query = " OR ".join([
        '"anime"',
        '"Crunchyroll"',
        '"Jujutsu Kaisen"',
        '"One Piece"',
        '"Solo Leveling"',
        '"Frieren"',
        '"Kaiju No. 8"',
        '"Demon Slayer"',
        '"Black Clover"',
        '"Fire Force"',
        '"Dr. STONE"',
        '"Mushoku Tensei"',
        '"The Apothecary Diaries"',
    ])

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 30,
        "apiKey": NEWSAPI_KEY,
    }

    try:
        resp = safe_get("https://newsapi.org/v2/everything", params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    items = []
    for article in data.get("articles", []):
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        description = (article.get("description") or "").strip()
        published = article.get("publishedAt") or ""
        source_name = (article.get("source") or {}).get("name") or "NewsAPI"

        if not title or not url:
            continue

        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            dt = None

        items.append({
            "title": title,
            "url": url,
            "description": description,
            "published_at": dt,
            "source": source_name,
        })
    return items

def text_for_scoring(item):
    return f"{item['title']} {item.get('description', '')}".lower()

def compute_relevancy(item):
    text = text_for_scoring(item)
    score = 0.0
    matches = []

    for title in WATCHLIST:
        aliases = TITLE_ALIASES.get(title, [title.lower()])
        title_hit = False
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower and alias_lower in text:
                title_hit = True
                score += 12.0 if alias_lower == aliases[0].lower() else 8.0
        if title_hit:
            matches.append(title)

    # Bonus terms that usually indicate genuinely useful news
    bonus_terms = {
        "trailer": 4.0,
        "visual": 3.0,
        "premiere": 4.0,
        "season": 3.0,
        "release": 3.0,
        "announced": 3.0,
        "announcement": 3.0,
        "cast": 2.0,
        "streaming": 2.0,
        "episode": 1.5,
        "manga": 1.0,
        "anime": 1.0,
    }
    for term, weight in bonus_terms.items():
        if term in text:
            score += weight

    # Recency bonus
    if item.get("published_at"):
        age_hours = max(0.0, (datetime.now(timezone.utc) - item["published_at"]).total_seconds() / 3600.0)
        score += max(0.0, 8.0 - math.log1p(age_hours))

    # Strong push for items that match multiple watched series or exact titles
    score += min(len(matches), 3) * 2.0

    item["matches"] = matches
    item["relevancy_score"] = round(score, 2)
    return item

def dedupe_items(items):
    seen_urls = set()
    seen_titles = set()
    output = []
    for item in items:
        t = re.sub(r"\s+", " ", item["title"].strip().lower())
        if item["url"] in seen_urls or t in seen_titles:
            continue
        seen_urls.add(item["url"])
        seen_titles.add(t)
        output.append(item)
    return output

def top_items():
    items = fetch_rss_items() + fetch_newsapi_items()
    items = dedupe_items(items)
    scored = [compute_relevancy(item) for item in items]
    scored.sort(key=lambda x: (x["relevancy_score"], x.get("published_at") or datetime(1970, 1, 1, tzinfo=timezone.utc)), reverse=True)
    # Prefer truly relevant items first, then backfill if needed
    relevant = [x for x in scored if x["relevancy_score"] >= 8]
    if len(relevant) >= 10:
        return relevant[:10]
    return scored[:10]

def get_schedule_text():
    # Placeholder lane. If you later wire Google Calendar or another source into this script,
    # replace this with real events.
    return "Schedule sync not connected yet."

def escape_markdown(text: str) -> str:
    # Telegram MarkdownV2 is a tiny dragon. This keeps it tame.
    special = r"_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text

def build_report():
    today = now_et().strftime("%A, %B %d, %Y")
    items = top_items()
    motivation = MOTIVATION_LINES[now_et().timetuple().tm_yday % len(MOTIVATION_LINES)]
    schedule = get_schedule_text()

    lines = [
        "🎴 Daily Anime Report",
        today,
        "",
    ]

    if not items:
        lines.append("No fresh anime items were found this cycle. The news sea is calm today.")
    else:
  for idx, item in enumerate(items, start=1):
    title = item["title"]
    url = item["url"]
    matches = ", ".join(item.get("matches", [])[:2]) or "general anime relevance"
    lines.append(f"{idx}. {title}")
    lines.append(f"   Relevance: {item['relevancy_score']} | Match: {matches}")
    lines.append(f"   {url}")
    lines.extend([
   lines.extend([
    "",
    "💬 Motivation",
    motivation,
    "",
    "📅 Today’s Schedule",
    schedule,
])
    return "\n".join(lines)

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

if __name__ == "__main__":
    send_telegram_message("Test message from GitHub Actions")
