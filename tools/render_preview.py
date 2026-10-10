#!/usr/bin/env python3
"""Render a mock Omarchy desktop (bar + terminal/editor + fetch + monitor
windows) from a colors.toml, optionally over a wallpaper.

usage: render_preview.py COLORS_TOML OUT.png [WALLPAPER] [--size 1800x1012]
"""
import os
import re
import subprocess
import sys
import tempfile

FONT = '/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf'
FONT_B = '/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf'
FONT_I = '/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Italic.ttf'


def parse(path):
    c = {}
    for line in open(path):
        m = re.match(r'\s*([A-Za-z0-9_]+)\s*=\s*"([^"]*)"', line)
        if m:
            c[m.group(1)] = m.group(2)
    return c


def mix(a, b, t):
    a, b = a.lstrip('#'), b.lstrip('#')
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02x%02x%02x' % tuple(round(x * (1 - t) + y * t) for x, y in zip(ca, cb))


def gradient_spec(spec, fallback):
    """'rgba(aabbccee) rgba(...) 45deg' -> ([#aabbcc, ...], angle)"""
    if not spec:
        return [fallback], 0
    cols, angle = [], 0
    for part in spec.split():
        m = re.match(r'rgba?\(([0-9a-fA-F]{6})', part)
        if m:
            cols.append('#' + m.group(1))
        elif part.startswith('#'):
            cols.append(part[:7])
        elif part.endswith('deg'):
            angle = float(part[:-3])
    return cols or [fallback], angle


def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.cmds = [f'viewbox 0 0 {w} {h}', f"fill '{bg}' rectangle 0,0 {w},{h}"]

    def rect(self, x, y, w, h, fill, stroke=None, sw=1):
        if stroke:
            self.cmds.append(f"fill none stroke '{stroke}' stroke-width {sw} rectangle {x},{y} {x + w},{y + h}")
            self.cmds.append("stroke none")
        else:
            self.cmds.append(f"stroke none fill '{fill}' rectangle {x},{y} {x + w - 1},{y + h - 1}")

    def circle(self, cx, cy, r, fill):
        self.cmds.append(f"stroke none fill '{fill}' circle {cx},{cy} {cx + r},{cy}")

    def poly(self, pts, fill):
        self.cmds.append(f"stroke none fill '{fill}' polygon " + ' '.join(f'{x},{y}' for x, y in pts))

    def text(self, x, y, s, fill, size, font=FONT):
        self.cmds.append(f"stroke none font '{font}' font-size {size} fill '{fill}' text {x},{y} '{esc(s)}'")

    def segs(self, x, y, segs, size, cw):
        """segs: list of (color, text[, font])"""
        for seg in segs:
            col, s = seg[0], seg[1]
            font = seg[2] if len(seg) > 2 else FONT
            if s.strip():
                self.text(x, y, s, col, size, font)
            x += len(s) * cw
        return x

    def save(self, path):
        with tempfile.NamedTemporaryFile('w', suffix='.mvg', delete=False) as f:
            f.write('\n'.join(self.cmds))
            mvg = f.name
        subprocess.run(['magick', '-size', f'{self.w}x{self.h}', 'xc:none', '-draw', f'@{mvg}', path], check=True)
        os.unlink(mvg)


