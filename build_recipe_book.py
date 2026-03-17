#!/usr/bin/env python3
"""Build Michelle's Recipe Book — food links only, fancy design."""

import csv, html, re
from urllib.parse import quote

CSV = r"C:\Users\jim_c\Downloads\WhatsApp Chat with M Ichelle\categorised_links_with_thumbs.csv"
OUT = r"C:\Users\jim_c\Downloads\gh-deploy\index.html"

DEAD_PHRASES = [
    "log in", "forgot account", "this video isn't available",
    "video isn't available anymore", "this content isn't available",
    "this page isn't available", "sorry, this page isn't available",
    "sign in to facebook", "you must log in",
]

def is_broken(r):
    t = r.get("title","").lower()
    d = r.get("description","").lower()
    if t.startswith(("timeout","error")): return True
    if t in ("facebook","instagram") and not r.get("description","").strip() and not r.get("thumbnail","").strip(): return True
    if any(p in d for p in DEAD_PHRASES): return True
    return False

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
food = [r for r in rows if r["category"] == "Food / recipes" and not is_broken(r)]
food = list(reversed(food))  # newest first
print(f"Food recipes: {len(food)}, with thumbnails: {sum(1 for r in food if r.get('thumbnail','').startswith('http'))}")

def is_reel(url):
    return any(x in url for x in ["/reel/", "/share/r/", "/share/v/", "fb.watch", "instagram.com/reel"])

def get_ig_code(url, kind):
    m = re.search(r'/' + kind + r'/([^/?]+)', url)
    return m.group(1) if m else ""

def build_card(r, idx):
    url   = r["url"]
    thumb = r.get("thumbnail","")
    desc  = (r.get("description") or "").strip()
    title = (r.get("title") or "").replace(" | Facebook","").replace(" | Instagram","").strip()
    if title.lower() in ("facebook","instagram",""):
        title = desc[:60] if desc else "Recipe"

    # Clean description — strip login wall remnants
    if any(p in desc.lower() for p in ["log in","forgot account"]):
        desc = ""

    short_desc = html.escape(desc[:180])
    display_title = html.escape(title[:90])
    safe_url = html.escape(url)
    reel = is_reel(url)
    is_ig = "instagram" in url

    if is_ig:
        kind = "reel" if "reel" in url else "p"
        code = get_ig_code(url, kind)
        preview = f'''<div class="card-thumb ig-embed-wrap">
          <iframe src="https://www.instagram.com/{kind}/{code}/embed/" allowfullscreen loading="lazy"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-presentation"
            onerror="iframeFail(this)"></iframe>
        </div>'''
    elif thumb:
        preview = f'''<a class="card-thumb thumb-link" href="{safe_url}" target="_blank" rel="noopener">
          <img src="{html.escape(thumb)}" alt="" loading="lazy" onerror="this.closest('.card-thumb').innerHTML='<div class=ph-inner>🍽️</div>'"/>
          <div class="thumb-overlay">
            <div class="play-circle">{'▶' if reel else '🔗'}</div>
            <span>{'Watch Reel' if reel else 'View Post'} on Facebook</span>
          </div>
        </a>'''
    else:
        preview = f'''<a class="card-thumb no-thumb" href="{safe_url}" target="_blank" rel="noopener">
          <div class="ph-inner">🍽️</div>
          <div class="thumb-overlay"><span>Open on {'Instagram' if is_ig else 'Facebook'}</span></div>
        </a>'''

    return f'''
<article class="recipe-card" data-idx="{idx}">
  {preview}
  <div class="card-body">
    <h3 class="recipe-title">{display_title}</h3>
    {f'<p class="recipe-desc">{short_desc}</p>' if short_desc else ''}
    <a class="recipe-link" href="{safe_url}" target="_blank" rel="noopener">
      {'▶ Watch Recipe' if reel else '📖 View Recipe'} ↗
    </a>
  </div>
</article>'''

