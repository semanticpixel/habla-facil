# habla fácil — cocktail menu

A single-page cocktail menu for **El Habla Fácil** — the most exclusive cocktail bar
in San Francisco. It is served from GitHub Pages and reached by a QR code on the bar,
so it is read on phones, standing up, in low light.

The site is two pages. `index.html` is the front door — logo and tagline, nothing
else. The menu lives at a random filename and **nothing links to it**: the only way
in is the QR code at the bar. The plan is a different menu file per occasion.

The menu is a finished layout with **placeholder drinks**. The real drink list is
still to come — replacing it is the next job.

### About the unguessable URL

This is obscurity, not access control, and it is the right amount of effort for this
QR menu — but know what it does and doesn't do. Nobody will guess
`ukln1jc9h9.html`, `robots.txt` and a `noindex` tag keep it out of search results,
and no page links to it. What it does not do: GitHub Pages on a free account requires
a **public repo**, so the filename is visible to anyone who opens the repo's file
list or its commit history. Renaming the file later does not erase it from history.
If that matters, Pages from a private repo is a paid feature; otherwise treat the
URL as semi-public and don't put anything in the menu you'd mind a stranger reading.

To publish a new menu: copy the menu file to a fresh random name, edit the drinks,
delete the old file, regenerate the QR. Keep `noindex` on every one.

## Files

```
index.html                     front door: logo and tagline only, nothing else
ukln1jc9h9.html                the menu, at an unguessable filename
CNAME                          custom domain for GitHub Pages
robots.txt                     disallow all — keeps the menu out of search results
assets/logo.svg                hand-lettered "habla fácil" mark, traced from a PNG
assets/glasses/coupe.svg       coupe, two layers
assets/glasses/short.svg       rocks glass, two layers  ← in use
assets/glasses/short-smoothed.svg   alternate rocks glass, drop-in swap
tools/trace-glass.py           turns a new glass PNG into a matching SVG
```

Neither page makes external requests — no fonts, no scripts, no image files. The
glass SVGs are inlined as `<symbol>`s and referenced with `<use>`. The copies in
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

Each drink is one `<article class="entry">` holding three named grid areas:

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
plot always agree. **If you add a drink, compute `cx`/`cy` with that formula** rather
than eyeballing coordinates.

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

## Still open

- **The real drink list.** Six placeholders (Paper Plane, Last Word, Clover Club, Old
  Fashioned, Negroni, Whiskey Sour) with invented flavour positions.
- **Liquid colours as a set.** Chosen one at a time they will drift. Six unrelated
  colours down a cream page get noisy — pick them together.
- **Printing.** Browsers drop background graphics by default, which would take the
  graph paper and the rules with them. Needs a print stylesheet or real borders if
  anyone prints this.
- **Drinks are hardcoded in the HTML.** If the list churns a lot, lifting them into a
  JSON array with a small render function would make edits safer — the plot maths is
  the part that is easy to get wrong by hand.
- **Only two glass types exist.** For a highball or a flute, see below.
- **One serif does every job.** A display face for the drink names only is the
  cheapest way to make the page feel as specific as the logo.
- Whether six repeated plots earn their place, or whether one shared map at the end —
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
character. Add the result to the sprite in `index.html` as another `<symbol>`.

## Deploying

Static site, no build step. Push, enable Pages on the default branch at root. The
custom domain is `elhablafacil.com`, stored in the root `CNAME` file. The front door
is `https://elhablafacil.com/` and the current menu is
`https://elhablafacil.com/ukln1jc9h9.html`.

**Point the QR code at the menu URL, not the front door.** Test it on a phone at the
brightness and distance people will actually scan it, and check the menu URL in a
private window before service — a typo in the filename is a 404 at the bar.
