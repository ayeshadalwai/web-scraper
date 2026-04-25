import csv
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from apify_client import ApifyClient


APIFY_TOKEN = os.getenv("APIFY_TOKEN")
DAYS_BACK = 90
RESULTS_LIMIT_PER_ACCOUNT = 5

BASE_DIR = Path(__file__).resolve().parent.parent
ACCOUNTS_FILE = BASE_DIR / "accounts.txt"
OUTPUT_DIR = BASE_DIR / "output"
SEEN_FILE = BASE_DIR / "seen_posts.json"

EVENT_KEYWORDS = [
    "event", "workshop", "hackathon", "competition", "webinar",
    "bootcamp", "training", "programme", "program", "meetup",
    "panel", "talk", "seminar", "registration", "register",
    "apply", "deadline", "rsvp", "open to all students",
]

TECH_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "ml",
    "data", "tech", "coding", "developer", "software",
    "robotics", "semiconductor", "computer vision", "yolov8",
    "agentic", "fintech", "digital", "startup",
]


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        raise FileNotFoundError(f"Missing accounts file: {ACCOUNTS_FILE}")

    accounts = []
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                accounts.append(line)

    return accounts


def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, indent=2)


def extract_url(item):
    raw_url = item.get("url", "")
    short_code = item.get("shortCode")

    if raw_url and "/p/" in raw_url:
        return raw_url

    if short_code:
        return f"https://www.instagram.com/p/{short_code}/"

    return None


def is_recent(item):
    timestamp = item.get("timestamp")
    if not timestamp:
        return True

    try:
        post_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - post_date <= timedelta(days=DAYS_BACK)
    except Exception:
        return True


def get_text(item):
    caption = item.get("caption") or ""
    hashtags = " ".join(item.get("hashtags") or [])
    location = item.get("locationName") or ""
    owner = item.get("ownerUsername") or ""

    return f"{caption} {hashtags} {location} {owner}".lower()


def classify_post(item):
    text = get_text(item)

    matched_event = [kw for kw in EVENT_KEYWORDS if kw in text]
    matched_tech = [kw for kw in TECH_KEYWORDS if kw in text]
    matched_keywords = matched_event + matched_tech

    if len(matched_event) >= 1 and len(matched_tech) >= 1:
        confidence = "high"
    elif len(matched_event) >= 1 or len(matched_tech) >= 2:
        confidence = "possible"
    else:
        confidence = "low"

    category = "other"
    if any(kw in text for kw in ["hackathon", "competition", "technothon"]):
        category = "hackathon/competition"
    elif any(kw in text for kw in ["workshop", "bootcamp", "training"]):
        category = "workshop/training"
    elif any(kw in text for kw in ["panel", "talk", "seminar", "webinar"]):
        category = "talk/panel"
    elif any(kw in text for kw in ["apply", "programme", "program"]):
        category = "student opportunity"

    return confidence, category, matched_keywords


def scrape_accounts(client, accounts):
    run = client.actor("apify/instagram-scraper").call(
        run_input={
            "directUrls": accounts,
            "resultsType": "posts",
            "resultsLimit": RESULTS_LIMIT_PER_ACCOUNT,
            "searchType": "hashtag",
            "searchLimit": 1,
        }
    )

    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def save_outputs(events):
    OUTPUT_DIR.mkdir(exist_ok=True)

    json_path = OUTPUT_DIR / "events_output.json"
    csv_path = OUTPUT_DIR / "events_output.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    fieldnames = [
        "confidence",
        "category",
        "date_posted",
        "source",
        "url",
        "matched_keywords",
        "caption_preview",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            row = event.copy()
            row["matched_keywords"] = ", ".join(row["matched_keywords"])
            writer.writerow(row)

    return json_path, csv_path


def main():
    if not APIFY_TOKEN:
        return {"error": "APIFY_TOKEN is not set"}

    accounts = load_accounts()
    seen = load_seen()
    client = ApifyClient(APIFY_TOKEN)

    print(f"Scraping {len(accounts)} Instagram accounts...")

    items = scrape_accounts(client, accounts)

    events = []
    skipped_duplicates = 0
    skipped_old = 0
    skipped_low_confidence = 0

    for item in items:
        url = extract_url(item)

        if not url:
            continue

        if url in seen:
            skipped_duplicates += 1
            continue

        if not is_recent(item):
            skipped_old += 1
            continue

        confidence, category, matched_keywords = classify_post(item)

        if confidence == "low":
            skipped_low_confidence += 1
            continue

        seen.add(url)

        events.append(
            {
                "confidence": confidence,
                "category": category,
                "date_posted": (item.get("timestamp") or "")[:10],
                "source": f"@{item.get('ownerUsername', '')}",
                "url": url,
                "matched_keywords": matched_keywords,
                "caption_preview": (item.get("caption") or "")[:250],
            }
        )

    save_seen(seen)
    json_path, csv_path = save_outputs(events)

    return {
        "accounts_checked": len(accounts),
        "posts_scraped": len(items),
        "events_found": len(events),
        "duplicates_skipped": skipped_duplicates,
        "old_posts_skipped": skipped_old,
        "low_confidence_skipped": skipped_low_confidence,
        "json_output": str(json_path),
        "csv_output": str(csv_path),
        "events": events,
    }


if __name__ == "__main__":
    result = main()

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nScraper finished.")
        print(f"Accounts checked: {result['accounts_checked']}")
        print(f"Posts scraped: {result['posts_scraped']}")
        print(f"Events found: {result['events_found']}")
        print(f"Duplicates skipped: {result['duplicates_skipped']}")
        print(f"Low confidence skipped: {result['low_confidence_skipped']}")
        print(f"Saved JSON: {result['json_output']}")
        print(f"Saved CSV: {result['csv_output']}")

        print("\nEvents:")
        print(json.dumps(result["events"], indent=2, ensure_ascii=False))

