#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import sys


class MenuParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.current = None
        self.in_h2 = False
        self.in_ingredients = False
        self.in_num = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()

        if tag == "article" and "entry" in classes:
            self.current = {
                "line": self.getpos()[0],
                "style": attrs.get("style", ""),
                "h2": [],
                "ingredients": [],
                "glass": None,
                "dot": None,
                "num": None,
            }
            return

        if self.current is None:
            return

        if tag == "h2":
            self.in_h2 = True
        elif tag == "span" and "num" in classes:
            self.current["num"] = ""
            self.in_num = True
        elif tag == "p" and "ing" in classes:
            self.in_ingredients = True
        elif tag == "use":
            self.current["glass"] = attrs.get("href") or attrs.get("xlink:href")
        elif tag == "circle" and "dot" in classes:
            self.current["dot"] = {
                "cx": attrs.get("cx"),
                "cy": attrs.get("cy"),
                "fill": attrs.get("fill"),
            }

    def handle_endtag(self, tag):
        if tag == "span":
            self.in_num = False
        elif tag == "h2":
            self.in_h2 = False
        elif tag == "p":
            self.in_ingredients = False
        elif tag == "article" and self.current is not None:
            self.entries.append(self.current)
            self.current = None

    def handle_data(self, data):
        if self.current is None:
            return

        if self.in_num:
            self.current["num"] += data
        elif self.in_h2:
            self.current["h2"].append(data)
        elif self.in_ingredients:
            self.current["ingredients"].append(data)


def compact(parts):
    return " ".join("".join(parts).split())


def color_from_style(style):
    match = re.search(r"--glass-liquid:\s*(#[0-9a-fA-F]{6})", style)
    return match.group(1) if match else None


def main():
    menu_path = Path(sys.argv[1] if len(sys.argv) > 1 else "ukln1jc9h9.html")
    if not menu_path.exists():
        print(f"Menu file not found: {menu_path}", file=sys.stderr)
        return 1

    parser = MenuParser()
    parser.feed(menu_path.read_text(encoding="utf-8"))

    errors = []
    names = set()

    for entry in parser.entries:
        label = compact(entry["h2"]) or f"entry at line {entry['line']}"
        liquid = color_from_style(entry["style"])
        dot = entry["dot"]

        if entry["num"] is None:
            errors.append(f"Line {entry['line']}: {label} is missing its <span class=\"num\"> counter slot.")
        elif entry["num"].strip():
            errors.append(
                f"Line {entry['line']}: {label} has a hardcoded drink number; "
                "numbering comes from the CSS counter."
            )

        drink_name = label
        if drink_name in names:
            errors.append(f"Line {entry['line']}: duplicate drink name: {drink_name}")
        names.add(drink_name)

        if not compact(entry["ingredients"]):
            errors.append(f"Line {entry['line']}: {label} is missing ingredients.")

        if not liquid:
            errors.append(f"Line {entry['line']}: {label} is missing --glass-liquid.")

        if not entry["glass"] or not entry["glass"].startswith("#glass-"):
            errors.append(f"Line {entry['line']}: {label} is missing a glass symbol reference.")

        if dot is None:
            errors.append(f"Line {entry['line']}: {label} is missing a flavour plot dot.")
            continue

        if liquid and dot["fill"] and dot["fill"].lower() != liquid.lower():
            errors.append(f"Line {entry['line']}: {label} dot fill does not match --glass-liquid.")

        for axis in ("cx", "cy"):
            try:
                value = float(dot[axis])
            except (TypeError, ValueError):
                errors.append(f"Line {entry['line']}: {label} dot {axis} is not numeric.")
                continue

            if not 10 <= value <= 86:
                errors.append(f"Line {entry['line']}: {label} dot {axis} is outside the plot bounds.")

    if not parser.entries:
        errors.append("No menu entries found.")

    if errors:
        print("Menu check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {len(parser.entries)} menu entries validated in {menu_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