def frame(path, inner, w, h, b, cols, angle, out):
    """Wrap an inner window image in a (gradient) border."""
    W, H = w + 2 * b, h + 2 * b
    if len(cols) == 1:
        grad = [f'xc:{cols[0]}']
        pre = ['-size', f'{W}x{H}']
    else:
        # ImageMagick gradient angle: 0 = top->bottom; Hyprland angle 0 = left->right
        pre = ['-size', f'{W}x{H}', '-define', f'gradient:angle={90 + angle}']
        grad = [f'gradient:{cols[0]}-{cols[-1]}']
    subprocess.run(['magick', *pre, *grad, inner, '-geometry', f'+{b}+{b}', '-composite', out], check=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    size = '1800x1012'
    if '--size' in sys.argv:
        size = sys.argv[sys.argv.index('--size') + 1]
        args.remove(size)
    colors_path, out = args[0], args[1]
    wallpaper = args[2] if len(args) > 2 else None
    W, H = map(int, size.split('x'))
    c = parse(colors_path)
    g = lambda k, d=None: c.get(k) or (c.get(d) if d else None) or '#ff00ff'  # noqa: E731
    bg, fg = g('background'), g('foreground')
    tmp = tempfile.mkdtemp()

    # ---------- base ----------
    base = os.path.join(tmp, 'base.png')
    if wallpaper:
        subprocess.run(['magick', wallpaper + '[0]', '-resize', f'{W}x{H}^', '-gravity', 'center',
                        '-extent', f'{W}x{H}', base], check=True)
    else:
        subprocess.run(['magick', '-size', f'{W}x{H}', f'xc:{g("darker_background")}', base], check=True)

    s = W / 1800.0
    gap_out, gap_in, b = round(10 * s), round(5 * s), max(2, round(2 * s))
    bar_h = round(26 * s)
    cw_size = round(15 * s)
    cw = cw_size * 0.6
    lh = round(cw_size * 1.45)

    act_cols, act_angle = gradient_spec(c.get('hyprland_active_border'), g('accent'))
    inact_cols, _ = gradient_spec(c.get('hyprland_inactive_border'), '#595959')

    top = bar_h + gap_out
    avail_h = H - top - gap_out
    left_w = round((W - 2 * gap_out - 2 * gap_in) * 0.5)
    right_w = W - 2 * gap_out - 2 * gap_in - left_w
    rt_h = round((avail_h - 2 * gap_in) * 0.47)
    rb_h = avail_h - 2 * gap_in - rt_h

    # ---------- left: terminal + editor ----------
    lw, lhh = left_w - 2 * b, avail_h - 2 * b
    cv = Canvas(lw, lhh, bg)
    x0, y = round(14 * s), round(26 * s)
    prompt = [(g('blue'), '~/net/acdc ', FONT_B), (g('magenta'), ' main '), (g('green'), '❯ ')]

    def line(segs):
        nonlocal y
        cv.segs(x0, y, segs, cw_size, cw)
        y += lh

    line(prompt + [(fg, 'jack-in --navi megaman.exe')])
    line([(g('accent'), '▸ '), (fg, 'Jack in! '), (g('bright_foreground'), 'MegaMan', FONT_B), (fg, ', Execute!')])
    line([(g('green'), '✓ '), (fg, 'PET link established '), (g('dark_foreground'), '· ACDC Area 1 · 0 viruses')])
    line(prompt + [(fg, 'ls')])
    line([(g('blue'), 'acdc-area/  ', FONT_B), (g('blue'), 'scilab/  ', FONT_B), (g('blue'), 'undernet/  ', FONT_B),
          (fg, 'folder.lua  '), (g('green'), 'navi.exe  ', FONT_B), (g('red'), 'secret.zip  ', FONT_B), (fg, 'mail.txt')])
    line(prompt + [(fg, 'git status -s')])
    line([(g('red'), ' M '), (fg, 'folder.lua')])
    line([(g('green'), 'A  '), (fg, 'chips/program-advance.lua')])
    line([(g('red'), '?? '), (fg, 'undernet/secret-area.map')])
    line(prompt + [(fg, 'nvim folder.lua')])
    y += round(4 * s)

    # editor block
    ed_top = y - lh + round(6 * s)
    cv.rect(0, ed_top, lw, lhh - ed_top, g('background'))
    cv.rect(0, ed_top, lw, 1, g('muted'))
    kw, st, num, cm, fn, fld, op, pun = (g('magenta'), g('green'), g('orange', 'yellow'), g('dark_foreground'),
                                         g('blue'), g('cyan'), g('bright_cyan'), fg)
    code = [
        [(cm, '-- Battle Chip folder: 30 chips, max 4 of a kind', FONT_I)],
        [(kw, 'local '), (fg, 'folder '), (op, '= '), (pun, '{')],
        [(pun, '  { '), (fld, 'name '), (op, '= '), (st, '"Cannon"'), (pun, ',   '), (fld, 'code '), (op, '= '), (st, '"A"'), (pun, ', '), (fld, 'atk '), (op, '= '), (num, '40'), (pun, ' },')],
        [(pun, '  { '), (fld, 'name '), (op, '= '), (st, '"HeatShot"'), (pun, ', '), (fld, 'code '), (op, '= '), (st, '"B"'), (pun, ', '), (fld, 'atk '), (op, '= '), (num, '40'), (pun, ' },')],
        [(pun, '  { '), (fld, 'name '), (op, '= '), (st, '"Bubbler"'), (pun, ',  '), (fld, 'code '), (op, '= '), (st, '"C"'), (pun, ', '), (fld, 'atk '), (op, '= '), (num, '50'), (pun, ' },')],
        [(pun, '  { '), (fld, 'name '), (op, '= '), (st, '"LifeSwrd"'), (pun, ', '), (fld, 'code '), (op, '= '), (st, '"*"'), (pun, ', '), (fld, 'atk '), (op, '= '), (num, '400'), (pun, ', '), (fld, 'pa '), (op, '= '), (num, 'true'), (pun, ' },')],
        [(pun, '}')],
        [],
        [(kw, 'local function '), (fn, 'program_advance'), (pun, '(chips)')],
        [(kw, '  if '), (op, '#'), (fg, 'chips '), (op, '< '), (num, '3 '), (kw, 'then return '), (num, 'nil '), (kw, 'end')],
        [(kw, '  return '), (fg, 'chips[1].'), (fld, 'code '), (op, '== '), (st, '"*" '), (kw, 'and '), (st, '"LifeSword" '), (kw, 'or '), (st, '"Z-Canon1"')],
        [(kw, 'end')],
        [],
        [(fn, 'print'), (pun, '(('), (st, '"Jack in! %s, Execute!"'), (pun, '):'), (fn, 'format'), (pun, '('), (st, '"MegaMan"'), (pun, '))')],
    ]
    gut = 4 * cw
    sel_line = 5
    for i, segs in enumerate(code):
        ly = y + i * lh
        if i == sel_line:
            cv.rect(0, ly - lh + round(5 * s), lw, lh, g('selection'))
        cv.text(x0, ly, f'{i + 1:>3}', g('accent') if i == sel_line else g('muted'), cw_size)
        end = cv.segs(x0 + gut, ly, segs, cw_size, cw)
        if i == 10:  # block cursor
            cx = x0 + gut + 20 * cw
            cv.rect(round(cx), ly - lh + round(6 * s), round(cw), lh - round(2 * s), g('bright_foreground'))
            cv.text(round(cx), ly, 'c', g('background'), cw_size)
    # status line
    sy = lhh - round(12 * s) - lh
    cv.rect(0, sy - round(2 * s), lw, lh + round(6 * s), g('lighter_background', 'background'))
    cv.rect(0, sy - round(2 * s), round(9 * cw), lh + round(6 * s), g('accent'))
    cv.text(round(x0 * 0.6), sy + lh - round(6 * s), ' NORMAL', g('background'), cw_size, FONT_B)
    cv.segs(round(10.5 * cw), sy + lh - round(6 * s), [(g('magenta'), ' main  '), (fg, 'folder.lua  '), (g('yellow'), '● 1  '), (g('red'), ' 1')], cw_size, cw)
    cv.text(lw - round(14 * cw), sy + lh - round(6 * s), '11:22  Top', g('dark_foreground'), cw_size)
    left_img = os.path.join(tmp, 'left.png')
    cv.save(left_img)

    # ---------- right top: fetch ----------
    rw, rth = right_w - 2 * b, rt_h - 2 * b
    cv = Canvas(rw, rth, bg)
    # Navi emblem (proportions measured from the flat emblem wallpaper):
    # yellow ring r=1.26R, black ring r=1.08R, red disk r=R, black L-wedges
    # in the upper-right / lower-left joined by a thin diagonal.
    ex, ey = round(rw * 0.2), round(rth * 0.42)
    R = round(min(rw, rth) * 0.25 / 1.26)
    em_red = os.environ.get('EMBLEM_RED', '#e01828')
    em_yel = os.environ.get('EMBLEM_GOLD', g('yellow'))
    blk = '#000000'
    cv.circle(ex, ey, round(R * 1.26), em_yel)
    cv.circle(ex, ey, round(R * 1.08), blk)
    cv.circle(ex, ey, R, em_red)
    Z = [(0.40, -1.3), (0.40, -0.46), (-0.46, 0.40), (-1.3, 0.40), (-1.3, 1.3),
         (-0.40, 1.3), (-0.40, 0.46), (0.46, -0.40), (1.3, -0.40), (1.3, -1.3)]
    cv.poly([(ex + x * R, ey + y * R) for x, y in Z], blk)
    cv.cmds.append(f"fill none stroke '{blk}' stroke-width {0.08 * R:.1f} circle {ex},{ey} {ex + R * 1.04:.1f},{ey}")
    ring_w = R * 0.18
    cv.cmds.append(f"fill none stroke '{em_yel}' stroke-width {ring_w:.1f} circle {ex},{ey} {ex + R * 1.17:.1f},{ey}")
    cv.cmds.append(f"fill none stroke '{bg}' stroke-width {R:.1f} circle {ex},{ey} {ex + R * 1.26 + R / 2:.1f},{ey}")
    cv.cmds.append('stroke none')
    ix, iy = round(rw * 0.42), round(rth * 0.16)
    info = [
        [(g('accent'), 'lan', FONT_B), (fg, '@'), (g('accent'), 'pet', FONT_B)],
        [(g('dark_foreground'), '─────────────')],
        [(g('blue'), 'OS      '), (fg, 'Omarchy (Arch Linux)')],
        [(g('blue'), 'WM      '), (fg, 'Hyprland')],
        [(g('blue'), 'Theme   '), (fg, 'HIKARI')],
        [(g('blue'), 'Navi    '), (fg, 'MegaMan.EXE')],
        [(g('blue'), 'Folder  '), (fg, '30/30 chips · 3 PA')],
        [(g('blue'), 'Area    '), (fg, 'ACDC Area 1')],
    ]
    for i, segs in enumerate(info):
        cv.segs(ix, iy + i * lh, segs, cw_size, cw)
    # swatches
    sw_keys = [['background', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'foreground'],
               ['muted', 'bright_red', 'bright_green', 'bright_yellow', 'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_foreground']]
    sq = round(cw * 3)
    for r, row in enumerate(sw_keys):
        for i, k in enumerate(row):
            cv.rect(ix + i * sq, iy + len(info) * lh + r * round(sq * 0.62), sq, round(sq * 0.62), g(k))
    right_top = os.path.join(tmp, 'rt.png')
    cv.save(right_top)

    # ---------- right bottom: monitor ----------
    rbh = rb_h - 2 * b
    cv = Canvas(rw, rbh, bg)
    pad = round(10 * s)

    def box(x, y, w, h, col, title):
        cv.rect(x, y, w, h, None, stroke=col, sw=max(1, round(s)))
        cv.rect(x + round(12 * s), y - round(cw_size * 0.6), round((len(title) + 2) * cw), round(cw_size * 1.2), bg)
        cv.text(x + round(12 * s) + round(cw), y + round(cw_size * 0.35), title, g('foreground'), cw_size, FONT_B)

    def grad_bar(x, y, w, h, cols, frac):
        n = 40
        for i in range(n):
            t = i / (n - 1)
            if len(cols) == 3:
                col = mix(cols[0], cols[1], t * 2) if t < 0.5 else mix(cols[1], cols[2], (t - 0.5) * 2)
            else:
                col = mix(cols[0], cols[-1], t)
            bx = x + round(i * w / n)
            bw = round((i + 1) * w / n) - round(i * w / n) - max(1, round(s))
            cv.rect(bx, y, bw, h, col if i / n < frac else g('selection'))

    bw_full = rw - 2 * pad
    bh1 = round(rbh * 0.42)
    box(pad, pad + round(6 * s), bw_full, bh1, g('magenta'), 'cpu')
    import math
    gx0, gy0 = pad + round(16 * s), pad + round(22 * s)
    gw, gh = bw_full - round(32 * s), bh1 - round(36 * s)
    cols = [g('cyan'), g('blue'), g('magenta')]
    n = 60
    for i in range(n):
        v = 0.25 + 0.6 * abs(math.sin(i * 0.37) * math.cos(i * 0.11)) + 0.12 * math.sin(i * 1.7)
        v = max(0.06, min(1.0, v))
        hh = round(gh * v)
        bx = gx0 + round(i * gw / n)
        bwid = max(1, round(gw / n) - max(1, round(2 * s)))
        steps = max(1, hh // max(2, round(4 * s)))
        for k in range(steps):
            t = k / max(1, round(gh / max(2, round(4 * s))))
            col = mix(cols[0], cols[1], t * 2) if t < 0.5 else mix(cols[1], cols[2], min(1, (t - 0.5) * 2))
            seg_h = max(2, round(4 * s))
            cv.rect(bx, gy0 + gh - (k + 1) * seg_h, bwid, seg_h - max(1, round(s)), col)
    y2 = pad + bh1 + round(22 * s)
    half = (bw_full - pad) // 2
    bh2 = rbh - y2 - pad
    box(pad, y2, half, bh2, g('green'), 'mem')
    box(pad + half + pad, y2, bw_full - half - pad, bh2, g('red'), 'net')
    rows = [('Used', [g('green'), g('cyan'), g('blue')], 0.58), ('Avail', [g('yellow'), g('red'), g('red')], 0.42),
            ('Cache', [g('blue'), g('cyan'), g('magenta')], 0.66), ('Free', [g('magenta'), g('blue'), g('cyan')], 0.21)]
    for i, (lbl, cols, frac) in enumerate(rows):
        ry = y2 + round(26 * s) + i * round(lh * 1.25)
        cv.text(pad + round(14 * s), ry + round(cw_size * 0.75), lbl, g('light_foreground', 'foreground'), cw_size)
        grad_bar(pad + round(14 * s) + round(7 * cw), ry, half - round(28 * s) - round(7 * cw), round(cw_size * 0.9), cols, frac)
    nx = pad + half + pad + round(14 * s)
    nw = bw_full - half - pad - round(28 * s)
    for j, (cols, lbl) in enumerate([([g('yellow'), g('red'), g('red')], '▼ download'), ([g('green'), g('cyan'), g('blue')], '▲ upload')]):
        base_y = y2 + round(30 * s) + j * round(bh2 * 0.45)
        cv.text(nx, base_y + round(cw_size * 0.4), lbl, g('light_foreground', 'foreground'), cw_size)
        for i in range(36):
            v = max(0.08, min(1, 0.35 + 0.5 * abs(math.sin(i * 0.5 + j)) * abs(math.cos(i * 0.23))))
            hh = round(bh2 * 0.28 * v)
            bx = nx + round(i * nw / 36)
            cv.rect(bx, base_y + round(bh2 * 0.34) - hh, max(1, round(nw / 36) - max(1, round(2 * s))), hh,
                    mix(cols[0], cols[1], v))
    right_bot = os.path.join(tmp, 'rb.png')
    cv.save(right_bot)

    # ---------- bar ----------
    cv = Canvas(W, bar_h, bg)
    bs = round(13 * s)
    bcw = bs * 0.6
    x = round(12 * s)
    for i in range(1, 6):
        col = g('accent') if i == 1 else (fg if i in (2, 3) else g('muted'))
        cv.text(x, round(bar_h * 0.7), str(i), col, bs, FONT_B if i == 1 else FONT)
        x += round(bcw * 2.4)
    clock = 'Saturday 12:46'
    cv.text(round(W / 2 - len(clock) * bcw / 2), round(bar_h * 0.7), clock, fg, bs, FONT_B)
    cv.text(W - round(bcw * 16), round(bar_h * 0.7), '󰂯  󰖩  󰕾  󰁹', fg, bs)
    bar = os.path.join(tmp, 'bar.png')
    cv.save(bar)

    # ---------- frames & composite ----------
    fl, frt, frb = (os.path.join(tmp, n) for n in ('fl.png', 'frt.png', 'frb.png'))
    frame(None, left_img, lw, lhh, b, act_cols, act_angle, fl)
    frame(None, right_top, rw, rth, b, inact_cols, 0, frt)
    frame(None, right_bot, rw, rbh, b, inact_cols, 0, frb)
    subprocess.run([
        'magick', base,
        '(', bar, ')', '-geometry', '+0+0', '-composite',
        '(', fl, '-alpha', 'set', '-channel', 'A', '-evaluate', 'multiply', '0.985', '+channel', ')',
        '-geometry', f'+{gap_out}+{top}', '-composite',
        '(', frt, '-alpha', 'set', '-channel', 'A', '-evaluate', 'multiply', '0.96', '+channel', ')',
        '-geometry', f'+{gap_out + left_w + 2 * gap_in}+{top}', '-composite',
        '(', frb, '-alpha', 'set', '-channel', 'A', '-evaluate', 'multiply', '0.96', '+channel', ')',
        '-geometry', f'+{gap_out + left_w + 2 * gap_in}+{top + rt_h + 2 * gap_in}', '-composite',
        out], check=True)


if __name__ == '__main__':
    main()
