#!/usr/bin/env python3
"""Draw the MegaMan Navi emblem as an anti-aliased transparent PNG.

usage: emblem.py OUT.png SIZE [--red #hex] [--gold #hex] [--black #hex]

Geometry measured from the flat emblem wallpaper (logo.png): gold ring outer
r=1.26R, black ring r=1.08R, red disk r=R; black L-shaped wedges in the
upper-right / lower-left quadrants joined by a thin diagonal.
"""
import os
import subprocess
import sys
import tempfile


def main():
    out, size = sys.argv[1], int(sys.argv[2])
    opts = dict(zip(sys.argv[3::2], sys.argv[4::2]))
    red = opts.get('--red', '#e01828')
    gold = opts.get('--gold', '#f0c800')
    black = opts.get('--black', '#000000')
    ss = 4  # supersample
    S = size * ss
    c = S / 2
    R = S / 2 / 1.26
    Z = [(0.40, -1.3), (0.40, -0.46), (-0.46, 0.40), (-1.3, 0.40), (-1.3, 1.3),
         (-0.40, 1.3), (-0.40, 0.46), (0.46, -0.40), (1.3, -0.40), (1.3, -1.3)]
    mvg = [
        f'viewbox 0 0 {S} {S}',
        f"fill '{gold}' circle {c},{c} {c + 1.26 * R - ss},{c}",
        f"fill '{black}' circle {c},{c} {c + 1.08 * R},{c}",
        f"fill '{red}' circle {c},{c} {c + R},{c}",
        # one Z-shaped black polygon: upper-right L-wedge, diagonal, lower-left L-wedge
        f"fill '{black}' polygon " + ' '.join(f'{c + x * R},{c + y * R}' for x, y in Z),
        # re-cut the black ring + gold ring over the wedge overflow
        f"fill none stroke '{black}' stroke-width {0.08 * R} circle {c},{c} {c + 1.04 * R},{c}",
        f"fill none stroke '{gold}' stroke-width {0.18 * R} circle {c},{c} {c + 1.17 * R},{c}",
    ]
    with tempfile.NamedTemporaryFile('w', suffix='.mvg', delete=False) as f:
        f.write('\n'.join(mvg))
        path = f.name
    # draw, then clear everything outside the gold ring
    subprocess.run([
        'magick', '-size', f'{S}x{S}', 'xc:none', '-draw', f'@{path}',
        '(', '-size', f'{S}x{S}', 'xc:black', '-fill', 'white',
        '-draw', f'circle {c},{c} {c + 1.26 * R - ss},{c}', ')',
        '-alpha', 'off', '-compose', 'CopyOpacity', '-composite',
        '-filter', 'box', '-resize', f'{size}x{size}', out], check=True)
    os.unlink(path)


if __name__ == '__main__':
    main()
