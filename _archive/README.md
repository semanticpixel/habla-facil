# Archived menus

`tools/new-menu` snapshots the outgoing `menu.json` here whenever you rotate to a
new menu URL, named `<date>-<old-filename>.json`. The date is the night the menu was
served — pass `--date YYYY-MM-DD` when retiring it later, since the default is
today. The drink list is the thing worth
keeping: the page is generated, so any archived menu can be rebuilt from its JSON.

To bring one back, copy the snapshot over `menu.json` and build:

```bash
cp _archive/2026-09-12-ukln1jc9h9.json menu.json
python3 tools/build-menu.py
```

It republishes at whatever `file` says, which for a snapshot is the URL that menu
originally had.

Nothing in this folder is published. The build copies an explicit allowlist of files
into the site and this folder is not on it. (The underscore prefix used to be what
kept it unpublished, back when GitHub Pages ran Jekyll over the branch; that is no
longer the mechanism, but the name is left alone as a signal that it is not part of
the site.)

Snapshots only happen on rotation, which is the boundary that matters -- a new
occasion gets a new URL. Revising drinks without rotating leaves the previous list
in git history only.
