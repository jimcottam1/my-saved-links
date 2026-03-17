#!/usr/bin/env python3
"""
WhatsApp Link Categoriser (async / concurrent version)
Uses your real Chrome browser (with your login cookies) to visit
Facebook and Instagram links and categorise them.

SETUP:
  pip install playwright
  playwright install chromium

USAGE:
  python categorise_links.py --input "WhatsApp_Chat_with_M_Ichelle.txt"

OPTIONS:
  --input       Path to your WhatsApp export .txt file
  --output      Output CSV file (default: categorised_links.csv)
  --limit       Max links to process (default: all)
  --concurrency Number of concurrent tabs (default: 10)
  --headless    Run without showing browser window (may fail on FB/IG)
  --profile     Path to your Chrome profile (auto-detected if not set)
  --sender      Filter sender name (default: ichelle)
"""

import re
import csv
import sys
import asyncio
import argparse
import platform
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright not installed. Run:  pip install playwright && playwright install chromium")
    sys.exit(1)


# ── Chrome profile paths by OS ──────────────────────────────────────────────
def default_chrome_profile():
    system = platform.system()
    home = Path.home()
    if system == "Windows":
        return home / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    elif system == "Darwin":
        return home / "Library" / "Application Support" / "Google" / "Chrome"
    else:
        return home / ".config" / "google-chrome"


# ── Extract links from WhatsApp export ─────────────────────────────────────
def extract_links(filepath, sender_filter="ichelle"):
    pat = re.compile(r'^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[-\u2013]\s*([^:]+):\s*(.+)$')
    seen, links = set(), []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            m = pat.match(line.strip())
            if m:
                sender, content = m.groups()
                if sender_filter.lower() in sender.lower():
                    for url in re.findall(r'https?://[^\s,]+', content):
                        url = url.rstrip(".,;)")
                        if url not in seen:
                            seen.add(url)
                            links.append(url)
    return links


def is_social(url):
    return any(x in url for x in [
        "facebook.com", "fb.watch", "m.facebook.com", "instagram.com"
    ])


# ── Category keywords ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Travel":                 ["travel", "holiday", "trip", "hotel", "flight", "vacation", "abroad", "flights"],
    "News / current affairs": ["news", "breaking", "report", "journal", "politics", "election", "government"],
    "Sport":                  ["sport", "gaa", "hurling", "football", "rugby", "soccer", "match", "game", "score"],
    "Music / entertainment":  ["music", "song", "singer", "band", "concert", "movie", "film", "theatre", "theaters"],
    "Animals / pets":         ["dog", "cat", "puppy", "kitten", "animal", "pet", "wildlife", "horse"],
    "Health / wellness":      ["health", "fitness", "workout", "exercise", "wellbeing", "mental health", "diet", "weight"],
    "Food / recipes":         ["recipe", "cook", "bake", "food", "meal", "dinner", "lunch", "breakfast", "ingredients"],
    "Family / kids":          ["family", "children", "kids", "baby", "parenting", "mum", "dad"],
    "Local / Limerick":       ["limerick", "kilmallock", "munster", "ireland", "irish", "tipperary"],
    "Funny / humour":         ["funny", "lol", "laugh", "comedy", "hilarious", "joke"],
    "Inspirational":          ["inspire", "motivat", "quote", "wisdom", "faith", "prayer", "god", "blessing"],
    "Shopping / deals":       ["shop", "deal", "sale", "buy", "price", "discount", "amazon", "order"],
}

