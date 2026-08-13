# ALife Online Expo — technical crib sheet

Quick answers for Q&A. Written to be skimmed while someone is talking at you.

---

## The 20-second answer

A **static website**. No server, no database, no build step, no framework, no
dependencies. Plain HTML, CSS and vanilla JavaScript, served by GitHub Pages at
**alife-expo.org**. Roughly 1,200 lines of JavaScript and 900 of CSS in total.

Three things run on top: **YouTube** for the videos, **third-party iframes** for
the large interactives (so we don't maintain other people's simulations), and
**Knight Lab TimelineJS** driven from a Google Sheet for the Zone 3 timeline.

---

## "Are those hero animations videos?"

**No — they are live simulations running in your browser right now.** Ten of
them, one per page, and each matches the zone it sits behind.

| Page | Simulation | What it actually is |
|---|---|---|
| Home | `boids` | Reynolds flocking — separation, alignment, cohesion |
| Zone 1 | `gol` | A real Conway's Game of Life on a toroidal grid |
| Zone 2 | `slime` | 600 agents depositing and following pheromone trails on a diffusing grid (physarum) |
| Zone 3 | `clock` | Clockwork automaton, for the history of mechanical life |
| Zone 4 | `boids4` | Flocking again, tuned for the emergence zone |
| Zone 5 | `phylo` | A phylogenetic tree growing and branching |
| Zone 6 | `rule30` | Elementary cellular automaton, Rule 30 — chaos from one black cell |
| Zone 7 | `matrix` | Cascading code, for hard/soft/wet ALife |
| Zone 8 | `forest` | Seven L-system trees growing and swaying in wind |
| Zone 9 | `future` | Star field with rotating DNA helices |

**How it works.** Each page's hero tag names its simulation:

```html
<header class="hero" data-hero-bg="gol">
```

On load, `hero-bg.js` creates a `<canvas>`, inserts it behind the hero content,
and looks that name up in a `SIM` registry. Each registry entry is a **factory
function**: it builds its own private state and returns a `tick()` function. A
`requestAnimationFrame` loop calls `tick()` about 60 times a second.

**Two tricks worth naming if pressed:**

- Each frame paints a *translucent* dark rectangle rather than clearing the
  canvas. That is what leaves motion trails behind the boids.
- After drawing, a gradient `tint()` is painted over the top, which keeps the
  white headline text readable against a busy animation.

**Performance.** The loop is cancelled entirely when the browser tab is hidden
(`visibilitychange`), and each simulation is rebuilt on window resize.

**To add one:** write a factory in `hero-bg.js`, then add the attribute to a page.
Two edits, no wiring.

---

## "How does the language toggle work?"

Three mechanisms, layered in the order they were built:

1. **Content files (the main one).** All placard text lives in
   `content/<zone>/<lang>.js`. `content-loader.js` injects the right file at
   runtime and renders the pages.
2. **Element-level.** Anything with `data-en` / `data-jp` attributes has its
   contents swapped — hero titles, badges, subtitles.
3. **Block-level (legacy).** Sibling `.lang-en` / `.lang-jp` divs, shown and
   hidden by CSS when a `lang-jp` class is toggled on `<body>`.

The EN|JP button is injected into the nav by JavaScript, so no page has to
include it. The choice persists in `localStorage`. Switching also sets
`<html lang="ja">` so screen readers change pronunciation, and fires a
`langchange` event that tells the content loader to re-render.

**Missing translations fall back to English automatically**, so a partial
translation is safe to ship.

### "How hard is a third language?"

Split the answer — it is the honest and more useful reply:

> **Translating is easy; adding the language slot is a one-off piece of coding.**

**Easy (this is the designed path, and what a volunteer would do):** copy the
nine `content/zone*/en.js` files to `fr.js`, translate the strings inside. No
HTML touched anywhere. Roughly an afternoon per zone.

**Needs a developer, once:** the language list `['en','jp']` is hardcoded, the
button is a two-way toggle rather than a picker, and hero titles use
`data-en`/`data-jp` attributes spread across ten HTML files. Widening that is an
evening of work. **After that, the fourth and fifth languages are content files
only.**

We are actively looking for volunteer translators — worth saying out loud.

---

## Likely follow-up questions

**"Why ship content as `.js` files instead of JSON?"**
Browsers block `fetch()` under `file://`. Shipping content as scripts that
register themselves into a global object means the whole expo works if you
download the folder and double-click a page — useful in a venue with bad wifi.

**"What happens when an external simulation disappears?"**
It has already happened. The Zone 1 Game of Life host began refusing to be
embedded in other sites, so it was swapped for `copy.sh/life`. Because each
interactive is one URL in one content file, replacing it is a one-line change.
There is a tester page (`tools/embed-test.html`) that loads candidate
simulations in iframes to check they can be embedded before we commit to one.

**"Is the timeline hard to update?"**
No — it is a Google Sheet. Add a row, and the timeline updates. No deploy.

**"How do you keep the change log current?"**
A script drafts entries from the site's revision history and opens a pull
request; the wording is then rewritten by a human before it goes live.
Automation drafts, a person publishes.

**"Does it work on phones?"**
Yes, responsive throughout — the interactive frames shrink at narrow widths.

**"What's it built with / can I have it?"**
No framework at all, deliberately: it has to still run in five years with nobody
maintaining a toolchain. Licensed **CC BY-NC-SA 4.0**, source on GitHub.

---

## Numbers, if you need them

- **9 zones**, 10 pages including the homepage
- **10 live hero simulations**
- **2 languages**, full parity
- `hero-bg.js` 775 lines · `style.css` ~880 · `expo.js` 152 ·
  `content-loader.js` 155 · `lang-toggle.js` 145
- **0 dependencies, 0 build steps, 0 servers**

---

## If something breaks live

- An interactive shows "refused to connect" → that site is blocking embedding.
  Use the "Open full screen ↗" link above the frame instead.
- Placard text doesn't load → almost always the language file; the site falls
  back to English on its own.
- Hero is a flat colour → the canvas hasn't booted; harmless, text still reads.
