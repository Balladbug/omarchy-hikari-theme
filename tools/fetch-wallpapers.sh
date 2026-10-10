#!/bin/bash
# Download the rest of the HIKARI wallpaper set from where it was originally
# published, and build it the same way it was built for the theme.
#
# These are Capcom artwork and fan art. They aren't redistributed in this
# repo; this script fetches them from their original hosts for personal use.
# Files go into Omarchy's per-theme user backgrounds folder, where they join
# the theme's own wallpaper in the rotation (`omarchy theme bg next`).
#
# usage: fetch-wallpapers.sh [destination] [--force]
# Needs curl and ImageMagick 7 (`magick`), both included in Omarchy.

set -uo pipefail

DEST="$HOME/.config/omarchy/backgrounds/hikari"
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h | --help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) DEST="$arg" ;;
  esac
done

NAVY="#0d1430"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
CAPCOM="https://www.capcom-games.com/megaman/exe/assets/images/common"
DA_LAN="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/88207535-9be7-42c6-8aab-8403e025b92d/dawk6fd-ddeb060a-b053-4dd9-b64f-55abd16a46ec.png/v1/fill/w_1920,h_1080/full.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTA4MCIsInBhdGgiOiIvZi84ODIwNzUzNS05YmU3LTQyYzYtOGFhYi04NDAzZTAyNWI5MmQvZGF3azZmZC1kZGViMDYwYS1iMDUzLTRkZDktYjY0Zi01NWFiZDE2YTQ2ZWMucG5nIiwid2lkdGgiOiI8PTE5MjAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.QvTgmeq0a8H6rUonplICFBONsupkZGjGSE5uYlRbiKY"
DA_MEGAMAN="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/2750c8aa-72ad-46fe-818a-a7123275307b/d5j63qc-e0635563-23be-46b1-a309-89f8843078da.png/v1/fill/w_1920,h_1080/full.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTA4MCIsInBhdGgiOiIvZi8yNzUwYzhhYS03MmFkLTQ2ZmUtODE4YS1hNzEyMzI3NTMwN2IvZDVqNjNxYy1lMDYzNTU2My0yM2JlLTQ2YjEtYTMwOS04OWY4ODQzMDc4ZGEucG5nIiwid2lkdGgiOiI8PTE5MjAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.BJi5Ve-dPG-UyVVvKB_TcLFWDf7p1GcUksNSKhwkIjQ"

# name | source URL | how it is built
WALLPAPERS=(
  "01-pet-hud-dial.png|$CAPCOM/bg_blue.png|center"
  "02-jack-in.png|https://sprites-inc.com/files/EXE/EXE5/Misc/MiscScreenMenu/JackIn_ToC_exe5.png|jackin"
  "03-navi-emblem.png|https://i.imgur.com/YuUkqeU.png|copy"
  "04-lan-and-megaman.png|https://i.imgur.com/mirwH16.png|upscale"
  "06-bass-exe.png|https://i.imgur.com/H6QTZmM.png|upscale"
  "07-lan-hikari.png|$DA_LAN|upscale"
  "08-roll-exe.png|https://i.imgur.com/LUrWuA9.png|upscale"
  "09-megaman-exe-sky.png|$DA_MEGAMAN|upscale"
  "10-protoman-exe.png|https://i.imgur.com/ojwDvx6.png|upscale"
  "13-welcome-back.png|https://wallpaperaccess.com/full/1900187.gif|pixel"
  "14-hud-dial-split.png|$CAPCOM/bg_main.png|offset"
)

build() {
  local how="$1" src="$2" out="$3"

  case "$how" in
    # Official HUD dial, centered on the theme navy
    center) magick -quiet -size 3840x2160 "xc:$NAVY" "$src" -gravity center -composite -depth 8 "$out" ;;
    # Official split dial at native size, centered right of the screen
    offset) magick -quiet -size 3840x2160 "xc:$NAVY" "$src" -geometry +1585-235 -composite -depth 8 "$out" ;;
    # One 240x135 frame of the BN5 jack-in sheet, scaled 16x nearest-neighbour
    jackin) magick -quiet "$src" -crop 240x135+7+2377 +repage -filter point -resize 1600% -alpha off -depth 8 "$out" ;;
    # 1920x1080 vector art, scaled 2x for 4K screens
    upscale) magick -quiet "$src[0]" -strip -filter Lanczos -resize 3840x2160 -depth 8 "$out" ;;
    # Pixel art on 8 px blocks: 1.5x nearest-neighbour gives even 12 px blocks
    pixel) magick -quiet "$src[0]" -alpha off -filter point -resize 3840x2400! -gravity center -crop 3840x2160+0+0 +repage -depth 8 "$out" ;;
    copy) magick -quiet "$src" -strip -depth 8 "$out" ;;
  esac
}

command -v magick >/dev/null || { echo "ImageMagick 7 (magick) is required" >&2; exit 1; }
mkdir -p "$DEST"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

failed=0
for entry in "${WALLPAPERS[@]}"; do
  IFS='|' read -r name url how <<<"$entry"
  out="$DEST/$name"

  if [[ -e $out && $FORCE == 0 ]]; then
    echo "skip   $name (exists)"
    continue
  fi

  src="$tmp/${name%.*}.src"
  if curl -fsSL -A "$UA" -o "$src" "$url" && build "$how" "$src" "$out"; then
    echo "saved  $name"
  else
    rm -f "$out"
    echo "FAILED $name ($url)" >&2
    failed=$((failed + 1))
  fi
done

echo
echo "Wallpapers are in $DEST"
echo "Cycle with: omarchy theme bg next"
exit $(( failed > 0 ))
