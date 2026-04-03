#!/usr/bin/env python3
"""
Westsider Blog Post Generator
==============================
Finds a trending West LA topic via Claude web search, writes a full blog post,
updates index.html / app.js / sitemap.xml, and uploads directly to cPanel via FTP.

Usage:
  python generate_post.py              # Generate and write all files
  python generate_post.py --dry-run    # Preview without touching any files

Requirements:
  pip install anthropic requests
  export ANTHROPIC_API_KEY=sk-ant-...
"""

import anthropic
import ftplib
import json
import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency: pip install requests anthropic")
    sys.exit(1)

# ── Configuration ──────────────────────────────────────────────────────────────
SITE_DIR = Path(__file__).parent.resolve()
PEXELS_KEY = "OtPIDgohl6fyCZbtrS9deqhTVkpDpt1AOVop0B2UdeiHaX0UACGEy3IZ"
UPLOAD_ZIP = Path.home() / "Desktop" / "westsider-upload.zip"

FTP_HOST = "westsider.org"
FTP_USER = "westsider-auto@westsider.org"
FTP_PASS = "kocXy0-zijkad-rozjon"
FTP_ROOT = ""  # FTP root is already public_html

CATEGORY_TAG_CLASS = {
    "dining":      "tag--dining",
    "outdoors":    "tag--outdoors",
    "nightlife":   "tag--nightlife",
    "arts":        "tag--arts",
    "beaches":     "tag--beaches",
    "hidden-gems": "tag--hidden-gems",
}

CATEGORY_DISPLAY = {
    "dining":      "Dining",
    "outdoors":    "Outdoors",
    "nightlife":   "Nightlife",
    "arts":        "Arts",
    "beaches":     "Beaches",
    "hidden-gems": "Hidden Gems",
}

