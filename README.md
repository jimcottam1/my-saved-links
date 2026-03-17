# Michelle's Recipe Book

A personal recipe collection site hosted on GitHub Pages. Michelle shares recipes from Facebook, Instagram, and the wider web — this site collects them into a searchable, beautifully presented book.

**Live site:** https://jimcottam1.github.io/my-saved-links/

---

## Adding new recipes

Use the **Admin page** (`admin.html`) — open it directly from your local machine (not via GitHub Pages).

### Prerequisites

1. **Python 3** installed
2. Install dependencies:
   ```
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Copy your Chrome profile (run once, with Chrome closed):
   ```
   python copy_profile.py
   ```
   This creates `~/ChromePW` — a snapshot of your Chrome login session so the server can fetch Facebook/Instagram content while Chrome stays open.

4. Set your **GitHub Personal Access Token** in the admin settings:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate a token with the `repo` scope
   - Paste it into the ⚙️ settings in `admin.html`

### Starting the server

Double-click **`start_server.bat`** or run:
```
python server.py
```

The server runs on `http://localhost:5555` and uses your Chrome login session to fetch metadata and thumbnail images from Facebook and Instagram.

### Adding a recipe

1. Open `admin.html` in your browser — the green pill confirms the server is running
2. Paste a Facebook, Instagram, or regular URL
3. Click **Fetch Details** — title, description, and thumbnail are auto-filled
4. Adjust anything if needed, then click **Add Recipe**
5. The image is saved to `/images/` and the recipe card is added to `index.html` — both committed directly to GitHub

---

## Project structure

| File | Purpose |
|------|---------|
| `index.html` | The live recipe book (GitHub Pages) |
| `admin.html` | Admin UI for adding and deleting recipes |
| `server.py` | Local Flask server — fetches FB/IG metadata via Playwright |
| `start_server.bat` | Double-click launcher for the server |
| `copy_profile.py` | One-time Chrome profile copy (run before first use) |
| `requirements.txt` | Python dependencies |
| `images/` | Locally hosted recipe thumbnails |

---

## How it works

- **Metadata fetching** — `server.py` launches Chrome with your real login session using [Playwright](https://playwright.dev/python/), navigates to the URL, and extracts the page title, description, and `og:image` thumbnail (including downloading the image as base64).
- **Image storage** — thumbnails are saved as `images/recipe_NN.jpg` in the repo, avoiding expiring Facebook CDN URLs.
- **GitHub commits** — `admin.html` uses the GitHub Contents API to commit images and `index.html` changes directly, so the live site updates within ~60 seconds.
- **Newest first** — recipes are sorted by newest on every page load.
