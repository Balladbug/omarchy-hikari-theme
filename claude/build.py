#!/usr/bin/env python3
"""Build hikari-claude.json, a Claude Code theme, from HIKARI's colors.toml.

Usage: build.py [path/to/colors.toml]

With no path it reads HIKARI's colors.toml at the root of this repo, so the
desktop and Claude Code themes come from the same palette. It writes
hikari-claude.json next to this script and prints the WCAG contrast of every
text color on the terminal background.
"""

import json
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_COLORS = HERE.parent / "colors.toml"
OUT = HERE / "hikari-claude.json"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def hexs(c):
    return "#" + "".join(f"{round(v):02x}" for v in c)


def mix(a, b, t):
    """Blend t of color b into color a."""
    a, b = rgb(a), rgb(b)
    return hexs(x + (y - x) * t for x, y in zip(a, b))


def luminance(h):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def build(p):
    bg = p["background"]
    fg = p["foreground"]
    white = p["bright_foreground"]
    grid = p["hyprland_inactive_border"].removeprefix("rgba(")[:6]

    def shimmer(c):
        return mix(c, white, 0.35)

    return {
        # MegaMan.EXE takes Claude's place: armor blue, and Clawd wears it too.
        "claude": p["accent"],
        "claudeShimmer": shimmer(p["accent"]),
        "clawd_body": p["accent"],
        "clawd_background": p["darker_background"],
        "claudeBlue_FOR_SYSTEM_SPINNER": p["blue"],
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": p["bright_blue"],
        # PET screen text on the Net navy.
        "text": fg,
        "inverseText": bg,
        "inactive": mix(fg, bg, 0.35),
        "inactiveShimmer": mix(fg, bg, 0.15),
        "subtle": p["muted"],
        # The prompt box is the active window: armor-blue border.
        "promptBorder": p["accent"],
        "promptBorderShimmer": shimmer(p["accent"]),
        # Modes. Plan is the jack-in beam, bash is Lan at the PET,
        # accept-edits is a Dark Chip.
        "planMode": p["cyan"],
        "bashBorder": p["orange"],
        "autoAccept": p["magenta"],
        "autoAcceptShimmer": shimmer(p["magenta"]),
        "fastMode": p["bright_yellow"],
        "fastModeShimmer": shimmer(p["bright_yellow"]),
        "effortUltra": p["magenta"],
        # Skills are Navi Customizer programs.
        "skill": p["bright_magenta"],
        "permission": p["bright_blue"],
        "permissionShimmer": shimmer(p["bright_blue"]),
        "suggestion": p["cyan"],
        "remember": p["bright_blue"],
        "background": p["cyan"],
        "ide": p["blue"],
        "professionalBlue": p["blue"],
        "chromeYellow": p["yellow"],
        # Status: Wood, battle-panel red, helmet gold.
        "success": p["green"],
        "error": p["red"],
        "warning": p["yellow"],
        "warningShimmer": shimmer(p["yellow"]),
        "merged": p["magenta"],
        # Diffs are tinted panels on the Net navy.
        "diffAdded": mix(bg, p["green"], 0.22),
        "diffRemoved": mix(bg, p["red"], 0.22),
        "diffAddedDimmed": mix(bg, p["green"], 0.10),
        "diffRemovedDimmed": mix(bg, p["red"], 0.10),
        "diffAddedWord": mix(bg, p["green"], 0.40),
        "diffRemovedWord": mix(bg, p["red"], 0.40),
        # Surfaces: MegaMan's bodysuit navy and indigo.
        "userMessageBackground": p["lighter_background"],
        "userMessageBackgroundHover": mix(p["lighter_background"], p["selection"], 0.5),
        "bashMessageBackgroundColor": mix(bg, p["orange"], 0.10),
        "memoryBackgroundColor": mix(bg, p["cyan"], 0.10),
        "composerSidebarBackground": p["dark_background"],
        "selectionBg": p["selection"],
        # Usage bar on the Navi Customizer grid.
        "rate_limit_fill": p["accent"],
        "rate_limit_empty": f"#{grid}",
        # Brief labels: Lan's orange vest and MegaMan's blue.
        "briefLabelYou": p["orange"],
        "briefLabelClaude": p["accent"],
        # Subagent colors.
        "red_FOR_SUBAGENTS_ONLY": p["red"],
        "blue_FOR_SUBAGENTS_ONLY": p["blue"],
        "green_FOR_SUBAGENTS_ONLY": p["green"],
        "yellow_FOR_SUBAGENTS_ONLY": p["yellow"],
        "purple_FOR_SUBAGENTS_ONLY": p["magenta"],
        "orange_FOR_SUBAGENTS_ONLY": p["orange"],
        "pink_FOR_SUBAGENTS_ONLY": p["bright_magenta"],
        "cyan_FOR_SUBAGENTS_ONLY": p["cyan"],
        # Ultrathink rainbow, from the battle chip elements.
        "rainbow_red": p["red"],
        "rainbow_orange": p["orange"],
        "rainbow_yellow": p["yellow"],
        "rainbow_green": p["green"],
        "rainbow_blue": p["accent"],
        "rainbow_indigo": p["blue"],
        "rainbow_violet": p["magenta"],
        "rainbow_red_shimmer": p["bright_red"],
        "rainbow_orange_shimmer": shimmer(p["orange"]),
        "rainbow_yellow_shimmer": p["bright_yellow"],
        "rainbow_green_shimmer": p["bright_green"],
        "rainbow_blue_shimmer": shimmer(p["accent"]),
        "rainbow_indigo_shimmer": p["bright_blue"],
        "rainbow_violet_shimmer": p["bright_magenta"],
    }


# Keys drawn as surfaces behind text, not as text.
SURFACES = {
    "inverseText", "clawd_background", "selectionBg", "composerSidebarBackground",
    "userMessageBackground", "userMessageBackgroundHover", "bashMessageBackgroundColor",
    "memoryBackgroundColor", "rate_limit_empty", "diffAdded", "diffRemoved",
    "diffAddedDimmed", "diffRemovedDimmed", "diffAddedWord", "diffRemovedWord",
}


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_COLORS
    palette = tomllib.loads(src.read_text())
    overrides = build(palette)
    theme = {"name": "hikari-claude", "base": "dark", "overrides": overrides}
    OUT.write_text(json.dumps(theme, indent=2) + "\n")
    print(f"wrote {OUT.name} ({len(overrides)} colors) from {src}")

    bg, fg = palette["background"], palette["foreground"]
    print(f"\ncontrast on background {bg}:")
    for key, value in overrides.items():
        if key not in SURFACES:
            print(f"  {contrast(value, bg):5.2f}  {value}  {key}")
    print(f"\ntext {fg} on surfaces:")
    for key in sorted(SURFACES - {"inverseText", "clawd_background", "rate_limit_empty"}):
        print(f"  {contrast(fg, overrides[key]):5.2f}  {overrides[key]}  {key}")


if __name__ == "__main__":
    main()
