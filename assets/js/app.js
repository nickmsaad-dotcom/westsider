/* ============================================================
   WESTSIDER — App JS
   ============================================================ */

(function () {
  'use strict';

  /* ──────────────────────────────────────────
     ThemeController
     Dark/light toggle with OS preference fallback
  ────────────────────────────────────────── */
  const ThemeController = {
    root: document.documentElement,
    toggle: document.getElementById('themeToggle'),
    sunIcon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`,
    moonIcon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`,

    init() {
      const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      const saved = localStorage.getItem('westsider-theme') || preferred;
      this.apply(saved);

      if (this.toggle) {
        this.toggle.addEventListener('click', () => {
          const next = this.root.dataset.theme === 'dark' ? 'light' : 'dark';
          this.apply(next);
          localStorage.setItem('westsider-theme', next);
        });
      }
    },

    apply(theme) {
      this.root.dataset.theme = theme;
      if (this.toggle) {
        this.toggle.innerHTML = theme === 'dark' ? this.sunIcon : this.moonIcon;
        this.toggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
      }
    }
  };

  /* ──────────────────────────────────────────
     NavController
     Sticky nav blur deepens on scroll
  ────────────────────────────────────────── */
  const NavController = {
    nav: document.getElementById('nav'),
    ticking: false,

    init() {
      if (!this.nav) return;
      window.addEventListener('scroll', () => {
        if (!this.ticking) {
          requestAnimationFrame(() => {
            this.nav.classList.toggle('scrolled', window.scrollY > 10);
            this.ticking = false;
          });
          this.ticking = true;
        }
      }, { passive: true });
    }
  };

  /* ──────────────────────────────────────────
     MobileMenuController
     Hamburger open/close with slide animation
  ────────────────────────────────────────── */
  const MobileMenuController = {
    btn: document.getElementById('menuToggle'),
    menu: document.getElementById('mobileMenu'),
    open: false,

    init() {
      if (!this.btn || !this.menu) return;

      this.btn.addEventListener('click', () => this.toggle());

      // Close on link click
      this.menu.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => this.close());
      });

      // Close on Escape
      document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && this.open) this.close();
      });
    },

    toggle() { this.open ? this.close() : this.openMenu(); },

    openMenu() {
      this.open = true;
      this.menu.style.maxHeight = this.menu.scrollHeight + 'px';
      this.menu.classList.add('open');
      this.btn.classList.add('open');
      this.btn.setAttribute('aria-expanded', 'true');
      this.menu.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    },

    close() {
      this.open = false;
      this.menu.style.maxHeight = '0';
      this.menu.classList.remove('open');
      this.btn.classList.remove('open');
      this.btn.setAttribute('aria-expanded', 'false');
      this.menu.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  };

  /* ──────────────────────────────────────────
     ScrollAnimator
     IntersectionObserver for .reveal elements
  ────────────────────────────────────────── */
  const ScrollAnimator = {
    init() {
      const elements = document.querySelectorAll('.reveal');
      if (!elements.length) return;

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
          if (entry.isIntersecting) {
            // Stagger siblings
            const siblings = Array.from(
              entry.target.parentElement.querySelectorAll('.reveal:not(.visible)')
            );
            const idx = siblings.indexOf(entry.target);
            entry.target.style.transitionDelay = `${Math.max(0, idx) * 70}ms`;
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      });

      elements.forEach(el => observer.observe(el));

      // Safari fix: IntersectionObserver doesn't reliably fire for elements
      // already in the viewport on page load — check them immediately
      requestAnimationFrame(function() {
        elements.forEach(function(el) {
          if (el.classList.contains('visible')) return;
          const rect = el.getBoundingClientRect();
          if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.style.transitionDelay = '0ms';
            el.classList.add('visible');
            observer.unobserve(el);
          }
        });
      });
    }
  };

  /* ──────────────────────────────────────────
     FilterController
     Category tabs with fade+scale animation
  ────────────────────────────────────────── */
  const FilterController = {
    tabs: document.querySelectorAll('.filter-tab'),
    cards: document.querySelectorAll('.card[data-category]'),

    init() {
      if (!this.tabs.length) return;

      this.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          // Update active tab
          this.tabs.forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
          });
          tab.classList.add('active');
          tab.setAttribute('aria-selected', 'true');

          const filter = tab.dataset.filter;
          this.filterCards(filter);
        });
      });
    },

    filterCards(filter) {
      this.cards.forEach(card => {
        const match = filter === 'all' || card.dataset.category === filter;

        if (match) {
          card.removeAttribute('hidden');
          card.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
          // Force reflow to restart transition
          void card.offsetWidth;
          card.style.opacity = '1';
          card.style.transform = '';
        } else {
          card.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
          card.style.opacity = '0';
          card.style.transform = 'scale(0.96)';
          setTimeout(() => {
            if (card.style.opacity === '0') {
              card.setAttribute('hidden', '');
            }
          }, 260);
        }
      });
    }
  };

  /* ──────────────────────────────────────────
     HeroController
     Trigger slow zoom once image loads
  ────────────────────────────────────────── */
  const HeroController = {
    init() {
      const hero = document.querySelector('.hero');
      if (!hero) return;
      // Small delay to trigger the CSS scale transition for the zoom effect
      setTimeout(() => hero.classList.add('loaded'), 100);
    }
  };

  /* ──────────────────────────────────────────
     NewsletterController
     Form validation + success state
  ────────────────────────────────────────── */
  const NewsletterController = {
    form: document.getElementById('newsletterForm'),
    success: document.getElementById('newsletterSuccess'),

    init() {
      if (!this.form) return;

      this.form.addEventListener('submit', e => {
        e.preventDefault();
        const input = this.form.querySelector('input[type="email"]');
        if (!input || !input.value.includes('@')) {
          input.style.borderColor = '#ff3b30';
          input.focus();
          setTimeout(() => { input.style.borderColor = ''; }, 2000);
          return;
        }
        // Show success
        this.form.classList.add('hide');
        if (this.success) this.success.classList.add('show');
      });
    }
  };

  /* ──────────────────────────────────────────
     Card click → post.html navigation
  ────────────────────────────────────────── */
  const CardNavController = {
    init() {
      document.querySelectorAll('.card, .featured__card').forEach(card => {
        const link = card.querySelector('a[href]');
        if (!link) return;
        card.style.cursor = 'pointer';
        card.addEventListener('click', (e) => {
          if (e.target.tagName === 'A') return;
          link.click();
        });
      });
    }
  };

  /* ──────────────────────────────────────────
     ProgressController
     Reading progress bar on post pages
  ────────────────────────────────────────── */
  const ProgressController = {
    init() {
      const bar = document.getElementById('progressBar');
      if (!bar) return;
      window.addEventListener('scroll', () => {
        const doc = document.documentElement;
        const scrolled = doc.scrollTop / (doc.scrollHeight - doc.clientHeight);
        bar.style.width = (scrolled * 100) + '%';
      }, { passive: true });
    }
  };

  /* ──────────────────────────────────────────
     BackToTopController
     Floating button on post pages
  ────────────────────────────────────────── */
  const BackToTopController = {
    init() {
      const btn = document.getElementById('backToTop');
      if (!btn) return;
      window.addEventListener('scroll', () => {
        const pct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight);
        btn.classList.toggle('visible', pct > 0.4);
      }, { passive: true });
      btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  };

  /* ──────────────────────────────────────────
     ReadTimeController
     Dynamic read time from word count
  ────────────────────────────────────────── */
  const ReadTimeController = {
    init() {
      const body = document.querySelector('.post__body');
      const meta = document.querySelector('.post__read-time');
      if (!body || !meta) return;
      const words = body.innerText.trim().split(/\s+/).length;
      const mins = Math.max(1, Math.round(words / 200));
      meta.textContent = mins + ' min read';
    }
  };

  /* ──────────────────────────────────────────
     ViewTracker
     Tracks post views in localStorage
  ────────────────────────────────────────── */
  const ViewTracker = {
    init() {
      const path = window.location.pathname;
      const slug = path.substring(path.lastIndexOf('/') + 1).replace('.html', '');
      if (!slug.startsWith('post-')) return;
      const views = JSON.parse(localStorage.getItem('westsider-views') || '{}');
      views[slug] = (views[slug] || 0) + 1;
      localStorage.setItem('westsider-views', JSON.stringify(views));
    }
  };

  /* ──────────────────────────────────────────
     PopularController
     "Most Popular" section on homepage
  ────────────────────────────────────────── */
  const POST_META = {
    'post-perse':            { title: 'Perse: A Modern Persian Dining Experience in Brentwood',     img: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80&auto=format&fit=crop', alt: 'Elegantly plated Persian dishes',  tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-perse.html' },
    'post-matu-kai':         { title: 'Matu Kai: Brentwood\'s New Wagyu Destination',               img: 'https://images.unsplash.com/photo-1558030006-450675393462?w=600&q=80&auto=format&fit=crop', alt: 'Wagyu steak',                     tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-matu-kai.html' },
    'post-seline':           { title: 'SELINE: Santa Monica\'s New Michelin-Worthy Tasting Menu',   img: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&q=80&auto=format&fit=crop', alt: 'Fine dining plate',               tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-seline.html' },
    'post-cosetta':          { title: 'Cosetta Is the California-Italian Spot Ocean Park Needed',   img: 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&q=80&auto=format&fit=crop', alt: 'Wood-fired pizza',                tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-cosetta.html' },
    'post-bars':             { title: 'The Best Bars in Santa Monica Right Now',                    img: 'https://images.unsplash.com/photo-1566417713940-fe7c737a9ef2?w=600&q=80&auto=format&fit=crop', alt: 'Rooftop bar',                     tag: 'Nightlife',    tagClass: 'tag--nightlife',   href: 'post-bars.html' },
    'post-din-tai-fung':     { title: 'Din Tai Fung Opens at Santa Monica Place — With Ocean Views', img: 'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&q=80&auto=format&fit=crop', alt: 'Soup dumplings',                  tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-din-tai-fung.html' },
    'post-sbar':             { title: 'S Bar by Katsuya: Brentwood\'s Best Kept Nightlife Secret',  img: 'https://images.unsplash.com/photo-1470337458703-46ad1756a187?w=600&q=80&auto=format&fit=crop', alt: 'Craft cocktails',                 tag: 'Nightlife',    tagClass: 'tag--nightlife',   href: 'post-sbar.html' },
    'post-brentwood-mart':   { title: 'Brentwood Country Mart: Brunch, Boutiques, and Sunday Ritual', img: 'https://images.unsplash.com/photo-1633583960343-e258fb899aef?w=600&q=80&auto=format&fit=crop', alt: 'Outdoor courtyard',             tag: 'Hidden Gems',  tagClass: 'tag--hidden-gems', href: 'post-brentwood-mart.html' },
    'post-farmers-market':   { title: 'Santa Monica Farmer\'s Market: Why Wednesday Wins',          img: 'https://images.unsplash.com/photo-1569254631271-fb470f53fa85?w=600&q=80&auto=format&fit=crop', alt: 'Farmers market produce',          tag: 'Dining',       tagClass: 'tag--dining',      href: 'post-farmers-market.html' },
    'post-palisades-park':   { title: 'Palisades Park at Sunset: The Free Show That Beats Any Bar', img: 'https://images.unsplash.com/photo-1568418268013-a51b38f236c2?w=600&q=80&auto=format&fit=crop', alt: 'Sunset over Pacific Ocean',       tag: 'Outdoors',     tagClass: 'tag--outdoors',    href: 'post-palisades-park.html' },
    'post-tongva-park':      { title: 'Tongva Park: Santa Monica\'s Most Underrated Six Acres',     img: 'https://images.unsplash.com/photo-1767681774612-a3062667f6ac?w=600&q=80&auto=format&fit=crop', alt: 'Urban park',                      tag: 'Outdoors',     tagClass: 'tag--outdoors',    href: 'post-tongva-park.html' },
    'post-hammer-museum':    { title: 'The Hammer Museum: World-Class Art, Always Free',            img: 'https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=600&q=80&auto=format&fit=crop', alt: 'Art gallery interior',             tag: 'Arts',         tagClass: 'tag--arts',        href: 'post-hammer-museum.html' },
    'post-ballona-creek':    { title: 'Ballona Creek Bike Path: West LA\'s Secret 7-Mile Escape',   img: 'https://images.unsplash.com/photo-1590622055142-4313e2f6935c?w=600&q=80&auto=format&fit=crop', alt: 'Bike path alongside creek',       tag: 'Outdoors',     tagClass: 'tag--outdoors',    href: 'post-ballona-creek.html' },
    'post-santa-monica-beach':{ title: 'The Locals\' Guide to Santa Monica Beach (Beyond the Pier)', img: 'https://images.unsplash.com/photo-1736804962370-637d516caedf?w=600&q=80&auto=format&fit=crop', alt: 'Santa Monica beach',             tag: 'Beaches',      tagClass: 'tag--beaches',     href: 'post-santa-monica-beach.html' },
    'post-heroes-golf':      { title: 'Heroes Golf Course: West LA\'s Best Kept Golf Secret',       img: 'https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?w=600&q=80&auto=format&fit=crop', alt: 'Par-3 golf course',               tag: 'Hidden Gems',  tagClass: 'tag--hidden-gems', href: 'post-heroes-golf.html' },
    'post-holy-basil':       { title: 'Holy Basil Santa Monica: The Westside Finally Gets Real Thai Street Food', img: 'https://images.unsplash.com/photo-1559314809-0d155014e29e?w=600&q=80&auto=format&fit=crop', alt: 'Vibrant Thai green curry with fresh herbs and coconut milk', tag: 'Dining', tagClass: 'tag--dining', href: 'post-holy-basil.html' },
    'post-force-of-nature':  { title: 'Force of Nature: Venice\'s Most Interesting New Bar Is Hiding Above Abbot Kinney', img: 'https://images.unsplash.com/photo-1510626176961-4b57d4fbad03?w=600&q=80&auto=format&fit=crop', alt: 'Intimate wine bar with warm lighting', tag: 'Nightlife', tagClass: 'tag--nightlife', href: 'post-force-of-nature.html' },
    'post-riley-chilis':     { title: 'We Interviewed the Guy Who Eats at Chili\'s Six Times a Week', img: 'https://images.unsplash.com/photo-1583119022894-919a68a3d0e3?w=600&q=80&auto=format&fit=crop', alt: 'Single big red chili pepper', tag: 'Dining', tagClass: 'tag--dining', href: 'post-riley-chilis.html' },
    'post-sawtelle':         { title: 'Sawtelle Blvd: West LA\'s Japanese Food Street You\'ve Been Sleeping On', img: 'https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?w=600&q=80&auto=format&fit=crop', alt: 'Rich tonkotsu ramen with chashu pork and soft-boiled egg at Tsujita LA on Sawtelle', tag: 'Dining', tagClass: 'tag--dining', href: 'post-sawtelle.html' }
  };

  const PopularController = {
    init() {
      const grid = document.getElementById('popularGrid');
      if (!grid) return;
      const views = JSON.parse(localStorage.getItem('westsider-views') || '{}');
      const sorted = Object.entries(views)
        .filter(([slug]) => POST_META[slug])
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);
      if (!sorted.length) {
        const section = grid.closest('section');
        if (section) section.style.display = 'none';
        return;
      }
      sorted.forEach(([slug]) => {
        const p = POST_META[slug];
        const card = document.createElement('article');
        card.className = 'card reveal';
        card.innerHTML =
          '<a href="' + p.href + '" tabindex="-1"><div class="card__image">' +
          '<img src="' + p.img + '" alt="' + p.alt + '" loading="lazy">' +
          '<span class="tag ' + p.tagClass + '">' + p.tag + '</span></div></a>' +
          '<div class="card__body"><h3 class="card__title">' + p.title + '</h3>' +
          '<div class="card__meta"><a href="' + p.href + '" class="btn btn--text">Read &rarr;</a></div></div>';
        grid.appendChild(card);
      });
      ScrollAnimator.init();
      CardNavController.init();
    }
  };

  /* ──────────────────────────────────────────
     Social Share (global scope for onclick)
  ────────────────────────────────────────── */
  window.shareTwitter = function() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(document.title);
    // Open synchronously inside the click handler so Safari doesn't block the popup
    var win = window.open('https://twitter.com/intent/tweet?url=' + url + '&text=' + text, '_blank');
    if (win) win.opener = null;
  };

  window.copyLink = function() {
    var href = window.location.href;
    var btn = document.querySelector('[onclick="copyLink()"]');

    function onSuccess() {
      if (btn) {
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Copy Link'; }, 2000);
      }
    }
    function onFail() {
      if (btn) {
        btn.textContent = 'Copy failed';
        setTimeout(function() { btn.textContent = 'Copy Link'; }, 2000);
      }
    }

    // Modern API (Chrome, Firefox, Safari 13.1+ on HTTPS)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(href).then(onSuccess).catch(function() {
        fallbackCopy(href, onSuccess, onFail);
      });
    } else {
      fallbackCopy(href, onSuccess, onFail);
    }
  };

  function fallbackCopy(text, onSuccess, onFail) {
    // execCommand fallback — works in Safari on HTTP and older browsers
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      ok ? onSuccess() : onFail();
    } catch (e) {
      document.body.removeChild(ta);
      onFail();
    }
  }

  /* ──────────────────────────────────────────
     Boot
  ────────────────────────────────────────── */
  function init() {
    ThemeController.init();
    NavController.init();
    MobileMenuController.init();
    ScrollAnimator.init();
    FilterController.init();
    HeroController.init();
    NewsletterController.init();
    CardNavController.init();
    ProgressController.init();
    BackToTopController.init();
    ReadTimeController.init();
    ViewTracker.init();
    PopularController.init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