# Related posts shown at the bottom of each post, grouped by category
RELATED = {
    "dining": [
        ("post-holy-basil.html", "https://images.unsplash.com/photo-1559314809-0d155014e29e?w=600&q=80&auto=format&fit=crop",
         "Vibrant Thai green curry with fresh herbs", "tag--dining", "Dining",
         "Holy Basil Santa Monica: The Westside Finally Gets Real Thai Street Food",
         "The acclaimed Thai street food kitchen opens on Santa Monica Blvd.", "5 min read"),
        ("post-sawtelle.html", "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?w=600&q=80&auto=format&fit=crop",
         "Rich tonkotsu ramen with chashu pork", "tag--dining", "Dining",
         "Sawtelle Blvd: West LA&rsquo;s Japanese Food Street You&rsquo;ve Been Sleeping On",
         "The definitive guide to the best restaurants on Sawtelle.", "6 min read"),
        ("post-cosetta.html", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&q=80&auto=format&fit=crop",
         "Wood-fired pizza on a wooden board", "tag--dining", "Dining",
         "Cosetta Is the California-Italian Spot Ocean Park Needed",
         "Wood-fired pizza and natural wine in a converted Ocean Park bungalow.", "4 min read"),
    ],
    "outdoors": [
        ("post-palisades-park.html", "https://images.unsplash.com/photo-1568418268013-a51b38f236c2?w=600&q=80&auto=format&fit=crop",
         "Sunset over the Pacific Ocean from Palisades Park", "tag--outdoors", "Outdoors",
         "Palisades Park at Sunset: The Free Show That Beats Any Bar",
         "A mile of cliffside park above the Pacific. Show up at 7pm. Don&rsquo;t miss it.", "4 min read"),
        ("post-ballona-creek.html", "https://images.unsplash.com/photo-1590622055142-4313e2f6935c?w=600&q=80&auto=format&fit=crop",
         "Bike path alongside a creek on a sunny day", "tag--outdoors", "Outdoors",
         "Ballona Creek Bike Path: West LA&rsquo;s Secret 7-Mile Escape",
         "A flat, car-free path from Culver City to the beach.", "4 min read"),
        ("post-heroes-golf.html", "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=600&q=80&auto=format&fit=crop",
         "Lush green par-3 golf course on a sunny California morning", "tag--hidden-gems", "Hidden Gems",
         "Heroes Golf Course: West LA&rsquo;s Best Kept Golf Secret",
         "A 9-hole par-3 on the VA campus for $12. The best deal in LA sports.", "4 min read"),
    ],
    "nightlife": [
        ("post-bars.html", "https://images.unsplash.com/photo-1566417713940-fe7c737a9ef2?w=600&q=80&auto=format&fit=crop",
         "Rooftop bar at dusk with city lights below", "tag--nightlife", "Nightlife",
         "The Best Bars in Santa Monica Right Now",
         "Where to watch the game and what to drink while you watch it.", "5 min read"),
        ("post-force-of-nature.html", "https://images.unsplash.com/photo-1510626176961-4b57d4fbad03?w=600&q=80&auto=format&fit=crop",
         "Intimate wine bar with warm lighting and string lights", "tag--nightlife", "Nightlife",
         "Force of Nature: Venice&rsquo;s Most Interesting New Bar Is Hiding Above Abbot Kinney",
         "A women-owned wine bar in a century-old Victorian home.", "5 min read"),
        ("post-sbar.html", "https://images.unsplash.com/photo-1470337458703-46ad1756a187?w=600&q=80&auto=format&fit=crop",
         "Craft cocktails at a stylish Brentwood bar", "tag--nightlife", "Nightlife",
         "S Bar by Katsuya: Brentwood&rsquo;s Best Kept Nightlife Secret",
         "The hidden gem of Brentwood&rsquo;s nightlife scene.", "4 min read"),
    ],
    "arts": [
        ("post-hammer-museum.html", "https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=600&q=80&auto=format&fit=crop",
         "Modern art gallery interior with high ceilings", "tag--arts", "Arts",
         "The Hammer Museum: World-Class Art, Always Free",
         "Free admission, world-class exhibitions, and the best courtyard in Westwood.", "4 min read"),
        ("post-brentwood-mart.html", "https://images.unsplash.com/photo-1633583960343-e258fb899aef?w=600&q=80&auto=format&fit=crop",
         "Sunny outdoor courtyard with boutique shops", "tag--hidden-gems", "Hidden Gems",
         "Brentwood Country Mart: Brunch, Boutiques, and Sunday Ritual",
         "The low-key celebrity hangout that&rsquo;s been around since 1948.", "4 min read"),
        ("post-farmers-market.html", "https://images.unsplash.com/photo-1569254631271-fb470f53fa85?w=600&q=80&auto=format&fit=crop",
         "Colorful fresh produce at a farmers market", "tag--dining", "Dining",
         "Santa Monica Farmer&rsquo;s Market: Why Wednesday Wins",
         "The Wednesday market is the best farmers market in Los Angeles.", "4 min read"),
    ],
    "beaches": [
        ("post-santa-monica-beach.html", "https://images.unsplash.com/photo-1736804962370-637d516caedf?w=600&q=80&auto=format&fit=crop",
         "Santa Monica beach on a clear sunny day", "tag--beaches", "Beaches",
         "The Locals&rsquo; Guide to Santa Monica Beach (Beyond the Pier)",
         "Where locals actually go and what they actually do there.", "5 min read"),
        ("post-palisades-park.html", "https://images.unsplash.com/photo-1568418268013-a51b38f236c2?w=600&q=80&auto=format&fit=crop",
         "Sunset over the Pacific Ocean", "tag--outdoors", "Outdoors",
         "Palisades Park at Sunset: The Free Show That Beats Any Bar",
         "A mile of cliffside park above the Pacific. Show up at 7pm.", "4 min read"),
        ("post-tongva-park.html", "https://images.unsplash.com/photo-1767681774612-a3062667f6ac?w=600&q=80&auto=format&fit=crop",
         "Modern urban park with creative play structures", "tag--outdoors", "Outdoors",
         "Tongva Park: Santa Monica&rsquo;s Most Underrated Six Acres",
         "The best park in Santa Monica that nobody talks about.", "4 min read"),
    ],
    "hidden-gems": [
        ("post-heroes-golf.html", "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=600&q=80&auto=format&fit=crop",
         "Lush green par-3 golf course on a sunny California morning", "tag--hidden-gems", "Hidden Gems",
         "Heroes Golf Course: West LA&rsquo;s Best Kept Golf Secret",
         "A 9-hole par-3 on the VA campus for $12. The best deal in LA sports.", "4 min read"),
        ("post-brentwood-mart.html", "https://images.unsplash.com/photo-1633583960343-e258fb899aef?w=600&q=80&auto=format&fit=crop",
         "Sunny outdoor courtyard with boutique shops", "tag--hidden-gems", "Hidden Gems",
         "Brentwood Country Mart: Brunch, Boutiques, and Sunday Ritual",
         "The low-key celebrity hangout that&rsquo;s been around since 1948.", "4 min read"),
        ("post-tongva-park.html", "https://images.unsplash.com/photo-1767681774612-a3062667f6ac?w=600&q=80&auto=format&fit=crop",
         "Modern urban park with creative play structures", "tag--outdoors", "Outdoors",
         "Tongva Park: Santa Monica&rsquo;s Most Underrated Six Acres",
         "The best park in Santa Monica that nobody talks about.", "4 min read"),
    ],
}


