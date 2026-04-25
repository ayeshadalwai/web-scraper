## scrape_instagram_events

Scrapes recent Instagram posts from tracked Malaysia AI/tech accounts and returns likely event posts for human review.

**Script:** `skills/instagram_event_scraper.py`

**Run with:**
```bash
python3 skills/instagram_event_scraper.py
```

Requires:

APIFY_TOKEN environment variable

Inputs:

accounts.txt contains Instagram account URLs to scrape

Outputs:

output/events_output.json
output/events_output.csv

Use this tool when:

User asks to find recent AI or tech events
User asks to scrape Instagram accounts for events
User asks for hackathons, workshops, bootcamps, talks, panels, training programmes, or student tech opportunities

Notes:

The scraper uses Apify's Instagram scraper.
It labels results as high or possible confidence using simple event and tech keywords.
It avoids returning duplicate posts using seen_posts.json.


