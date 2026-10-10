#!/usr/bin/env python3
"""Check an Omarchy colors.toml: WCAG contrast of every key against the
background(s), plus the closest pairs among the ANSI colors (CIEDE2000-ish
via CIE76 on Lab, good enough to flag near-duplicates)."""
import math
import re
import sys


def parse(path):
    colors = {}
    for line in open(path):
        m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*"(#[0-9A-Fa-f]{6})"', line)
        if m:
            colors[m.group(1)] = m.group(2).lower()
    return colors


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lab(h):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(h))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de(a, b):
    return math.dist(lab(a), lab(b))


def main():
    c = parse(sys.argv[1])
    bg = c['background']
    print(f"background {bg}")
    order = ['foreground', 'light_foreground', 'bright_foreground', 'dark_foreground', 'muted',
             'accent', 'red', 'bright_red', 'orange', 'yellow', 'bright_yellow', 'green',
             'bright_green', 'cyan', 'bright_cyan', 'blue', 'bright_blue', 'magenta',
             'bright_magenta', 'brown']
    print(f"{'key':18} {'hex':8} {'vs bg':>6} {'vs dark':>7} {'vs sel':>6}")
    for k in order:
        if k in c:
            sel = c.get('selection', bg)
            dk = c.get('darker_background', bg)
            flag = '' if contrast(c[k], bg) >= 4.5 else ('  <4.5' if contrast(c[k], bg) >= 3 else '  <3 !!')
            print(f"{k:18} {c[k]:8} {contrast(c[k], bg):6.2f} {contrast(c[k], dk):7.2f} {contrast(c[k], sel):6.2f}{flag}")
    for k in ('selection', 'lighter_background', 'dark_background', 'darker_background'):
        if k in c:
            print(f"{k:18} {c[k]:8} fg-on-it {contrast(c['foreground'], c[k]):5.2f}")
    ansi = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'orange',
            'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan']
    ansi = [k for k in ansi if k in c]
    pairs = sorted((de(c[a], c[b]), a, b) for i, a in enumerate(ansi) for b in ansi[i + 1:]
                   if not (b == 'bright_' + a or a == 'bright_' + b))
    print("closest non-bright-pair ANSI pairs (Lab dE76):")
    for d, a, b in pairs[:6]:
        print(f"  {d:5.1f}  {a} {c[a]}  ~  {b} {c[b]}")


if __name__ == '__main__':
    main()