# ── Step 1: Research a trending West LA topic ──────────────────────────────────
def research_topic(client: anthropic.Anthropic) -> str:
    """Use Claude with web search to find a timely West LA topic."""
    print("🔍 Researching trending West LA topics...")

    messages = [
        {
            "role": "user",
            "content": (
                "Search for the latest news, openings, events, and happenings in "
                "West Los Angeles — specifically Santa Monica, Brentwood, Venice, "
                "Sawtelle, Culver City, and Pacific Palisades — from the past 2 weeks. "
                "Focus on: new restaurant or bar openings, seasonal outdoor activities, "
                "local events, arts/culture news, beach updates, or underrated local spots. "
                "After searching, summarize the single most interesting, timely, and "
                "hyper-local topic in 150 words. Include: what it is, where exactly it is, "
                "why West LA locals would care, any key details (prices, hours, dates). "
                "Also identify the single best Google search query (under 8 words) that "
                "someone in LA would type to find this kind of content — e.g. "
                "'best new restaurants Santa Monica 2026' or 'things to do Venice Beach weekend'. "
                "Include it at the end labeled: TARGET QUERY: <query>"
            ),
        }
    ]

    for _ in range(6):  # handle pause_turn for long server-side loops
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=messages,
        )
        if response.stop_reason == "end_turn":
            break
        if response.stop_reason == "pause_turn":
            messages = [messages[0], {"role": "assistant", "content": response.content}]
        else:
            break

    for block in response.content:
        if block.type == "text":
            return block.text.strip()

    return "West Los Angeles has exciting new restaurant openings and outdoor events happening this month."


# ── Step 2: Get a Pexels image ─────────────────────────────────────────────────
def get_pexels_image(queries) -> dict:
    """Try each query in order and return the first Pexels result that yields photos."""
    if isinstance(queries, str):
        queries = [queries]

    for query in queries:
        print(f"📸 Searching Pexels for: {query}")
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": query, "per_page": 10, "orientation": "landscape", "size": "large"},
                timeout=10,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])

            if photos:
                # Pick the photo whose alt text best matches the query keywords
                query_words = set(query.lower().split())
                def relevance(p):
                    alt_words = set((p.get("alt") or "").lower().split())
                    return len(query_words & alt_words)

                photos.sort(key=relevance, reverse=True)
                p = photos[0]
                base = p["src"]["original"].split("?")[0]
                alt = p.get("alt") or query.title()
                print(f"   ✅ Found: {alt[:60]}")
                return {
                    "url_hero":     base + "?auto=compress&cs=tinysrgb&w=1400&q=85",
                    "url_featured": base + "?auto=compress&cs=tinysrgb&w=900&q=80",
                    "url_card":     base + "?auto=compress&cs=tinysrgb&w=600&q=80",
                    "url_og":       base + "?auto=compress&cs=tinysrgb&w=1200&q=85",
                    "alt": alt,
                }
        except Exception as e:
            print(f"  ⚠️  Pexels error on '{query}': {e}")

    # Generic LA fallback
    print("  ⚠️  All queries failed — using fallback image.")
    base = "https://images.unsplash.com/photo-1568418268013-a51b38f236c2"
    return {
        "url_hero":     base + "?w=1400&q=85&auto=format&fit=crop",
        "url_featured": base + "?w=900&q=80&auto=format&fit=crop",
        "url_card":     base + "?w=600&q=80&auto=format&fit=crop",
        "url_og":       base + "?w=1200&q=85&auto=format&fit=crop",
        "alt": "West Los Angeles scene",
    }


