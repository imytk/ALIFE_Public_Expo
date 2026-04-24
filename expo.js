/* =========================================================
   ALIFE PUBLIC EXPO — Shared JS
   Placard pager: drives prev/next navigation within a zone's
   placard sections without a page reload.
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {

  document.querySelectorAll('.placard-pager').forEach(pager => {
    const pages = Array.from(pager.querySelectorAll('.placard-page'));
    const prevBtn = pager.querySelector('.pager-prev');
    const nextBtn = pager.querySelector('.pager-next');
    const indicator = pager.querySelector('.page-indicator');
    const dotsContainer = pager.querySelector('.page-dots');
    let current = 0;

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

    // Build dots
    pages.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.className = 'dot' + (i === 0 ? ' active' : '');
      dot.setAttribute('aria-label', `Go to page ${i + 1}`);
      dot.addEventListener('click', () => goTo(i));
      dotsContainer.appendChild(dot);
    });

    function updateButtons() {
      const last = pages.length - 1;
      const penult = last - 1;

      if (prevBtn) prevBtn.disabled = current === 0;

      if (nextBtn) {
        if (current === last) {
          // On the final (interactive) slide — hide the Next button
          nextBtn.style.visibility = 'hidden';
        } else {
          nextBtn.style.visibility = '';
          nextBtn.disabled = false;
          if (current === penult) {
            // Penultimate page: label becomes "Try X →"
            nextBtn.textContent = tryLabel + ' →';
          } else {
            nextBtn.textContent = 'Next →';
          }
        }
      }

      // Zone-nav row: inject once, update each call
      let zoneNav = pager.querySelector('.pager-zone-nav');
      if (current === last && (prevZone || nextZone)) {
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

    function goTo(n) {
      pages[current].classList.remove('active');
      dotsContainer.querySelectorAll('.dot')[current].classList.remove('active');
      current = n;
      pages[current].classList.add('active');
      dotsContainer.querySelectorAll('.dot')[current].classList.add('active');
      if (indicator) indicator.textContent = `${current + 1} / ${pages.length}`;
      updateButtons();
      // Scroll pager into view smoothly
      pager.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    if (prevBtn) prevBtn.addEventListener('click', () => { if (current > 0) goTo(current - 1); });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (current < pages.length - 1) goTo(current + 1); });

    // Init
    goTo(0);
  });

});
