# habla fácil

Cocktail menu for El Habla Fácil, served as a static page and reached by a QR code.

Two pages: `index.html` is the front door, and the menu sits at a random filename
that nothing links to, reachable only by the QR code at the bar. No build step, no
dependencies — deploy by enabling GitHub Pages on the default branch at root.

Drinks in the menu page are placeholders. See `CLAUDE.md` for how the layout, the
glass artwork, and the flavour plot fit together, and for what's still open.

For retired menus, move the old HTML file into `_archive/`. GitHub Pages ignores
underscore-prefixed folders, so archived files stay in the public repository without
being served on the live site.

The live site uses `elhablafacil.com`; the QR code should point directly to the
current menu file, not the front door.
