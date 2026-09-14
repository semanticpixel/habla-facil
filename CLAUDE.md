# habla fácil — cocktail menu

A single-page cocktail menu for **El Habla Fácil** — the most exclusive cocktail bar
in San Francisco. It is served from GitHub Pages and reached by a QR code on the bar,
so it is read on phones, standing up, in low light.

The site is two pages. `index.html` is the front door — logo and tagline, nothing
else. The menu lives at a random filename and **nothing links to it**: the only way
in is the QR code at the bar. The plan is a different menu file per occasion.

The menu page is **generated**, not hand-written. `menu.json` is the source of truth
for the drink list; `tools/build-menu.py` renders it through `templates/menu.html`
and a GitHub Actions workflow publishes the result. To change the drinks, edit
`menu.json` — never the generated HTML, which is not in the repository.

### About the unguessable URL

This is obscurity, not access control, and it is the right amount of effort for this
QR menu — but know what it does and doesn't do. Nobody will guess
the filename, `robots.txt` and a `noindex` tag keep it out of search results, and no
page links to it. What it does not do: GitHub Pages on a free account requires a
**public repo**, so the filename is visible to anyone who reads `menu.json` or its
commit history. Rotating it later does not erase the old one from history.
If that matters, Pages from a private repo is a paid feature; otherwise treat the
URL as semi-public and don't put anything in the menu you'd mind a stranger reading.

To publish a new menu: run `tools/new-menu` to rotate the filename in `menu.json`,
edit the drinks, push, regenerate the QR. There is no old file to delete — the page
is generated, so the previous URL simply stops existing. `noindex` lives in the
template, so every menu inherits it.

Regenerate the QR with `tools/make-qr.py` after every rotation. It reads the domain
from `CNAME` and the filename from `menu.json`, so it cannot point at a stale URL --
which is the failure that ends with guests scanning into a 404 at the bar.

`new-menu` snapshots the outgoing `menu.json` into `_archive/` before rotating, so
each menu's drink list outlives its URL and can be rebuilt later. Pass
`--date 2026-09-12` to name the snapshot for the night it was actually served —
you rarely retire a menu the same day you pour it, and the default is today. That happens on
rotation only: revising drinks without rotating leaves the previous list in git
history alone. See `_archive/README.md`.

Note that `menu.json` is in the public repository, so the current filename is
visible there just as the HTML file used to be. Same exposure as before, no better
and no worse.

## Files

```
menu.json                      THE DRINK LIST — source of truth, edit this
templates/menu.html            the menu shell: CSS, glass sprite, {{placeholders}}
tools/build-menu.py            menu.json + template -> _site/
index.html                     front door: logo and tagline only, nothing else
404.html                       branded not-found page
CNAME                          custom domain for GitHub Pages
robots.txt                     disallow all — keeps the menu out of search results
assets/logo.svg                hand-lettered "habla fácil" mark, traced from a PNG
assets/glasses/coupe.svg       coupe, two layers
assets/glasses/short.svg       rocks glass, two layers  ← in use
assets/glasses/short-smoothed.svg   alternate rocks glass, drop-in swap
tools/new-menu                 archives menu.json, then rotates to a fresh filename
tools/make-qr.py               QR code for the current menu URL, into _local/
_archive/                      retired menu.json snapshots, never published
_local/                        gitignored scratch for QR codes and other artifacts
tools/check-menu.py            validates a generated menu page
tools/test-reveal.js           tests the tap-to-reveal script from the built page
tools/trace-glass.py           turns a new glass PNG into a matching SVG
.github/workflows/pages.yml    builds and deploys to GitHub Pages
```

The generated menu page lands in `_site/`, which is gitignored. Build it with:

```bash
python3 tools/build-menu.py      # then open the path it prints
```

Neither page makes an external request — no fonts, no script files, no image files.
The menu carries one small inline script, for the tap-to-reveal methods; that is the
only JavaScript in the project. The glass SVGs are inlined as `<symbol>`s and
referenced with `<use>`. The copies in
`assets/` are the same artwork for reuse elsewhere (Instagram, coasters, print).

## How the artwork works

Each glass SVG is two paths in a shared `viewBox="0 0 124 120"`:

