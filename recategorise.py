#!/usr/bin/env python3
"""Re-categorise existing CSV using fixed word-boundary matching."""

import csv, re, sys
sys.path.insert(0, r"C:\Users\jim_c\Downloads")
from categorise_links import categorise

CSV_IN  = r"C:\Users\jim_c\Downloads\WhatsApp Chat with M Ichelle\categorised_links_with_thumbs.csv"
CSV_OUT = r"C:\Users\jim_c\Downloads\WhatsApp Chat with M Ichelle\categorised_links_with_thumbs.csv"

rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8")))

changes = 0
for r in rows:
    old_cat = r["category"]
    new_cat = categorise(r["title"], r["description"], r["url"])
    if old_cat != new_cat:
        print(f"  #{r['number']} {old_cat!r} -> {new_cat!r} | {r['description'][:60]}")
        r["category"] = new_cat
        changes += 1

print(f"\n{changes} categories updated out of {len(rows)}")

fields = ["number","platform","url","title","description","thumbnail","category","fetched_at"]
with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print("Saved.")
