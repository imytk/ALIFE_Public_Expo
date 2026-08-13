# ALIFE_Public_Expo

Each folder corresponds to a single zone in the ALife Public Expo. Generally speaking, each zone needs the following contents:

- Exhibit Placard/Label (In English and Japanese) outlining the zone theme.
- Short description of the video/interactive elements (in English and Japanese)
- Video compilation (mp4 format)
- Python Script(s) or other file(s) for interactive component
## Keeping the Change Log up to date

`changelog.html` is visitor-facing, so entries are written in plain language
("Zone 5: fixed a bug showing two sets of navigation buttons"), not copied
from commit messages ("Update zone5.html"). To keep that quality without
writing entries from memory, drafting is automated but publishing is not.

`tools/changelog_draft.py` compares the newest date heading in
`changelog.html` against `git log`, and lays out card markup for any dates
that are missing — grouping commits by date, naming the zones and pages each
one touched, and leaving the commit subject in place as a starting point.

```sh
python3 tools/changelog_draft.py            # preview the draft
python3 tools/changelog_draft.py --write    # insert it into changelog.html
python3 tools/changelog_draft.py --check    # exit 1 if entries are missing
```

The `Draft Change Log` GitHub Action runs the same script on every push to
`main` and, when entries are missing, opens (or updates) a pull request on
the `chore/changelog-draft` branch. **Nothing reaches the live site until
that PR is edited and merged** — rewrite each `<li>` for a reader, delete the
`<!-- DRAFT -->` and `<!-- sha · files -->` marker comments, and drop anything
not worth announcing.

Commits touching only `changelog.html`, `tools/`, `.github/`, or `CNAME` are
ignored, so regenerating the Change Log never produces an entry about itself.