```html
<path class="liquid" fill="var(--glass-liquid, #EF676C)" d="…"/>
<path class="ink"    fill="var(--glass-ink, #060405)"    d="…"/>
```

Liquid sits under ink, so **setting one CSS variable recolours the drink**:

```css
.entry { --glass-liquid: #E0842F; }
```

The variable inherits into the `<use>` shadow tree, which is why this works with a
sprite. It does **not** work through `<img src="coupe.svg">` — the SVG has to be in
the DOM.

Both glasses share the same viewBox, a common baseline (y=113) and a common centre
(x=62), so they line up in a list at any size with one CSS rule. The rocks glass is
drawn at 80% inside its box: it is wide and solid where the coupe is tall and mostly
stem, so at equal height it read much heavier. That 0.80 is baked into the path
geometry, not applied in CSS, so the baselines still agree.

`assets/logo.svg` is one path with `fill="currentColor"` and `fill-rule="evenodd"`
(the counters in the letterforms depend on evenodd — don't drop it).

## How the menu is built

Each drink is one entry in the `drinks` array of `menu.json`:

```json
{
  "name": "Yellow",
  "ingredients": "gin, yellow Chartreuse, Suze, lemon",
  "tags": ["floral", "bitter", "sweet"],
  "glass": "coupe",
  "liquid": "#DBB319",
  "flavour": { "x": -0.40, "y": -0.50 },
  "instructions": "Equal parts, shaken."
}
```

`instructions` is the method, rendered into every entry and hidden in CSS. Tapping
the logo three times shows all of them at once and stores that in `localStorage`, so
whoever is pouring taps once and it sticks. Three more taps hide them again.

Each drink renders as one `<article class="entry">` holding three named grid areas:

```
grid-template-areas:
  "leaf  leaf"      writing: number, name, ingredients
  "plate chart"     graph-paper band: the glass, and the flavour plot
```

Same two lines at every width — the phone and desktop layouts are identical in shape,
and the media query only adjusts sizes. Source order is leaf, plate, chart.

**The flavour plot.** Axes are sweet/bitter vertically and sour/spirit-forward
horizontally, after the TasteAtlas flavour map. Each drink's position is a pair in
-1..1 mapped into the 96×96 viewBox:

```
cx = 48 + x * 33     x: -1 sour        → +1 spirit-forward
cy = 48 - y * 33     y: -1 bitter      → +1 sweet
```

The dot is filled with the same colour as that drink's liquid, so the glass and the
plot always agree. **You do not compute `cx`/`cy` by hand** — put the `x`/`y` pair in
`menu.json` and the generator applies the formula. `tools/build-menu.py` rejects any
value outside -1..1, and `tools/check-menu.py` rejects a rendered dot outside the
plot bounds.

Drink numbers come from a CSS counter (`counter-reset` on `.menu`,
`counter-increment` on `.entry`, `decimal-leading-zero` in `.num::before`), so the
markup carries no index and reordering drinks in `menu.json` renumbers them
automatically. A hardcoded number in the HTML is a validation error.

Key CSS variables in `:root`: `--paper`, `--ink`, `--muted`, `--pen` (frame around an
entry), `--seam` (dividers inside one, deliberately about a third of `--pen`),
`--grid`, `--rule`, `--margin`, `--pitch` (rule spacing — body line-height matches it
so the writing sits on the lines, don't change one without the other), `--plot`
(flavour plot size; its cell sizes from it).

## Decisions already made — please don't quietly undo these

- **Graph paper only where something is positioned** (the glass in its cell, the dot
  on its axes). The masthead has none: it was competing with the hand lettering.
- **Two line weights.** A frame around an entry, much lighter seams inside it. When
  every line had the same weight the page flattened into a mesh.
- **Tasting tags are `display: none`.** The markup is still there. They duplicated
  what the plot already says. Deleting that one property brings them back.
- **The glass is 9.5rem against a 10.5rem plot.** Not a mistake — the glass viewBox
  has empty margin baked in, so the two drawings come out the same actual height.
- Lowercase tagline under the logo: the mark already says the name.
- **Padding, margin and borders are logical properties** (`padding-block`,
  `margin-inline`, `border-block-start`, `border-inline-end`). Keep new rules in the
  same idiom. Sizes stay physical (`width`, `max-width`) deliberately, as does the
  `inset` on `.leaf::before` and the `max-width` media query — logical equivalents
  there buy nothing for a page that is only ever laid out left-to-right.
- **The body's block padding is symmetric.** Top and bottom both come from the one
  `clamp()`, so the page is inset by the same amount at each end.
- **The methods are rendered, not fetched.** They ship in the HTML and CSS hides
  them, so the page needs no JavaScript to be complete — the script only toggles a
  class on `<html>`. It reads storage before first paint so a reload does not flash
  the menu without them.
- **The reveal has no visible affordance** on purpose: no pointer cursor, no tap
  highlight, no focus ring. It is a secret for whoever is behind the bar, which also
  means it is pointer-only and not reachable by keyboard.
- **Two drinks sit below a 3.0 contrast ratio** against the paper on purpose: Yellow
  (1.92) and White-Collar Mexican (2.51). Both are pale drinks where the colour was
  chosen over dot legibility. Yellow has nowhere to go — saturation and darkness
  trade against each other directly at that hue.
- **Drink numbers come from a CSS counter, never the markup.** Reordering drinks in
  `menu.json` renumbers them for free.

## Still open

- **Liquid colours as a set.** Chosen one at a time they drift. The current seven
  were picked together: hue separates the three non-red drinks, and the four red
  ones — which cannot separate by hue — are laddered by lightness and chroma, from
  pale strawberry aperitif to deep rye brick. Every pair clears an OKLab distance of
  0.08. Adding a drink means re-checking the set, not picking one more colour.
- **Printing.** Browsers drop background graphics by default, which would take the
  graph paper and the rules with them. Needs a print stylesheet or real borders if
  anyone prints this.
- **Only two glass types exist.** For a highball or a flute, see below.
- **One serif does every job.** A display face for the drink names only is the
  cheapest way to make the page feel as specific as the logo.
- Whether seven repeated plots earn their place, or whether one shared map at the end —
  the way the TasteAtlas reference does it — would say more about how the drinks
  relate. A middle option: keep the small plots, strip their labels, label the axes
  once in a legend.

## Adding a new glass

Draw it the same way as the others: white background, near-black ink, one flat colour
for the liquid, roughly the same pen size.

```bash
pip install pillow scipy numpy vtracer
python3 tools/trace-glass.py highball.png assets/glasses/highball.svg \
    --height 74 --label "Highball glass"
```

`--height` is the drawn height inside the 124×120 box — the coupe is the anchor at
104, the rocks glass is 52.8. The script fails loudly if the drawing overflows the
box rather than letting it clip silently. `--smooth N` rounds wobble out of the liquid
edge; `--thin N` erodes the ink to match pen weight across drawings, at some cost to
character.

Add the result to the sprite in `templates/menu.html` as another `<symbol>`, then add
its name to `GLASSES` in `tools/build-menu.py` so `menu.json` can reference it.

## Deploying

Push to `main`. `.github/workflows/pages.yml` builds the site and deploys it to
GitHub Pages. Pages must be set to **"GitHub Actions"** as its source, not
"Deploy from a branch" — the workflow requests this itself via `configure-pages`,
but the setting is worth checking if a deploy goes missing.

Pull requests build and validate but never publish.

The custom domain is `elhablafacil.com`, stored in the root `CNAME` file, which the
build copies into the published output. The front door is
`https://elhablafacil.com/` and the current menu is whatever `file` says in
`menu.json`.

**Point the QR code at the menu URL, not the front door.** `tools/make-qr.py` does
that for you:

```bash
pip install segno
python3 tools/make-qr.py          # writes _local/menu-qr.{svg,png}
```

It defaults to error-correction level H, which tolerates 30% damage — worth the
denser code for something that gets splashed and handled. Print it 4–5cm square,
keep the four-module quiet zone, and never invert it: some scanners refuse
light-on-dark. Test it on a phone at the brightness and distance people will
actually scan from, and check the menu URL in a private window before service.

`segno` is needed only to make a QR, the same way `tools/trace-glass.py` needs
Pillow. Neither the build nor CI touches them.
