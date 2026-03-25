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
├── post.html                # Generic post template
├── post-*.html              # Individual blog posts (one file per post)
├── assets/
│   ├── css/
│   │   ├── style.css        # Main site styles
│   │   └── post.css         # Post page styles
│   └── js/
│       └── app.js           # Nav, theme toggle, animations
├── sitemap.xml
├── robots.txt
└── .htaccess                # Forces HTTPS redirect
```

## Content / Posts
Each post is a standalone `.html` file named `post-<slug>.html`. Current posts cover:
- Restaurants: Cosetta, Din Tai Fung, Matu Kai, Perse, Seline, Sbar
- Parks/Outdoors: Ballona Creek, Palisades Park, Santa Monica Beach, Tongva Park
- Attractions: Brentwood Mart, Farmers Market, Hammer Museum, Heroes Golf

## Deployment
- GitHub repo: `https://github.com/nickmsaad-dotcom/westsider.git`
- Static hosting (likely via cPanel/shared host based on `.htaccess`)
- `.htaccess` forces HTTPS

## Conventions
- New posts: duplicate an existing `post-*.html`, update content, add a card to `index.html`
- **Card ordering:** Always add new post cards at the TOP of `#postsGrid` in `index.html` (newest first). March 2026 posts appear before February 2026 posts, etc.
- SEO: each page has `<meta name="description">` and Open Graph tags
- Images: sourced from Unsplash with `?w=&q=&auto=format&fit=crop` params
- Accessibility: ARIA labels used throughout nav and hero sections
