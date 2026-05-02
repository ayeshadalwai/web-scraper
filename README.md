# Instagram Event Scraper

Scrapes Malaysian AI/tech event posts from tracked Instagram accounts using Apify.

## Current MVP

The scraper:
- reads Instagram account URLs from `accounts.txt`
- scrapes recent posts using Apify
- filters likely AI/tech event posts
- exports results to JSON and CSV
- supports dry-run mode using cached Apify output to avoid extra usage cost

## Setup

Install dependency:

```bash
pip install apify-client
```

Set Apify token:

export APIFY_TOKEN=your_token_here

## Run

Live run, uses Apify credits:

python3 skills/instagram_event_scraper.py

Dry run, uses cached data for free:

python3 skills/instagram_event_scraper.py --dry-run

## Output
output/events_output.json
output/events_output.csv
output/apify_cache.json

## Notes
- seen_posts.json tracks already seen posts during live runs.
- Dry-run mode ignores duplicate tracking so cached posts can be reused for filter testing.
- Current filtering prioritises actionable AI/tech opportunities and tries to reduce non-actionable posts like recaps, merchandise, winners/finalists, and sponsor/partner spotlights.