/**
 * lang-toggle.js — EN / JP language switcher for the ALife Online Expo
 *
 * TWO-TIER APPROACH
 * ─────────────────
 * 1. BLOCK switching (placard content):
 *    Sections are structured as two sibling divs:
 *      <div class="lang-en"> ... English content ... </div>
 *      <div class="lang-jp"> ... Japanese content ... </div>
 *    Switching adds/removes the class "lang-jp" on <body>.
 *    CSS handles show/hide: .lang-jp is hidden by default;
 *    body.lang-jp .lang-jp { display:block } and body.lang-jp .lang-en { display:none }.
 *
 * 2. ELEMENT switching (hero labels, short structural strings):
 *    Any element with data-en and data-jp attributes has its
 *    innerHTML swapped directly.
 *
 *    Example:
 *      <h1 data-en="Welcome to Life As It Could Be"
 *          data-jp="あり得る生命の世界へようこそ">Welcome to Life As It Could Be</h1>
 *
 * FALLBACK
 * ────────
 * If an element has data-en but no data-jp, it stays in English.
 *
 * PERSISTENCE
 * ───────────
 * Chosen language stored in localStorage under 'alife-lang'.
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'alife-lang';
  const LANGS = ['en', 'jp'];

  // ── Helpers ──────────────────────────────────────────────────────────────

  function getSavedLang() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return LANGS.includes(saved) ? saved : 'en';
    } catch (_) {
      return 'en';
    }
  }

  function saveLang(lang) {
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (_) {}
  }

  // ── Apply language to the page ────────────────────────────────────────────

  function applyLang(lang) {
    // 1. Update <html lang="…">
    document.documentElement.lang = lang === 'jp' ? 'ja' : 'en';

    // 2. Block switching — toggle body class so CSS shows/hides .lang-en / .lang-jp divs
    if (lang === 'jp') {
      document.body.classList.add('lang-jp');
    } else {
      document.body.classList.remove('lang-jp');
    }

    // 3. Element switching — for short structural strings (hero badge, h1, hero-sub, h2s)
    document.querySelectorAll('[data-en], [data-jp]').forEach(el => {
      const text = el.getAttribute('data-' + lang);
      if (text != null && text !== '') {
        el.innerHTML = text;
      } else if (lang === 'jp') {
        // No JP text — fall back to EN
        const en = el.getAttribute('data-en');
        if (en != null && en !== '') {
          el.innerHTML = en;
        }
      }
    });

    // 4. Update toggle button appearance
    const btn = document.getElementById('lang-toggle-btn');
    if (btn) {
      btn.setAttribute('aria-pressed', lang === 'jp' ? 'true' : 'false');
      btn.querySelector('.lt-en').classList.toggle('lt-active', lang === 'en');
      btn.querySelector('.lt-jp').classList.toggle('lt-active', lang === 'jp');
    }

    // 5. Fire a custom event so other scripts can react if needed
    document.dispatchEvent(new CustomEvent('langchange', { detail: { lang } }));
  }

  // ── Build the toggle button ───────────────────────────────────────────────

  function buildToggle() {
    const btn = document.createElement('button');
    btn.id = 'lang-toggle-btn';
    btn.className = 'lang-toggle';
    btn.setAttribute('aria-label', 'Switch language / 言語を切り替える');
    btn.setAttribute('type', 'button');
    btn.innerHTML =
      '<span class="lt-en">EN</span>' +
      '<span class="lt-sep">|</span>' +
      '<span class="lt-jp">JP</span>';

    btn.addEventListener('click', () => {
      const current = getSavedLang();
      const next = current === 'en' ? 'jp' : 'en';
      saveLang(next);
      applyLang(next);
    });

    return btn;
  }

  // ── Inject into nav ───────────────────────────────────────────────────────

  function init() {
    const nav = document.querySelector('.site-nav .container');
    if (!nav) return;

    const logo = nav.querySelector('.nav-logo');
    const links = nav.querySelector('.nav-links');

    const btn = buildToggle();

    // Insert between logo and nav-links
    if (links) {
      nav.insertBefore(btn, links);
    } else if (logo) {
      logo.insertAdjacentElement('afterend', btn);
    } else {
      nav.appendChild(btn);
    }

    // Apply the saved (or default) language immediately
    const lang = getSavedLang();
    applyLang(lang);
  }

  // Run after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