# ── Step 3: Generate post content via Claude ───────────────────────────────────
def generate_post_data(client: anthropic.Anthropic, topic_summary: str) -> dict:
    """Ask Claude to write the post and return structured JSON."""
    print("✍️  Generating blog post content...")

    month_year = datetime.now().strftime("%B %Y")

    # Extract target query if Claude included one
    target_query = ""
    if "TARGET QUERY:" in topic_summary:
        parts = topic_summary.split("TARGET QUERY:")
        topic_summary = parts[0].strip()
        target_query = parts[1].strip().strip('"').strip("'")

    prompt = f"""You are a staff writer for Westsider, a local lifestyle guide to West LA.
Voice: conversational, witty, insider-y, affectionate — first-person plural ("we").
Today: {month_year}

Topic summary:
{topic_summary}

Target Google search query (what people are actually searching for): {target_query}

Return ONLY a valid JSON object — no markdown fences, no extra text. Fields:

{{
  "slug": "post-short-descriptive-slug",
  "title": "Post Title Here",
  "meta_description": "130-155 char SEO description.",
  "tag": "dining",
  "read_time": "5 min read",
  "date": "{month_year}",
  "excerpt": "1-2 sentence homepage teaser under 160 chars.",
  "pexels_queries": ["most specific visual query", "broader fallback query", "category fallback"],
  "body_html": "<p class=\\"post__lead\\">Opening paragraph.</p>\\n\\n<p>Second paragraph.</p>\\n\\n<h2>Section Heading</h2>\\n<p>Content.</p>"
}}

Rules:
- slug: lowercase, hyphens, starts with "post-", 4-7 words. Derive from target query if possible.
- title: lead with the target query concept naturally — e.g. if query is "best new restaurants Santa Monica 2026",
  title could be "The Best New Restaurants in Santa Monica Right Now". Keep the Westsider voice but make sure
  the title contains the words people are searching for.
- tag: EXACTLY one of: dining, outdoors, nightlife, arts, beaches, hidden-gems
- pexels_queries: array of 3 search queries for a landscape hero photo, ordered most-to-least specific.
  Query 1: describe the exact scene/subject of this post (e.g. "izakaya bar yakitori grill", "Santa Monica beach volleyball sunset")
  Query 2: broader version without proper nouns (e.g. "Japanese restaurant warm interior", "beach volleyball golden hour")
  Query 3: generic category fallback (e.g. "restaurant dining", "outdoor beach", "cocktail bar night")
  All queries should produce LANDSCAPE photos. No text overlays, no people close-up portraits.
- body_html: 600-900 words of HTML using ONLY these elements:
    <p class="post__lead">...</p>  → first paragraph only
    <p>...</p>                     → body paragraphs
    <h2>...</h2>                   → 3-4 section headings that naturally include search keywords
    <blockquote class="pull-quote">&ldquo;Memorable quote.&rdquo;</blockquote>  → once
    <div class="post__tip"><strong>Tip Title</strong>Actionable advice.</div>  → once
  Use HTML entities: &rsquo; &ldquo; &rdquo; &mdash; &amp;
  NO markdown, NO extra HTML tags, NO inline styles.
  Naturally weave in the target query keywords throughout the body — don't stuff, just write like a local
  who happens to use the words people search for.
- meta_description: include the target query keywords, location, and a reason to click. 130-155 chars.
- excerpt: punchy, curiosity-driving, ends mid-thought if possible"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = next((b.text for b in response.content if b.type == "text"), "")

    # Strip markdown fences if Claude added them
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw.strip(), flags=re.MULTILINE)
    raw = raw.strip()

    # Extract JSON object even if surrounded by extra text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)

    data = json.loads(raw)

    # Validate and normalise
    if data.get("tag") not in CATEGORY_TAG_CLASS:
        data["tag"] = "dining"

    slug = re.sub(r"[^a-z0-9-]", "", data.get("slug", "new-post").lower().replace(" ", "-"))
    if not slug.startswith("post-"):
        slug = "post-" + slug
    data["slug"] = slug

    return data


# ── Step 4: Build post HTML file ───────────────────────────────────────────────
def build_post_html(post: dict, img: dict) -> str:
    tag = post["tag"]
    tag_cls = CATEGORY_TAG_CLASS[tag]
    tag_disp = CATEGORY_DISPLAY[tag]

    # Related posts section
    related_cards = ""
    for href, img_url, alt, r_tag_cls, r_tag, title, excerpt, rt in RELATED.get(tag, RELATED["dining"]):
        related_cards += (
            f'          <article class="card reveal">'
            f'<a href="{href}" tabindex="-1"><div class="card__image">'
            f'<img src="{img_url}" alt="{alt}" loading="lazy">'
            f'<span class="tag {r_tag_cls}">{r_tag}</span>'
            f'</div></a><div class="card__body">'
            f'<h3 class="card__title">{title}</h3>'
            f'<p class="card__excerpt">{excerpt}</p>'
            f'<div class="card__meta"><span class="read-time">{rt}</span>'
            f'<a href="{href}" class="btn btn--text">Read &rarr;</a>'
            f'</div></div></article>\n'
        )

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{post['meta_description']}">
  <meta property="og:title" content="{post['title']} &mdash; Westsider">
  <meta property="og:description" content="{post['meta_description']}">
  <meta property="og:image" content="{img['url_og']}">
  <title>{post['title']} &mdash; Westsider</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
  <link rel="stylesheet" href="assets/css/post.css">
</head>
<body>
  <div class="progress-bar" id="progressBar"></div>
  <header class="nav" id="nav" role="banner">
    <div class="container nav__inner">
      <a href="index.html" class="nav__logo" aria-label="Westsider home">West<span>sider</span></a>
      <nav class="nav__links"><a href="index.html#featured">Featured</a><a href="index.html#posts">Explore</a><a href="index.html#newsletter">Newsletter</a></nav>
      <div class="nav__actions">
        <button class="theme-toggle" id="themeToggle" aria-label="Switch to dark mode"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></button>
        <button class="nav__hamburger" id="menuToggle" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobileMenu"><span></span><span></span><span></span></button>
      </div>
    </div>
    <div class="nav__mobile" id="mobileMenu" aria-hidden="true">
      <nav class="nav__mobile-links"><a href="index.html#featured">Featured</a><a href="index.html#posts">Explore</a><a href="index.html#newsletter">Newsletter</a></nav>
    </div>
  </header>
  <main>
    <div class="post__hero" id="postHero">
      <img src="{img['url_hero']}" alt="{img['alt']}" loading="eager">
      <div class="post__hero-overlay" aria-hidden="true"></div>
    </div>
    <article class="container post__article" aria-labelledby="post-title">
      <a href="index.html" class="post__back"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>Back to Westsider</a>
      <header class="post__header">
        <span class="tag {tag_cls}">{tag_disp}</span>
        <h1 class="post__title" id="post-title">{post['title']}</h1>
        <div class="post__meta"><span>By Westsider Staff</span><span>{post['date']}</span><span class="post__read-time">{post['read_time']}</span></div>
      </header>
      <div class="post__body">
        {post['body_html']}
      </div>
      <div class="post__share">
        <button class="share-btn" onclick="shareTwitter()">Share on X</button>
        <button class="share-btn" onclick="copyLink()">Copy Link</button>
      </div>
    </article>
    <section class="section related" aria-labelledby="related-heading">
      <div class="container">
        <span class="section__eyebrow reveal">Keep Reading</span>
        <h2 class="section__heading reveal" id="related-heading">More from Westsider</h2>
        <div class="grid grid--3">
{related_cards}        </div>
      </div>
    </section>
  </main>
  <footer class="footer" role="contentinfo"><div class="container footer__inner"><div class="footer__brand"><a href="index.html" class="nav__logo" aria-label="Westsider home">West<span>sider</span></a><p class="footer__tagline">Your insider guide to West Los Angeles.</p></div><nav class="footer__links"><a href="index.html#posts">Dining</a><a href="index.html#posts">Outdoors</a><a href="index.html#posts">Nightlife</a><a href="index.html#posts">Arts</a><a href="index.html#posts">Beaches</a><a href="index.html#posts">Hidden Gems</a></nav><p class="footer__copy">&copy; 2026 Westsider. All rights reserved.</p></div></footer>
  <button class="back-to-top" id="backToTop" aria-label="Back to top">&#8679;</button>
  <script src="assets/js/app.js"></script>
  <script>document.addEventListener('DOMContentLoaded',()=>{{const h=document.getElementById('postHero');if(h)setTimeout(()=>h.classList.add('loaded'),100);}});</script>
</body>
</html>"""


