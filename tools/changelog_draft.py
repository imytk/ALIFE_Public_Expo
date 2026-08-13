#!/usr/bin/env python3
"""
changelog_draft.py — draft Change Log entries from git history.

WHY THIS EXISTS
───────────────
changelog.html is written for visitors, not developers: entries read like
"Zone 5: fixed a bug showing two sets of navigation buttons", not like
"Update zone5.html". Raw commit messages are too terse to publish as-is,
so this script does the mechanical half of the job — working out which
dates are missing from the Change Log, which zones/pages each commit
touched, and laying that out in the exact card markup the page uses —
and leaves the wording to a human.

The output is a DRAFT. Every generated <li> is a starting point to be
rewritten in visitor-facing language before it ships.

USAGE
─────
    python3 tools/changelog_draft.py              # print draft to stdout
    python3 tools/changelog_draft.py --write      # insert into changelog.html
    python3 tools/changelog_draft.py --since 2026-07-30
    python3 tools/changelog_draft.py --check      # exit 1 if entries missing

HOW "MISSING" IS DECIDED
────────────────────────
The newest <h3> date heading in changelog.html is treated as the
high-water mark. Any commit dated after it is considered undocumented.
Commits that only touch changelog.html (or files in EXCLUDE) are ignored,
so regenerating the Change Log never generates a new entry about itself.
"""

import argparse
import datetime as dt
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "changelog.html"

# Commits touching only these paths never produce an entry.
EXCLUDE = {"changelog.html", ".github", "tools", ".gitignore", "CNAME"}

ZONE_TITLES = {
    "1": "Welcome to Life As It Could Be",
    "2": "The Line Between Living and Non-Living",
    "3": "History of Artificial Life",
    "4": "Emergence & Self-Organisation",
    "5": "Evolution & Adaptation",
    "6": "Complexity From Simplicity",
    "7": "Diverse ALife — Hard, Soft, Wet",
    "8": "ALife and Society",
    "9": "The Future of Artificial Life",
}

PAGE_NAMES = {
    "index.html": "Homepage",
    "faq.html": "FAQ page",
    "contact.html": "Contact page",
    "style.css": "Site styling",
    "expo.js": "Site behaviour",
    "content-loader.js": "Zone content loading",
    "lang-toggle.js": "Language toggle",
    "hero-bg.js": "Hero backgrounds",
}


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def latest_documented_date():
    """Newest date already present in changelog.html, or None."""
    if not CHANGELOG.exists():
        return None
    html = CHANGELOG.read_text(encoding="utf-8")
    dates = []
    for raw in re.findall(r"<h3>([^<]+)</h3>", html):
        cleaned = raw.split("—")[0].strip()
        for fmt in ("%B %d, %Y", "%d %B %Y"):
            try:
                dates.append(dt.datetime.strptime(cleaned, fmt).date())
                break
            except ValueError:
                continue
    return max(dates) if dates else None


def area_for(path):
    """Human-readable area name for a changed file, or None to ignore."""
    m = re.match(r"^zone(\d)\.html$", path) or re.match(r"^content/zone(\d)/", path)
    if m:
        n = m.group(1)
        return f"Zone {n}: {ZONE_TITLES.get(n, '')}".rstrip(": ")
    if path in PAGE_NAMES:
        return PAGE_NAMES[path]
    if path.split("/")[0] in EXCLUDE:
        return None
    return None  # source material, docs, notes — not visitor-facing


def collect(since):
    """Commits after `since`, grouped by date (newest date first)."""
    # \x1f (unit separator): unlike \x1e, Python's splitlines() does not
    # treat it as a line boundary, so it survives the split below.
    sep = "\x1f"
    fmt = f"%H{sep}%ad{sep}%s"
    args = ["log", "--date=short", f"--pretty={fmt}", "--no-merges"]
    if since:
        args.append(f"--since={since.isoformat()}")
    by_date = OrderedDict()
    for line in git(*args).splitlines():
        if not line.strip():
            continue
        sha, date_s, subject = line.split(sep, 2)
        date = dt.date.fromisoformat(date_s)
        if since and date <= since:
            continue
        files = [f for f in git("show", "--name-only", "--pretty=", sha).splitlines() if f]
        if not files:
            continue
        # Skip commits that only touch infrastructure/the changelog itself.
        if all(f.split("/")[0] in EXCLUDE for f in files):
            continue
        areas = OrderedDict.fromkeys(a for a in (area_for(f) for f in files) if a)
        by_date.setdefault(date, []).append(
            {"sha": sha[:7], "subject": subject, "areas": list(areas), "files": files}
        )
    return by_date


def render(by_date):
    """Draft card markup, newest date first, matching changelog.html."""
    out = []
    for date in sorted(by_date, reverse=True):
        commits = by_date[date]
        heading = date.strftime("%B %-d, %Y") if sys.platform != "win32" else date.strftime("%B %d, %Y")
        out.append('<!-- ── DRAFT: rewrite the wording below, then delete this comment ── -->')
        out.append('<div class="card placard-text" style="margin-bottom:1.25rem;">')
        out.append(f"<h3>{heading}</h3>")
        out.append("<ul>")
        for c in commits:
            areas = c["areas"]
            # A commit touching most of the site reads better as one phrase
            # than as a list of every zone it happened to touch.
            if len(areas) >= 6:
                label = "Site-wide"
            else:
                label = "; ".join(areas)
            prefix = f"{label} — " if label else ""
            out.append(
                f"<li>{prefix}{c['subject']}."
                f"  <!-- {c['sha']} · {', '.join(c['files'][:8])} --></li>"
            )
        out.append("</ul>")
        out.append("</div>")
        out.append("")
    return "\n".join(out)


def write_into_changelog(draft):
    """Insert draft cards directly above the newest existing entry card."""
    html = CHANGELOG.read_text(encoding="utf-8")
    anchor = '<div class="card placard-text" style="margin-bottom:1.25rem;">'
    i = html.index(anchor)
    CHANGELOG.write_text(html[:i] + draft + "\n" + html[i:], encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="YYYY-MM-DD; default = newest date in changelog.html")
    ap.add_argument("--write", action="store_true", help="insert the draft into changelog.html")
    ap.add_argument("--check", action="store_true", help="exit 1 if undocumented commits exist")
    args = ap.parse_args()

    since = dt.date.fromisoformat(args.since) if args.since else latest_documented_date()
    by_date = collect(since)

    if not by_date:
        print(f"changelog is up to date (latest documented entry: {since})", file=sys.stderr)
        return 0

    draft = render(by_date)
    if args.write:
        write_into_changelog(draft)
        print(f"inserted {len(by_date)} draft date block(s) into changelog.html", file=sys.stderr)
    else:
        print(draft)
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
