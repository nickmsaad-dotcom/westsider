# Westsider — CLAUDE.md

## Project Overview
**westsider.org** is a static HTML/CSS/JS blog and local guide for West Los Angeles (Santa Monica, Brentwood, Sawtelle, and surrounding areas). No build system, no framework — pure hand-written HTML files deployed via GitHub.

## Tech Stack
- **Frontend:** Vanilla HTML5, CSS3 (custom), vanilla JavaScript
- **Fonts:** Google Fonts — Inter
- **Images:** Unsplash (external URLs)
- **No build tools:** No npm, no bundler, no SSG
- **Dark mode:** Toggle via `data-theme` attribute on `<html>`

## File Structure
```
westsider/
├── index.html               # Homepage (featured + post grid + newsletter)
├── post.html                # Generic post template (do NOT link to this publicly)
├── post-*.html              # Individual blog posts (one file per post)
├── assets/
│   ├── css/
│   │   ├── style.css        # Main site styles
│   │   └── post.css         # Post page styles
│   └── js/
│       └── app.js           # Nav, theme toggle, animations, share buttons
├── sitemap.xml
├── robots.txt
└── .htaccess                # Forces HTTPS redirect
```

## Content / Posts
Each post is a standalone `.html` file named `post-<slug>.html`. Current posts:
- Restaurants: Cosetta, Din Tai Fung, Holy Basil, Matu Kai, Perse, Riley & Chili's, Seline, Sbar, Sawtelle
- Parks/Outdoors: Ballona Creek, Palisades Park, Santa Monica Beach, Tongva Park
- Attractions: Brentwood Mart, Farmers Market, Hammer Museum, Heroes Golf
- Nightlife: Bars, Force of Nature, S Bar

## Deployment
- GitHub repo: `https://github.com/nickmsaad-dotcom/westsider.git`
- Hosting: **Namecheap cPanel** — files uploaded manually via cPanel File Manager
- GitHub is code backup only — NOT auto-deployed
- `.htaccess` forces HTTPS
- **After every update:** zip changed files to `~/Desktop/westsider-upload.zip`, upload to `public_html/` in cPanel and Extract

## Conventions
- New posts: duplicate an existing `post-*.html`, update content, add a card to `index.html`
- **Card ordering:** Always add new post cards at the TOP of `#postsGrid` in `index.html` (newest first). March 2026 posts appear before February 2026 posts, etc.
- **Nav links:** Post pages do NOT have a "Read" nav link — it was removed sitewide. Nav = Featured, Explore, Newsletter only.
- **Post content visibility:** `post__header` and `post__body` must NOT have the `reveal` class — content must load instantly without scrolling
- **New post checklist:**
  1. Duplicate existing `post-*.html`
  2. Update all content, meta tags, OG tags, title, hero image
  3. Add card to TOP of `#postsGrid` in `index.html`
  4. Add entry to `POST_META` in `app.js` (for Most Popular section)
  5. Add URL to `sitemap.xml`
  6. Verify Unsplash image URLs return 200 before publishing
- SEO: each page has `<meta name="description">` and Open Graph tags
- Images: sourced from Unsplash with `?w=&q=&auto=format&fit=crop` params — always verify URLs are live (not 404)
- Accessibility: ARIA labels used throughout nav and hero sections

## Known Fixes Applied
- Safari clipboard: uses `execCommand` fallback when `navigator.clipboard` unavailable
- Safari scroll reveal: `requestAnimationFrame` check fires on page load for in-viewport elements
- IntersectionObserver: `rootMargin: '0px 0px 80px 0px'` pre-triggers content before viewport entry
- `post.html` template links removed from all nav and related-post sections sitewide
