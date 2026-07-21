/* =========================================================
   ALIFE PUBLIC EXPO — Shared JS
   Placard pager: drives prev/next navigation within a zone's
   placard sections without a page reload.

   Pagers whose .placard-page elements are already in the HTML
   at load time (most zones, today) are initialized automatically
   below. Pagers marked data-zone="..." get their pages injected
   dynamically by content-loader.js, which calls
   AlifeExpo.initPager(pager) itself once content is fetched —
   and again any time the language changes, since the pages get
   rebuilt. initPager() is safe to call more than once on the
   same pager: it re-reads whatever .placard-page elements are
   currently inside it and rebuilds the dots/state around them.
   ========================================================= */

function initPager(pager) {
  const pages = Array.from(pager.querySelectorAll('.placard-page'));
  if (!pages.length) return;

  const prevBtn = pager.querySelector('.pager-prev');
  const nextBtn = pager.querySelector('.pager-next');
  const indicator = pager.querySelector('.page-indicator');
  const dotsContainer = pager.querySelector('.page-dots');

  // Optional data attributes on .placard-pager:
  //   data-try-label  — label for the final-page "Try" button (e.g. "Try Boids")
  //   data-next-zone  — href for the next-zone link (e.g. "zone5.html")
  //   data-next-label — text for the next-zone link (e.g. "Zone 5: Evolution →")
  //   data-prev-zone  — href for the prev-zone link (e.g. "zone3.html")
  //   data-prev-label — text for the prev-zone link (e.g. "← Zone 3: History")
  const tryLabel  = pager.dataset.tryLabel  || 'Try It';
  const nextZone  = pager.dataset.nextZone  || null;
  const nextLabel = pager.dataset.nextLabel || 'Next Zone →';
  const prevZone  = pager.dataset.prevZone  || null;
  const prevLabel = pager.dataset.prevLabel || '← Prev Zone';

  // State lives on the pager element so the (once-bound) prev/next
  // listeners always act on the latest pages/current index, even
  // after content-loader.js rebuilds the pages for a language switch.
  const state = { pages, current: 0 };
  pager._pagerState = state;

  function updateButtons() {
    const last = state.pages.length - 1;
    const penult = last - 1;

    if (prevBtn) prevBtn.disabled = state.current === 0;

    if (nextBtn) {
      if (state.current === last) {
        // On the final (interactive) slide — hide the Next button
        nextBtn.style.visibility = 'hidden';
      } else {
        nextBtn.style.visibility = '';
        nextBtn.disabled = false;
        if (state.current === penult) {
          // Penultimate page: label becomes "Try X →"
          nextBtn.textContent = tryLabel + ' →';
        } else {
          nextBtn.textContent = 'Next →';
        }
      }
    }

    // Zone-nav row: inject once, update each call
    let zoneNav = pager.querySelector('.pager-zone-nav');
    if (state.current === last && (prevZone || nextZone)) {
      if (!zoneNav) {
        zoneNav = document.createElement('div');
        zoneNav.className = 'pager-zone-nav zone-nav';
        zoneNav.style.marginTop = '1.5rem';
        if (prevZone) {
          const a = document.createElement('a');
          a.href = prevZone;
          a.className = 'zone-nav-btn';
          a.textContent = prevLabel;
          zoneNav.appendChild(a);
        }
        if (nextZone) {
          const a = document.createElement('a');
          a.href = nextZone;
          a.className = 'zone-nav-btn primary';
          a.textContent = nextLabel;
          zoneNav.appendChild(a);
        }
        // Insert after the placard-page-nav
        const nav = pager.querySelector('.placard-page-nav');
        nav.insertAdjacentElement('afterend', zoneNav);
      }
      zoneNav.style.display = 'flex';
    } else if (zoneNav) {
      zoneNav.style.display = 'none';
    }
  }

  function goTo(n, scroll) {
    state.pages[state.current].classList.remove('active');
    dotsContainer.querySelectorAll('.dot')[state.current].classList.remove('active');
    state.current = n;
    state.pages[state.current].classList.add('active');
    dotsContainer.querySelectorAll('.dot')[state.current].classList.add('active');
    if (indicator) indicator.textContent = `${state.current + 1} / ${state.pages.length}`;
    updateButtons();
    // Only scroll when the user navigates — not on the initial page load
    if (scroll) pager.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  state.goTo = goTo;

  // (Re)build dots for the current set of pages.
  dotsContainer.innerHTML = '';
  state.pages.forEach((_, i) => {
    const dot = document.createElement('button');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.setAttribute('aria-label', `Go to page ${i + 1}`);
    dot.addEventListener('click', () => pager._pagerState.goTo(i, true));
    dotsContainer.appendChild(dot);
  });

  // Bind prev/next listeners once per pager — they read pager._pagerState
  // fresh on every click, so they stay correct across content rebuilds.
  if (!pager.dataset.pagerBound) {
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        const st = pager._pagerState;
        if (st.current > 0) st.goTo(st.current - 1, true);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const st = pager._pagerState;
        if (st.current < st.pages.length - 1) st.goTo(st.current + 1, true);
      });
    }
    pager.dataset.pagerBound = '1';
  }

  // Init — no scroll, page loads at top
  goTo(0, false);
}

window.AlifeExpo = window.AlifeExpo || {};
window.AlifeExpo.initPager = initPager;

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.placard-pager').forEach(pager => {
    // Pagers with data-zone get their pages injected by content-loader.js,
    // which calls initPager() itself once the content arrives.
    if (pager.dataset.zone) return;
    initPager(pager);
  });
});