cards_html = "\n".join(build_card(r, i) for i, r in enumerate(food))

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Michelle's Recipes</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lato:wght@300;400;700&display=swap" rel="stylesheet"/>
<style>
:root {{
  --cream:   #fdf8f0;
  --parchment: #f5ece0;
  --warm:    #efe5d3;
  --border:  #ddd0bc;
  --terra:   #b5451b;
  --terra-d: #8c3314;
  --terra-l: #e8834a;
  --olive:   #5a6e3a;
  --text:    #2c1f0f;
  --muted:   #8a7060;
  --gold:    #c9973a;
  --radius:  12px;
}}
*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}
body {{
  font-family:'Lato',sans-serif;
  background:var(--cream);
  color:var(--text);
  min-height:100vh;
}}

/* ── Hero header ── */
.hero {{
  background: linear-gradient(160deg, #3b1f0a 0%, #6b3520 40%, #b5451b 100%);
  padding: 60px 20px 50px;
  text-align: center;
  position: relative;
  overflow: hidden;
}}
.hero::before {{
  content:'';
  position:absolute; inset:0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}}
.hero-badge {{
  display:inline-block;
  border:1px solid rgba(255,255,255,0.3);
  color:rgba(255,255,255,0.75);
  font-family:'Lato',sans-serif;
  font-weight:300;
  letter-spacing:4px;
  font-size:0.7rem;
  text-transform:uppercase;
  padding:5px 16px;
  border-radius:20px;
  margin-bottom:20px;
}}
.hero h1 {{
  font-family:'Playfair Display',serif;
  font-size:clamp(2.4rem,7vw,4.5rem);
  font-weight:700;
  color:#fff;
  line-height:1.1;
  text-shadow:0 2px 20px rgba(0,0,0,0.3);
}}
.hero h1 em {{
  font-style:italic;
  color:#f5d5a8;
}}
.hero-sub {{
  font-family:'Lato',sans-serif;
  font-weight:300;
  color:rgba(255,255,255,0.7);
  font-size:1rem;
  margin-top:12px;
  letter-spacing:1px;
}}
.hero-divider {{
  display:flex; align-items:center; justify-content:center;
  gap:12px; margin:24px auto 0; max-width:300px;
}}
.hero-divider span {{ color:rgba(255,255,255,0.3); font-size:1.2rem; }}
.hero-divider::before, .hero-divider::after {{
  content:''; flex:1; height:1px; background:rgba(255,255,255,0.2);
}}
.hero-stats {{
  display:flex; justify-content:center; gap:32px;
  margin-top:28px; flex-wrap:wrap;
}}
.stat {{
  text-align:center; color:rgba(255,255,255,0.85);
}}
.stat-num {{
  display:block;
  font-family:'Playfair Display',serif;
  font-size:1.8rem; font-weight:600; color:#f5d5a8;
}}
.stat-label {{
  font-size:0.72rem; letter-spacing:2px; text-transform:uppercase;
  font-weight:300; opacity:.7;
}}

/* ── Toolbar ── */
.toolbar {{
  position:sticky; top:0; z-index:100;
  background:rgba(253,248,240,0.97);
  backdrop-filter:blur(10px);
  border-bottom:1px solid var(--border);
  padding:12px 20px;
  display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  box-shadow:0 2px 12px rgba(0,0,0,0.06);
}}
.toolbar-logo {{
  font-family:'Playfair Display',serif;
  font-size:1rem; font-weight:600;
  color:var(--terra);
  white-space:nowrap; margin-right:4px;
}}
.search-wrap {{
  position:relative; flex:1; min-width:160px; max-width:320px;
}}
.search-wrap::before {{
  content:'🔍'; position:absolute; left:10px; top:50%;
  transform:translateY(-50%); font-size:13px; pointer-events:none;
}}
#search {{
  width:100%;
  background:#fff; border:1px solid var(--border); border-radius:20px;
  color:var(--text); font-size:13px;
  padding:7px 12px 7px 32px;
  outline:none; font-family:'Lato',sans-serif;
  transition:border-color .2s;
}}
#search:focus {{ border-color:var(--terra); box-shadow:0 0 0 3px rgba(181,69,27,.08); }}
.filter-btn {{
  padding:6px 14px; border-radius:20px; border:1px solid var(--border);
  background:#fff; color:var(--muted); font-size:12px; cursor:pointer;
  font-family:'Lato',sans-serif; font-weight:400;
  transition:all .18s; white-space:nowrap;
}}
.filter-btn.active, .filter-btn:hover {{
  background:var(--terra); border-color:var(--terra); color:#fff;
}}
#count {{ font-size:12px; color:var(--muted); margin-left:auto; white-space:nowrap; font-style:italic; }}

