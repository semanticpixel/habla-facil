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

Tapping the logo three times on the menu reveals how each drink is made, and
remembers it. The methods ship in the page and CSS hides them; the only JavaScript
is the toggle.

See `CLAUDE.md` for how the layout, the glass artwork, and the flavour plot fit
together, and for what's still open.

When you rotate to a new menu URL, `tools/new-menu` snapshots the outgoing
`menu.json` into `_archive/` as `<date>-<old-filename>.json`. The drink list is what
is worth keeping — the page is generated, so any archived menu rebuilds by copying
its snapshot over `menu.json` and building. Nothing in `_archive/` is published.

The live site uses `elhablafacil.com`; the QR code should point directly to the
current menu file, not the front door.

To start a fresh menu URL, run `tools/new-menu`. It archives the outgoing
`menu.json` and rotates to a new filename. Then regenerate the QR:

```bash
pip install segno
python3 tools/make-qr.py      # writes _local/menu-qr.{svg,png}
```

`_local/` is gitignored — QR codes are regenerable, and this repository is public.
