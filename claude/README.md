# hikari-claude

A Claude Code theme that matches HIKARI, the Mega Man Battle Network theme for
Omarchy in this repo. It is an optional add-on: installing the desktop theme
does not change Claude Code until you run `install.sh`.

MegaMan.EXE takes Claude's place. The accent, the spinner, Clawd and the prompt
border are his armor blue, on the same Net navy as the HIKARI desktop.

## Install

On an Omarchy machine with HIKARI installed:

```bash
~/.config/omarchy/themes/hikari/claude/install.sh
```

On any other machine with Claude Code, with or without Omarchy. It needs only
`bash` and `jq`:

```bash
git clone https://github.com/Balladbug/omarchy-hikari-theme ~/omarchy-hikari-theme
~/omarchy-hikari-theme/claude/install.sh
```

The script:
- links `hikari-claude.json` into `~/.claude/themes/`.
- sets `"theme": "custom:hikari-claude"` in `~/.claude/settings.json`.

Claude Code watches the themes folder, so open sessions retint without a
restart. If one does not, restart it or pick the theme by hand with `/theme`.

The link points into the clone, so `git pull` updates the theme in place.
`omarchy theme install` deletes and re-clones the theme folder at the same
path, so the link keeps working after a reinstall too.

Omarchy writes its own generated theme to `~/.claude/themes/omarchy.json` when
you switch desktop themes. It does not touch this file or the active setting.
To go back to it, pick `omarchy` with `/theme`.

## Palette

Every color comes from HIKARI's `colors.toml`. The theme covers all 72 keys that
Claude Code 2.1 accepts, not only the ones in Omarchy's generated theme.

| Claude Code | HIKARI | Reference |
|---|---|---|
| claude, Clawd, prompt border, usage bar | accent `#18c0f8` | MegaMan.EXE armor |
| text | foreground `#c8e0f8` | PET screen text |
| your messages | lighter_background `#142050` | MegaMan bodysuit navy |
| selection | selection `#203080` | MegaMan bodysuit indigo |
| usage bar, empty | `#284068` | Navi Customizer grid lines |
| plan mode, suggestions | cyan `#58e8d8` | jack-in beam |
| bash mode, your brief label | orange `#f87020` | Lan's vest |
| accept edits, ultra effort, merged | magenta `#b078f8` | Dark Chip stamp |
| skills | bright_magenta `#f8a8e0` | Navi Customizer program |
| fast mode | bright_yellow `#f8f028` | Elec element |
| permission prompts | bright_blue `#90b0f8` | Aqua Style highlight |
| success | green `#30c858` | Wood element |
| error | red `#f86060` | battle panel red |
| warning | yellow `#f0c800` | helmet gold |
| diffs | green and red over the navy | battle panels |
| ultrathink rainbow | the element colors | battle chips |

Text colors on the background, as WCAG contrast ratios:
- **Body text:** 13.3:1.
- **Every other text color:** 5:1 or higher.
- **subtle:** HIKARI's muted slate (3.2:1). It is meant to recede.

## Rebuild

`build.py` regenerates `hikari-claude.json` from a `colors.toml` and prints the
contrast of every color. With no argument it reads the `colors.toml` at the root
of this repo, so a palette change there carries over with one command:

```bash
claude/build.py
```

## Credits

*Mega Man Battle Network* and *Rockman.EXE* are (c) Capcom. This is an unofficial
fan theme, not affiliated with or endorsed by Capcom.
