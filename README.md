# habla fácil

Cocktail menu for El Habla Fácil, served as a static page and reached by a QR code.

Two pages: `index.html` is the front door, and the menu sits at a random filename
that nothing links to, reachable only by the QR code at the bar.

The menu page is generated. `menu.json` holds the drink list, `tools/build-menu.py`
renders it through `templates/menu.html`, and a GitHub Actions workflow publishes the
result to Pages on every push to `main`. No dependencies beyond Python 3.

```bash
python3 tools/build-menu.py      # builds into _site/, prints the menu path
```

To change the drinks, edit `menu.json` — the generated HTML is not in the repository.

See `CLAUDE.md` for how the layout, the glass artwork, and the flavour plot fit
together, and for what's still open.

Retired menus live in git history rather than on disk, since the page is generated.
`_archive/` still holds any menu HTML kept from before the generator.

The live site uses `elhablafacil.com`; the QR code should point directly to the
current menu file, not the front door.

To start a fresh menu URL, run `tools/new-menu`. It rotates the filename in
`menu.json` and prints the name to use for the next QR code.