/* ── Chapter divider ── */
.chapter {{
  text-align:center; padding:36px 20px 16px;
  position:relative;
}}
.chapter::after {{
  content:''; display:block; width:60px; height:2px;
  background:var(--gold); margin:14px auto 0; border-radius:2px;
}}
.chapter h2 {{
  font-family:'Playfair Display',serif;
  font-size:clamp(1.4rem,3vw,2rem);
  font-weight:400; color:var(--terra);
  font-style:italic;
}}
.chapter p {{
  font-size:0.85rem; color:var(--muted);
  margin-top:6px; letter-spacing:.5px;
}}

/* ── Grid ── */
#grid {{
  display:grid;
  grid-template-columns:repeat(auto-fill, minmax(280px,1fr));
  gap:24px;
  padding:16px 24px 60px;
  max-width:1500px;
  margin:0 auto;
}}

/* ── Recipe card ── */
.recipe-card {{
  background:#fff;
  border-radius:var(--radius);
  overflow:hidden;
  border:1px solid var(--border);
  display:flex; flex-direction:column;
  transition:transform .25s ease, box-shadow .25s ease;
  box-shadow:0 2px 8px rgba(44,31,15,.06);
}}
.recipe-card:hover {{
  transform:translateY(-4px);
  box-shadow:0 12px 32px rgba(44,31,15,.14);
}}

/* ── Thumbnail ── */
.card-thumb {{
  display:block; position:relative;
  height:200px; overflow:hidden;
  background:var(--warm); flex-shrink:0;
}}
.card-thumb img {{
  width:100%; height:100%; object-fit:cover;
  display:block; transition:transform .4s ease;
}}
.recipe-card:hover .card-thumb img {{ transform:scale(1.05); }}

.thumb-overlay {{
  position:absolute; inset:0;
  background:linear-gradient(to top, rgba(44,31,15,.65) 0%, transparent 50%);
  display:flex; flex-direction:column;
  align-items:center; justify-content:flex-end;
  padding:14px; gap:6px;
  opacity:0; transition:opacity .25s;
  text-decoration:none;
}}
.recipe-card:hover .thumb-overlay {{ opacity:1; }}
.play-circle {{
  width:48px; height:48px; border-radius:50%;
  background:rgba(255,255,255,0.92);
  display:flex; align-items:center; justify-content:center;
  font-size:1.1rem; color:var(--terra);
  box-shadow:0 2px 12px rgba(0,0,0,.2);
}}
.thumb-overlay span {{
  color:#fff; font-size:11px; font-weight:700;
  letter-spacing:1px; text-transform:uppercase;
  text-shadow:0 1px 4px rgba(0,0,0,.5);
}}
.thumb-link {{ text-decoration:none; }}
.no-thumb {{
  cursor:pointer;
  background:linear-gradient(135deg, var(--parchment) 0%, var(--warm) 100%);
}}
.ph-inner {{
  position:absolute; inset:0;
  display:flex; align-items:center; justify-content:center;
  font-size:3.5rem; opacity:.35;
}}
.ig-embed-wrap {{
  height:360px;
}}
.ig-embed-wrap iframe {{
  width:100%; height:100%; border:none; display:block;
}}

/* ── Card body ── */
.card-body {{
  padding:16px 18px 18px;
  display:flex; flex-direction:column; gap:10px;
  flex:1; border-top:3px solid var(--terra-l);
}}
.recipe-title {{
  font-family:'Playfair Display',serif;
  font-size:1rem; font-weight:600;
  color:var(--text); line-height:1.35;
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;
}}
.recipe-desc {{
  font-size:0.82rem; color:var(--muted);
  line-height:1.6;
  display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
  flex:1;
}}
.recipe-link {{
  display:inline-flex; align-items:center; gap:5px;
  align-self:flex-start;
  background:var(--terra);
  color:#fff; font-size:11px; font-weight:700;
  letter-spacing:.5px; text-transform:uppercase;
  padding:7px 14px; border-radius:20px;
  text-decoration:none; margin-top:4px;
  transition:background .18s;
}}
.recipe-link:hover {{ background:var(--terra-d); }}