# ── Step 5: Update index.html ──────────────────────────────────────────────────
def update_index_html(post: dict, img: dict) -> None:
    path = SITE_DIR / "index.html"
    html = path.read_text(encoding="utf-8")

    tag = post["tag"]
    tag_cls = CATEGORY_TAG_CLASS[tag]
    tag_disp = CATEGORY_DISPLAY[tag]
    slug_html = post["slug"] + ".html"

    # ── Replace the featured section ────────────────────────────────────────
    new_featured = f"""    <!-- FEATURED POST — {post['title'][:55]} -->
    <section class="section featured" id="featured" aria-labelledby="featured-heading">
      <div class="container">
        <span class="section__eyebrow reveal">Featured</span>
        <h2 class="section__heading reveal" id="featured-heading">This Week&rsquo;s Pick</h2>

        <article class="featured__card reveal">
          <div class="featured__image">
            <img
              src="{img['url_featured']}"
              alt="{img['alt']}"
              loading="eager"
            >
            <span class="tag {tag_cls}">{tag_disp}</span>
          </div>
          <div class="featured__body">
            <h3>{post['title']}</h3>
            <p class="excerpt">
              {post['excerpt']}
            </p>
            <div class="meta">
              <span class="read-time">{post['read_time']}</span>
              <a href="{slug_html}" class="btn btn--text">Read Article &rarr;</a>
            </div>
          </div>
        </article>
      </div>
    </section>"""

    html = re.sub(
        r"    <!-- FEATURED POST.*?</section>",
        new_featured,
        html,
        count=1,
        flags=re.DOTALL,
    )

    # ── Prepend card to postsGrid ────────────────────────────────────────────
    new_card = f"""
          <!-- — {post['title'][:55]} / {tag_disp} -->
          <article class="card reveal" data-category="{tag}">
            <a href="{slug_html}" aria-label="Read: {post['title']}" tabindex="-1">
              <div class="card__image">
                <img
                  src="{img['url_card']}"
                  alt="{img['alt']}"
                  loading="lazy"
                >
                <span class="tag {tag_cls}">{tag_disp}</span>
              </div>
            </a>
            <div class="card__body">
              <h3 class="card__title">{post['title']}</h3>
              <p class="card__excerpt">{post['excerpt']}</p>
              <div class="card__meta">
                <span class="read-time">{post['read_time']}</span>
                <a href="{slug_html}" class="btn btn--text">Read &rarr;</a>
              </div>
            </div>
          </article>
"""

    grid_marker = '        <div class="grid" id="postsGrid">'
    html = html.replace(grid_marker, grid_marker + "\n" + new_card, 1)

    path.write_text(html, encoding="utf-8")
    print("  ✅ Updated index.html")


