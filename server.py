#!/usr/bin/env python3
"""
Local Playwright server for Michelle's Recipe Admin
────────────────────────────────────────────────────
Run this before using admin.html to get proper metadata
from Facebook and Instagram (uses your real Chrome login).

Usage:
    python server.py

Then open admin.html — it will automatically use this server.

First-time setup:
    pip install flask flask-cors playwright
    playwright install chromium
    python copy_profile.py   ← run once to copy your Chrome profile
"""

import platform
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright not installed. Run:")
    print("  pip install flask flask-cors playwright")
    print("  playwright install chromium")
    exit(1)

app = Flask(__name__)
CORS(app)

PORT = 5555


def get_chrome_profile():
    """
    Use the copied profile (ChromePW) if it exists — this lets Chrome
    stay open while the server runs. Otherwise fall back to the real
    profile (Chrome must be closed first).
    Run copy_profile.py once to create the ChromePW copy.
    """
    copied = Path.home() / "ChromePW"
    if copied.exists():
        return str(copied)

    system = platform.system()
    home = Path.home()
    if system == "Windows":
        return str(home / "AppData" / "Local" / "Google" / "Chrome" / "User Data")
    elif system == "Darwin":
        return str(home / "Library" / "Application Support" / "Google" / "Chrome")
    return str(home / ".config" / "google-chrome")


DEAD_PHRASES = [
    "log in", "forgot account", "this video isn't available",
    "this content isn't available", "sign in to facebook",
    "you must log in", "sorry, this page isn't available",
]


def clean_title(title):
    for suffix in [" | Facebook", " | Instagram", " - Facebook", " - Instagram"]:
        title = title.replace(suffix, "")
    return title.strip()


def looks_dead(title, desc):
    text = (title + " " + desc).lower()
    return any(p in text for p in DEAD_PHRASES)


@app.route("/image")
def download_image():
    """Download an image with browser headers and return as base64."""
    import urllib.request, base64
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer":    "https://www.facebook.com/",
            "Accept":     "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        return jsonify({"base64": base64.b64encode(data).decode("ascii")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "port": PORT})


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    profile = get_chrome_profile()
    print(f"  Fetching: {url[:80]}...")
    print(f"  Profile:  {profile}")

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile,
                channel="chrome",
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-notifications",
                ],
                ignore_default_args=["--enable-automation"],
            )
        except Exception as e:
            msg = str(e)
            if "Target page, context or browser has been closed" in msg or "already running" in msg.lower():
                hint = " (Chrome may be open — run copy_profile.py first)"
            else:
                hint = ""
            return jsonify({"error": f"Could not launch Chrome: {msg}{hint}"}), 500

        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2500)

            title = clean_title(page.title() or "")

            description = ""
            for selector in [
                'meta[property="og:description"]',
                'meta[name="description"]',
                'meta[property="og:title"]',
            ]:
                el = page.query_selector(selector)
                if el:
                    val = (el.get_attribute("content") or "").strip()
                    if val:
                        description = val
                        break

            thumbnail = ""
            for sel in ['meta[property="og:image:secure_url"]', 'meta[property="og:image"]']:
                el = page.query_selector(sel)
                if el:
                    val = (el.get_attribute("content") or "").strip()
                    if val:
                        thumbnail = val
                        break

            if looks_dead(title, description):
                return jsonify({
                    "error": "Page returned a login wall — make sure you are logged into Facebook/Instagram in Chrome and have run copy_profile.py"
                }), 422

            # Download thumbnail image using the same authenticated browser context
            import base64 as b64mod
            thumbnail_base64 = ""
            if thumbnail:
                try:
                    img_response = page.request.get(thumbnail, timeout=15000)
                    if img_response.ok:
                        thumbnail_base64 = b64mod.b64encode(img_response.body()).decode("ascii")
                        print(f"  ImgSize:  {len(thumbnail_base64)} chars base64")
                except Exception as img_err:
                    print(f"  Img err:  {img_err}")

            result = {
                "title":            title[:150],
                "description":      description[:400],
                "thumbnail":        thumbnail,
                "thumbnail_base64": thumbnail_base64,
            }
            print(f"  Title:    {result['title'][:60]}")
            print(f"  Thumb:    {'yes' if thumbnail else 'no'}")
            return jsonify(result)

        except PWTimeout:
            return jsonify({"error": "Timed out loading page"}), 504
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            page.close()
            context.close()


if __name__ == "__main__":
    profile = get_chrome_profile()
    copied_exists = Path.home() / "ChromePW"

    print()
    print("  Michelle's Recipe Admin — Local Server")
    print("  " + "─" * 38)
    print(f"  URL:     http://localhost:{PORT}")
    print(f"  Profile: {profile}")
    if not copied_exists.exists():
        print()
        print("  ⚠️  No ChromePW profile found.")
        print("  Run copy_profile.py once (with Chrome closed)")
        print("  so Chrome can stay open while the server runs.")
    print()
    print("  Open admin.html to start adding recipes.")
    print("  Press Ctrl+C to stop.")
    print()

    app.run(port=PORT, debug=False, threaded=False)