/* ── Empty ── */
#empty {{
  display:none; grid-column:1/-1;
  text-align:center; padding:80px 20px; color:var(--muted);
}}
#empty h3 {{
  font-family:'Playfair Display',serif;
  font-size:1.6rem; font-style:italic; margin-bottom:8px; color:var(--terra);
}}

/* ── Footer ── */
footer {{
  background:linear-gradient(135deg, #3b1f0a, #6b3520);
  color:rgba(255,255,255,0.6);
  text-align:center; padding:32px 20px;
  font-size:0.8rem; letter-spacing:.5px;
  font-family:'Lato',sans-serif; font-weight:300;
}}
footer strong {{
  font-family:'Playfair Display',serif;
  color:rgba(255,255,255,0.9); font-style:italic;
}}

@media(max-width:600px) {{
  #grid {{ grid-template-columns:1fr; padding:12px 14px 40px; gap:16px; }}
  .hero {{ padding:40px 16px 36px; }}
  .toolbar {{ padding:10px 14px; }}
}}
</style>
</head>
<body>

<header class="hero">
  <div class="hero-badge">✦ a collection of delicious finds ✦</div>
  <h1><em>Michelle's</em><br>Recipe Book</h1>
  <p class="hero-sub">Food & recipes shared with love</p>
  <div class="hero-divider"><span>✦</span></div>
  <div class="hero-stats">
    <div class="stat"><span class="stat-num">{len(food)}</span><span class="stat-label">Recipes</span></div>
    <div class="stat"><span class="stat-num">{sum(1 for r in food if is_reel(r['url']))}</span><span class="stat-label">Video Reels</span></div>
    <div class="stat"><span class="stat-num">{sum(1 for r in food if r.get('thumbnail','').startswith('http'))}</span><span class="stat-label">With Preview</span></div>
  </div>
</header>

<div class="toolbar">
  <span class="toolbar-logo">🍽 Michelle's Recipes</span>
  <div class="search-wrap">
    <input id="search" type="search" placeholder="Search recipes…" oninput="applyFilters()"/>
  </div>
  <button class="filter-btn active" data-filter="all" onclick="setFilter('all',this)">All</button>
  <button class="filter-btn" data-filter="reel" onclick="setFilter('reel',this)">▶ Reels</button>
  <button class="filter-btn" data-filter="post" onclick="setFilter('post',this)">📄 Posts</button>
  <span id="count">{len(food)} recipes</span>
</div>

<div class="chapter">
  <h2>Today's Collection</h2>
  <p>Click any recipe to watch or view the full post</p>
</div>

<div id="grid">
{cards_html}
  <div id="empty">
    <h3>No recipes found</h3>
    <p>Try a different search term.</p>
  </div>
</div>

<footer>
  <strong>Michelle's Recipe Book</strong> &nbsp;·&nbsp; {len(food)} hand-picked recipes
</footer>

<script>
let activeFilter = 'all';

function setFilter(f, btn) {{
  activeFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}}

function applyFilters() {{
  const q = document.getElementById('search').value.toLowerCase();
  let n = 0;
  document.querySelectorAll('.recipe-card').forEach(c => {{
    const isReel = c.querySelector('.thumb-link, .no-thumb')?.href
      ? /\\/reel\\/|\\/share\\/r\\/|fb\\.watch|instagram\\.com\\/reel/.test(c.querySelector('a').href)
      : false;
    const text = c.textContent.toLowerCase();
    const matchFilter = activeFilter === 'all' || (activeFilter === 'reel' && isReel) || (activeFilter === 'post' && !isReel);
    const matchSearch = !q || text.includes(q);
    const show = matchFilter && matchSearch;
    c.style.display = show ? '' : 'none';
    if(show) n++;
  }});
  document.getElementById('count').textContent = n + ' recipes';
  document.getElementById('empty').style.display = n === 0 ? 'block' : 'none';
}}

function iframeFail(el) {{
  const wrap = el.closest('.ig-embed-wrap');
  if(wrap) wrap.innerHTML = '<div class="ph-inner">🍽️</div>';
}}
</script>
</body>
</html>"""

open(OUT, "w", encoding="utf-8").write(page)
print(f"Done — {len(food)} recipes written to {OUT}")