# ── Step 6: Update app.js POST_META ───────────────────────────────────────────
def update_app_js(post: dict, img: dict) -> None:
    path = SITE_DIR / "assets" / "js" / "app.js"
    js = path.read_text(encoding="utf-8")

    slug = post["slug"]
    tag_cls = CATEGORY_TAG_CLASS[post["tag"]]
    tag_disp = CATEGORY_DISPLAY[post["tag"]]
    title_js = post["title"].replace("'", "\\'")
    alt_js = img["alt"].replace("'", "\\'")

    new_entry = (
        f"    '{slug}': {{ "
        f"title: '{title_js}', "
        f"img: '{img['url_card']}', "
        f"alt: '{alt_js}', "
        f"tag: '{tag_disp}', "
        f"tagClass: '{tag_cls}', "
        f"href: '{slug}.html' }},\n"
    )

    js = js.replace("  const POST_META = {\n", f"  const POST_META = {{\n{new_entry}", 1)
    path.write_text(js, encoding="utf-8")
    print("  ✅ Updated app.js POST_META")


# ── Step 7: Update sitemap.xml ─────────────────────────────────────────────────
def update_sitemap(slug: str) -> None:
    path = SITE_DIR / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")

    today = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"""  <url>
    <loc>https://westsider.org/{slug}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    # Insert after the first </url> (the homepage entry)
    xml = xml.replace("  </url>\n  <url>", f"  </url>\n{new_entry}  <url>", 1)
    path.write_text(xml, encoding="utf-8")
    print("  ✅ Updated sitemap.xml")


# ── Step 8: Zip files for cPanel upload ───────────────────────────────────────
def create_upload_zip(post_filename: str) -> None:
    files = [
        SITE_DIR / post_filename,
        SITE_DIR / "index.html",
        SITE_DIR / "assets" / "js" / "app.js",
        SITE_DIR / "sitemap.xml",
    ]

    with zipfile.ZipFile(UPLOAD_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                arcname = f.relative_to(SITE_DIR)
                zf.write(f, arcname)
                print(f"  📦 {arcname}")

    print(f"\n✅ Created: {UPLOAD_ZIP}")


# ── Step 9: FTP upload to cPanel ──────────────────────────────────────────────
def ftp_upload(post_filename: str) -> None:
    """Upload changed files directly to cPanel via FTP."""
    files = [
        (SITE_DIR / post_filename,               post_filename),
        (SITE_DIR / "index.html",                "index.html"),
        (SITE_DIR / "assets" / "js" / "app.js", "assets/js/app.js"),
        (SITE_DIR / "sitemap.xml",               "sitemap.xml"),
    ]

    print(f"\n🌐 Connecting to {FTP_HOST}...")
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.set_pasv(True)
        print(f"   Connected: {ftp.getwelcome()[:60]}")

        for local_path, remote_path in files:
            if not local_path.exists():
                print(f"   ⚠️  Skipping {local_path.name} (not found)")
                continue

            # Ensure remote directory exists (skip if file is in root)
            if "/" in remote_path:
                remote_dir = remote_path.rsplit("/", 1)[0]
                _ftp_makedirs(ftp, remote_dir)

            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"   ✅ Uploaded {remote_path}")

    print("\n✅ FTP upload complete.")


def _ftp_makedirs(ftp: ftplib.FTP, remote_dir: str) -> None:
    """Create remote directories recursively if they don't exist."""
    parts = remote_dir.split("/")
    path = ""
    for part in parts:
        if not part:
            continue
        path = f"{path}/{part}" if path else part
        try:
            ftp.cwd(path)
        except ftplib.error_perm:
            ftp.mkd(path)
        finally:
            ftp.cwd("/")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    dry_run = "--dry-run" in sys.argv

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY is not set.")
        print("    Run: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n🚀  Westsider Blog Post Generator")
    print("=" * 42)

    # 1. Research
    topic_summary = research_topic(client)
    print(f"\n📋 Topic found:\n   {topic_summary[:200].replace(chr(10), ' ')}...\n")

    # 2. Generate content
    post = generate_post_data(client, topic_summary)
    print(f"\n📝 Post generated:")
    print(f"   Title:  {post['title']}")
    print(f"   Slug:   {post['slug']}")
    print(f"   Tag:    {post['tag']}")
    print(f"   Excerpt: {post['excerpt'][:80]}...")

    # 3. Image — try specific queries in order, fall back to category
    queries = post.get("pexels_queries") or [post.get("pexels_query", "west los angeles")]
    img = get_pexels_image(queries)
    print(f"   Image:  {img['url_card'][:70]}...")

    if dry_run:
        print("\n⚠️   DRY RUN — no files written.")
        print("\nFull post data:")
        safe = {k: v for k, v in post.items() if k != "body_html"}
        print(json.dumps(safe, indent=2))
        print(f"\nbody_html preview:\n{post['body_html'][:300]}...")
        return

    print("\n📂 Writing files...")

    post_html = build_post_html(post, img)
    post_file = post["slug"] + ".html"
    (SITE_DIR / post_file).write_text(post_html, encoding="utf-8")
    print(f"  ✅ Created {post_file}")

    update_index_html(post, img)
    update_app_js(post, img)
    update_sitemap(post["slug"])

    print("\n📡 Uploading to westsider.org...")
    ftp_upload(post_file)

    print(f"""
{'=' * 42}
✅  Done! — {post['title']}

Live at: https://westsider.org/{post_file}
""")


if __name__ == "__main__":
    main()