def categorise(title, description, url):
    import re as _re
    text = (title + " " + description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(_re.search(r'\b' + _re.escape(kw) + r'\b', text) for kw in keywords):
            return category
    if "/reel/" in url or "/share/v/" in url or "fb.watch" in url:
        return "Video / reel"
    if "/share/r/" in url:
        return "Shared reel"
    if "/share/p/" in url:
        return "Shared post"
    if "instagram.com/reel" in url:
        return "Instagram reel"
    if "instagram.com/p/" in url:
        return "Instagram post"
    return "Uncategorised"


# ── Fetch a single page (async) ─────────────────────────────────────────────
async def fetch_page(context, url, timeout=15000):
    page = await context.new_page()
    page.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        await asyncio.sleep(2)

        title = await page.title() or ""

        description = ""
        for selector in [
            'meta[property="og:description"]',
            'meta[name="description"]',
            'meta[property="og:title"]',
        ]:
            try:
                el = await page.query_selector(selector)
                if el:
                    description = await el.get_attribute("content") or ""
                    if description:
                        break
            except Exception:
                pass

        if not description:
            try:
                description = (await page.inner_text("body"))[:300].replace("\n", " ").strip()
            except Exception:
                pass

        # Grab og:image thumbnail
        thumbnail = ""
        try:
            el = await page.query_selector('meta[property="og:image"]')
            if el:
                thumbnail = await el.get_attribute("content") or ""
        except Exception:
            pass

        return title[:120], description[:300], thumbnail

    except PWTimeout:
        return "TIMEOUT", "", ""
    except Exception as e:
        return f"ERROR: {str(e)[:60]}", "", ""
    finally:
        await page.close()


# ── Worker: one task per link ───────────────────────────────────────────────
async def process_link(sem, context, i, total, url, results, lock):
    async with sem:
        platform_name = "Instagram" if "instagram" in url else "Facebook"
        print(f"[{i}/{total}] {platform_name}: {url[:80]}...")

        title, description, thumbnail = await fetch_page(context, url)
        category = categorise(title, description, url)

        print(f"        -> {category} | {title[:60]}")

        async with lock:
            results.append({
                "number":      i,
                "platform":    platform_name,
                "url":         url,
                "title":       title,
                "description": description,
                "thumbnail":   thumbnail,
                "category":    category,
                "fetched_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            })


# ── Main ────────────────────────────────────────────────────────────────────
async def amain():
    parser = argparse.ArgumentParser(description="Categorise WhatsApp FB/IG links using your Chrome session")
    parser.add_argument("--input",       required=True, help="WhatsApp export .txt file")
    parser.add_argument("--output",      default="categorised_links.csv")
    parser.add_argument("--limit",       type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent tabs (default: 10)")
    parser.add_argument("--headless",    action="store_true")
    parser.add_argument("--profile",     default="")
    parser.add_argument("--sender",      default="ichelle")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"File not found: {args.input}")
        sys.exit(1)

    print(f"\nReading {args.input}...")
    all_links = extract_links(args.input, args.sender)
    social_links = [u for u in all_links if is_social(u)]
    print(f"Found {len(all_links)} total links, {len(social_links)} Facebook/Instagram")

    if args.limit:
        social_links = social_links[:args.limit]
        print(f"Processing first {args.limit} links")

    if not social_links:
        print("No Facebook/Instagram links found. Exiting.")
        sys.exit(0)

    profile_path = args.profile or str(default_chrome_profile())
    print(f"Using Chrome profile: {profile_path}")
    print(f"Concurrency: {args.concurrency} tabs")
    print(f"Make sure Chrome is fully closed!\n")

    results = []

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                channel="chrome",
                headless=args.headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
        except Exception as e:
            print(f"Could not launch Chrome: {e}")
            print("  -> Make sure Chrome is closed and the profile path is correct.")
            sys.exit(1)

        sem = asyncio.Semaphore(args.concurrency)
        lock = asyncio.Lock()
        total = len(social_links)

        tasks = [
            process_link(sem, context, i, total, url, results, lock)
            for i, url in enumerate(social_links, 1)
        ]
        await asyncio.gather(*tasks)
        await context.close()

    # Sort results by original number before writing
    results.sort(key=lambda r: r["number"])

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["number", "platform", "url", "title", "description", "thumbnail", "category", "fetched_at"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! Results saved to: {args.output}")

    from collections import Counter
    counts = Counter(r["category"] for r in results)
    print("\nCategory summary:")
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"   {count:>3}  {cat}")


if __name__ == "__main__":
    asyncio.run(amain())
