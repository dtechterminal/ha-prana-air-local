#!/bin/sh
# Rebuild custom_components/prana_air_local/brand/ from docs/brand/.
# Needs ImageMagick 7 (`magick`) and python3.
#   aqi-logo.svg    -> logo / dark_logo (wordmark; ® glyph dropped, it needs a font)
#   aqi-favicon.png -> icon (the multicolour "Q")
set -eu
cd "$(dirname "$0")/.."
out=custom_components/prana_air_local/brand
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# ImageMagick's SVG renderer ignores <style>, so inline the class fills.
python3 - docs/brand/aqi-logo.svg "$tmp" <<'PY'
import re, sys
src, tmp = sys.argv[1], sys.argv[2]
s = open(src).read()
css = s.split("<style>")[1].split("</style>")[0]
fills = {}
for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
    if m := re.search(r"fill:\s*([^;]+);", body):
        for c in re.findall(r"\.(cls-\d+)", sel):
            fills[c] = m.group(1).strip()
s = re.sub(r'<g id="Page-1">.*?</g>\s*', "", s, flags=re.S)
s = re.sub(r"<defs>.*?</defs>", "", s, flags=re.S)
s = re.sub(r'<path class="cls-1"[^>]*/>\s*', "", s)
s = re.sub(r'class="(cls-\d+)"', lambda m: f'fill="{fills[m.group(1)]}"', s)
open(f"{tmp}/light.svg", "w").write(s)
open(f"{tmp}/dark.svg", "w").write(s.replace('fill="#1f9ec9"', 'fill="#ffffff"'))
PY
for variant in light dark; do
  prefix=; [ "$variant" = dark ] && prefix=dark_
  magick -background none -density 1600 "$tmp/$variant.svg" -trim +repage "$tmp/$variant.png"
  magick "$tmp/$variant.png" -resize x128 -strip "PNG32:$out/${prefix}logo.png"
  magick "$tmp/$variant.png" -resize x256 -strip "PNG32:$out/${prefix}logo@2x.png"
done
magick docs/brand/aqi-favicon.png -trim +repage "$tmp/q.png"
for size in 256 512; do
  inner=$((size * 88 / 100))
  name=icon.png; [ "$size" = 512 ] && name=icon@2x.png
  magick "$tmp/q.png" -resize "${inner}x${inner}" -background none -gravity center \
    -extent "${size}x${size}" -strip "PNG32:$out/$name"
done
