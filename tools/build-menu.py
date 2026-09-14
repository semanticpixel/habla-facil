#!/usr/bin/env python3
"""Build the menu page from menu.json and templates/menu.html.

The menu HTML is generated, not committed. Everything that gets published --
the front door, the 404 page, the artwork -- is assembled into an output
directory ready for GitHub Pages.

    python3 tools/build-menu.py              # build into _site/
    python3 tools/build-menu.py --out dist   # build somewhere else

Prints the path of the generated menu page to stdout; diagnostics go to stderr.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GLASSES = {"coupe", "short"}
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MENU_FILENAME = re.compile(r"^[A-Za-z0-9_-]{1,64}\.html$")

# Published alongside the generated menu. An allowlist, not a denylist: anything
# added to the repository stays unpublished until it is named here.
STATIC_FILES = ("index.html", "404.html", "robots.txt", "CNAME")
STATIC_DIRS = ("assets",)

# The drink number comes from a CSS counter, so the markup carries no index and
# reordering drinks in menu.json cannot desynchronise the numbering.
#
# The method is rendered into every entry and hidden in CSS. Tapping the logo three
# times reveals it -- nothing is fetched or assembled at runtime, so the page works
# the same with scripting off, minus the secret.
ENTRY = """      <article class="entry" style="--glass-liquid: light-dark({light}, {dark})">
        <div class="leaf">
          <h2><span class="num"></span> {name}</h2>
          <p class="ing">{ingredients}</p>
          <p class="recipe">{instructions}</p>
          <p class="tags">{tags}</p>
        </div>
        <div class="plate">
          <svg class="glass" aria-hidden="true"><use href="#glass-{glass}"/></svg>
        </div>
        <div class="chart">
          <svg class="plot" viewBox="0 0 96 96" aria-hidden="true">
            <line x1="48" y1="10" x2="48" y2="86"/>
            <line x1="10" y1="48" x2="86" y2="48"/>
            <circle class="dot" cx="{cx}" cy="{cy}" r="5.5"/>
            <text x="48" y="6"  class="ax" text-anchor="middle">sweet</text>
            <text x="48" y="94" class="ax" text-anchor="middle">bitter</text>
            <text x="1"  y="44" class="ax">sour</text>
            <text x="95" y="44" class="ax" text-anchor="end">spirit</text>
          </svg>
        </div>
      </article>
"""


def liquids(drink):
    """The drink's colour for each theme.

    A bare string is the light colour and doubles as the dark one, so menus
    archived before dark mode still build -- they just look the same in both.
    """
    value = drink["liquid"]
    if isinstance(value, str):
        return value, value
    return value["light"], value["dark"]


def plot_position(flavour):
    """Map a flavour pair in -1..1 into the 96x96 plot viewBox.

    x: -1 sour .. +1 spirit-forward      y: -1 bitter .. +1 sweet
    """
    return (
        round(48 + float(flavour["x"]) * 33, 1),
        round(48 - float(flavour["y"]) * 33, 1),
    )


def validate(menu):
    """Check menu.json before rendering, so failures name the drink."""
    errors = []

    if not MENU_FILENAME.match(menu.get("file", "")):
        errors.append(f'"file" must be a plain .html filename, got {menu.get("file")!r}')
    if not str(menu.get("note", "")).strip():
        errors.append('"note" is empty')

    drinks = menu.get("drinks")
    if not isinstance(drinks, list) or not drinks:
        errors.append('"drinks" must be a non-empty list')
        return errors

    seen = set()
    for i, drink in enumerate(drinks, start=1):
        where = f"drink {i} ({drink.get('name') or 'unnamed'})"

        name = str(drink.get("name", "")).strip()
        if not name:
            errors.append(f"{where}: missing name")
        elif name.casefold() in seen:
            errors.append(f"{where}: duplicate name")
        else:
            seen.add(name.casefold())

        for field in ("ingredients", "instructions"):
            if not str(drink.get(field, "")).strip():
                errors.append(f"{where}: missing {field}")

        liquid = drink.get("liquid")
        if isinstance(liquid, str):
            if not HEX.match(liquid):
                errors.append(f"{where}: liquid must be a #rrggbb colour, got {liquid!r}")
        elif isinstance(liquid, dict):
            for theme in ("light", "dark"):
                if not HEX.match(str(liquid.get(theme, ""))):
                    errors.append(
                        f"{where}: liquid.{theme} must be a #rrggbb colour, got {liquid.get(theme)!r}"
                    )
        else:
            errors.append(f"{where}: liquid must be a colour or a light/dark pair, got {liquid!r}")

        if drink.get("glass") not in GLASSES:
            errors.append(f"{where}: glass must be one of {sorted(GLASSES)}, got {drink.get('glass')!r}")

        flavour = drink.get("flavour")
        if not isinstance(flavour, dict):
            errors.append(f"{where}: missing flavour")
            continue
        for axis in ("x", "y"):
            try:
                value = float(flavour[axis])
            except (KeyError, TypeError, ValueError):
                errors.append(f"{where}: flavour {axis} is not a number")
                continue
            if not -1 <= value <= 1:
                errors.append(f"{where}: flavour {axis} is {value}, outside -1..1")

    return errors


def render(menu):
    template = (ROOT / "templates" / "menu.html").read_text(encoding="utf-8")

    entries = ""
    for drink in menu["drinks"]:
        cx, cy = plot_position(drink["flavour"])
        light, dark = liquids(drink)
        entries += ENTRY.format(
            light=light,
            dark=dark,
            name=html.escape(drink["name"]),
            ingredients=html.escape(drink["ingredients"]),
            instructions=html.escape(drink["instructions"]),
            tags=html.escape(" · ".join(drink["tags"])),
            glass=drink["glass"],
            cx=cx,
            cy=cy,
        )

    page = template
    for key, value in (
        ("entries", entries),
        ("note", html.escape(menu["note"])),
        ("file", menu["file"]),
    ):
        page = page.replace("{{" + key + "}}", value)

    left = re.findall(r"\{\{(\w+)\}\}", page)
    if left:
        raise SystemExit(f"template placeholder(s) never filled: {sorted(set(left))}")
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="_site", help="output directory (default: _site)")
    parser.add_argument("--skip-check", action="store_true", help="skip tools/check-menu.py")
    args = parser.parse_args()

    menu = json.loads((ROOT / "menu.json").read_text(encoding="utf-8"))

    errors = validate(menu)
    if errors:
        print("menu.json is not valid:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    menu_path = out / menu["file"]
    menu_path.write_text(render(menu), encoding="utf-8")

    for name in STATIC_FILES:
        shutil.copy2(ROOT / name, out / name)
    for name in STATIC_DIRS:
        shutil.copytree(ROOT / name, out / name)

    if not args.skip_check:
        check = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check-menu.py"), str(menu_path)],
            capture_output=True,
            text=True,
        )
        sys.stderr.write(check.stdout + check.stderr)
        if check.returncode != 0:
            return check.returncode

    print(f"built {len(menu['drinks'])} drinks into {out}", file=sys.stderr)
    print(menu_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
