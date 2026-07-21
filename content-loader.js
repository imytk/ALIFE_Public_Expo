/**
 * content-loader.js — loads placard text from per-zone, per-language
 * content files and renders it into a zone's placard pager.
 *
 * WHY <script> TAGS INSTEAD OF fetch()
 * ─────────────────────────────────────
 * This site is often opened directly as a local file (file://...), not
 * through a web server. Browsers block fetch()/XHR to local files under
 * file:// for security reasons (CORS), but plain <script src="..."> tags
 * are NOT subject to that restriction — so content is shipped as small
 * JS files that self-register into a global registry, and loaded by
 * injecting a <script> tag rather than fetching JSON. This works
 * identically whether the site is opened by double-clicking the HTML
 * file or served over http(s).
 *
 * HOW IT WORKS
 * ────────────
 * A placard pager opts in to dynamic content with a `data-zone` attribute:
 *
 *   <div class="placard-pager" data-zone="zone1" ...>
 *     <div class="placard-pages"></div>   <!-- left empty in the HTML -->
 *     ...
 *   </div>
 *
 * Content lives in content/<zone>/<lang>.js — each file registers an
 * array of page objects onto window.__ALIFE_CONTENT__:
 *
 *   window.__ALIFE_CONTENT__ = window.__ALIFE_CONTENT__ || {};
 *   window.__ALIFE_CONTENT__['zone1:en'] = [
 *     { "id": "welcome", "title": "...", "body": "<p>...</p>", "wrapCard": true },
 *     ...
 *   ];
 *
 *   - id        short slug, useful for debugging/anchors (not required)
 *   - title     page heading (plain text — do not include markup)
 *   - body      inner HTML for the page. Standard placard text should just
 *               be paragraphs/lists; pages that need custom layout (e.g. an
 *               embedded interactive + callout) can include that markup
 *               directly.
 *   - wrapCard  true (default) wraps body in <div class="card placard-text">.
 *               Set false for pages that bring their own layout (like the
 *               "try it" interactive page) so body renders unwrapped.
 *
 * ADDING A LANGUAGE: drop a new content/<zone>/<lang>.js file (same ids
 * and page order as the others, registering under 'zone:<lang>') — no
 * HTML edits required anywhere. The language actually shown is whatever
 * lang-toggle.js has stored under the 'alife-lang' localStorage key; this
 * script re-renders whenever lang-toggle.js fires its 'langchange' event.
 *
 * FALLBACK: if content/<zone>/<lang>.js is missing (language not yet
 * translated for this zone), falls back to content/<zone>/en.js.
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'alife-lang';
  const REGISTRY = (window.__ALIFE_CONTENT__ = window.__ALIFE_CONTENT__ || {});

  function getSavedLang() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved || 'en';
    } catch (_) {
      return 'en';
    }
  }

  function buildPage(pageData) {
    const div = document.createElement('div');
    div.className = 'placard-page';
    if (pageData.id) div.dataset.pageId = pageData.id;

    const h2 = document.createElement('h2');
    h2.className = 'section-title-centred';
    h2.textContent = pageData.title || '';
    div.appendChild(h2);

    if (pageData.wrapCard === false) {
      const temp = document.createElement('div');
      temp.innerHTML = pageData.body || '';
      while (temp.firstChild) div.appendChild(temp.firstChild);
    } else {
      const card = document.createElement('div');
      card.className = 'card placard-text';
      card.innerHTML = pageData.body || '';
      div.appendChild(card);
    }

    return div;
  }

  // Loads content/<zone>/<lang>.js via a <script> tag (not fetch — see
  // header comment) and resolves with the page array it registers.
  function loadContent(zone, lang) {
    const key = `${zone}:${lang}`;
    if (REGISTRY[key]) return Promise.resolve(REGISTRY[key]);

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = `content/${zone}/${lang}.js`;
      script.onload = () => {
        if (REGISTRY[key]) {
          resolve(REGISTRY[key]);
        } else {
          reject(new Error(`content/${zone}/${lang}.js loaded but did not register '${key}'`));
        }
      };
      script.onerror = () => reject(new Error(`failed to load content/${zone}/${lang}.js`));
      document.head.appendChild(script);
    });
  }

  function render(pager, lang) {
    const zone = pager.dataset.zone;
    if (!zone) return;

    const pagesContainer = pager.querySelector('.placard-pages');
    if (!pagesContainer) return;

    loadContent(zone, lang)
      .catch(() => loadContent(zone, 'en'))
      .then(pages => {
        pagesContainer.innerHTML = '';
        pages.forEach(p => pagesContainer.appendChild(buildPage(p)));

        // Rebuild the pager chrome (dots, prev/next state) around the new pages.
        if (window.AlifeExpo && typeof window.AlifeExpo.initPager === 'function') {
          window.AlifeExpo.initPager(pager);
        }
      })
      .catch(err => {
        console.error('content-loader: failed to load content for', zone, lang, err);
      });
  }

  function init() {
    const pagers = document.querySelectorAll('.placard-pager[data-zone]');
    if (!pagers.length) return;

    const lang = getSavedLang();
    pagers.forEach(pager => render(pager, lang));

    document.addEventListener('langchange', e => {
      const newLang = (e.detail && e.detail.lang) || getSavedLang();
      pagers.forEach(pager => render(pager, newLang));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
