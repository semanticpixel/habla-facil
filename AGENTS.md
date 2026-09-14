# Agent Instructions

This repository's detailed project guide lives in [CLAUDE.md](CLAUDE.md). Read it
before changing layout, artwork, menu structure, deployment behavior, or the
unguessable menu URL pattern.

Quick orientation:

- `index.html` is the front door: logo and tagline only.
- The live menu is an unlinked random-filename page reached by QR code.
- **The menu page is generated.** Edit `menu.json`, not HTML. Build with
  `python3 tools/build-menu.py`; the output in `_site/` is gitignored.
- Layout, CSS and the glass sprite live in `templates/menu.html`.
- Keep `robots.txt` and the template's `noindex, nofollow` metadata intact.
- Preserve the El Habla Fácil brand illusion in public-facing docs and copy.
- `tools/build-menu.py` validates `menu.json` and runs `tools/check-menu.py` on the
  rendered page; both must pass.
- Drink numbers come from a CSS counter — never hardcode an index in the markup.
- Drink methods are rendered into the page and hidden in CSS; the inline script only
  toggles a class. Run `node tools/test-reveal.js` after a build if you touch it.
- Liquid colours come in light/dark pairs and must be re-solved per theme, never
  reused or merely lightened. The dot's colour comes from CSS; never add a `fill`.
- `_local/` is gitignored scratch for generated artifacts; never commit its contents.
- Keep changes small and consistent with the existing static HTML/CSS approach.
