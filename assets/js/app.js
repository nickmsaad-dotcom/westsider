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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
