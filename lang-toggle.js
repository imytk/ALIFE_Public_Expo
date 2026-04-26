/**
 * lang-toggle.js — EN / JP language switcher for the ALife Online Expo
 *
 * HOW TO MARK TRANSLATABLE TEXT
 * ─────────────────────────────
 * Add data-en and data-jp attributes to any element whose *text content*
 * should switch. The element's current innerHTML is used as the EN default
 * if data-en is not explicitly set.
 *
 * Examples:
 *
 *   <h2 data-en="What is Life?" data-jp="生命とは何か？">What is Life?</h2>
 *
 *   <p data-en="English paragraph text." data-jp="日本語の段落テキスト。">
 *     English paragraph text.
 *   </p>
 *
 *   <!-- For elements with inner HTML markup, use data-en/data-jp with HTML: -->
 *   <p data-en="<strong>Bold</strong> word." data-jp="<strong>太字</strong>の言葉。">
 *     <strong>Bold</strong> word.
 *   </p>
 *
 * FALLBACK
 * ────────
 * If an element has data-en but no data-jp, it stays in English regardless
 * of the selected language (no blank content).
 *
 * PERSISTENCE
 * ───────────
 * The chosen language is stored in localStorage under 'alife-lang' and
 * restored automatically on every page load.
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
    // Update <html lang="…">
    document.documentElement.lang = lang === 'jp' ? 'ja' : 'en';

    // Swap all translatable elements
    document.querySelectorAll('[data-en], [data-jp]').forEach(el => {
      const text = el.getAttribute('data-' + lang);
      if (text != null && text !== '') {
        el.innerHTML = text;
      } else if (lang === 'jp') {
        // No JP text available — fall back to EN (don't blank the element)
        const en = el.getAttribute('data-en');
        if (en != null && en !== '') {
          el.innerHTML = en;
        }
      }
    });

    // Update toggle button appearance
    const btn = document.getElementById('lang-toggle-btn');
    if (btn) {
      btn.setAttribute('aria-pressed', lang === 'jp' ? 'true' : 'false');
      btn.querySelector('.lt-en').classList.toggle('lt-active', lang === 'en');
      btn.querySelector('.lt-jp').classList.toggle('lt-active', lang === 'jp');
    }

    // Fire a custom event so other scripts can react if needed
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
