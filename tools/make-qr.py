#!/usr/bin/env python3
"""Make the QR code for the current menu.

Reads the domain from CNAME and the filename from menu.json, so the code always
points at whatever menu is live. Run it again after tools/new-menu -- the URL
changes, and an old QR is a 404 at the bar.

    pip install segno
    python3 tools/make-qr.py

Output lands in _local/, which is gitignored: these are regenerable artifacts and
the repository is public, so there is no reason to commit them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Brand ink on brand paper. Contrast is ~19:1, far past anything a scanner needs.
INK = "#060405"
PAPER = "#FCFAF3"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="_local", help="output directory (default: _local)")
    parser.add_argument(
        "--ecc",
        default="h",
        choices=list("lmqh"),
        help="error correction: l=7%%, m=15%%, q=25%%, h=30%% damage tolerated (default: h)",
    )
    parser.add_argument("--scale", type=int, default=20, help="pixels per module in the PNG (default: 20)")
    parser.add_argument("--url", help="encode this instead of the current menu URL")
    args = parser.parse_args()

    try:
        import segno
    except ImportError:
        print("segno is not installed. Run:\n\n    pip install segno\n", file=sys.stderr)
        return 1

    if args.url:
        url = args.url
    else:
        domain = (ROOT / "CNAME").read_text(encoding="utf-8").strip()
        menu_file = json.loads((ROOT / "menu.json").read_text(encoding="utf-8"))["file"]
        url = f"https://{domain}/{menu_file}"

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)

    qr = segno.make(url, error=args.ecc)
    modules = 17 + 4 * qr.version

    # Vector for anything printed; PNG for a quick scan test off the screen.
    # The plain one is pure black on white, which is the safest a scanner can get.
    qr.save(out / "menu-qr.svg", scale=10, border=4, dark=INK, light=PAPER)
    qr.save(out / "menu-qr.png", scale=args.scale, border=4, dark=INK, light=PAPER)
    qr.save(out / "menu-qr-plain.png", scale=args.scale, border=4)

    def show(path):
        """Repo-relative when it is inside the repo, absolute when --out is elsewhere."""
        try:
            return path.relative_to(ROOT)
        except ValueError:
            return path

    print(f"encoded: {url}")
    print(f"version {qr.version} at ECC {args.ecc.upper()} -- {modules}x{modules} modules, quiet zone 4")
    for name in ("menu-qr.svg", "menu-qr.png", "menu-qr-plain.png"):
        print(f"  {show(out / name)}")
    print("\nPrint it 4-5cm square, keep the blank margin, and scan it from a phone before service.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
