#!/usr/bin/env bash
# Render every MotoGlow printed part to STL.
#   ./build.sh            -> stl/ alongside this script
#   ./build.sh /some/dir  -> somewhere else
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-stl}"
mkdir -p "$OUT"

render() {  # render <file> <part> <outname>
  printf '  %-22s' "$3.stl"
  openscad --export-format binstl -D "part=\"$2\"" -o "$OUT/$3.stl" "$1" 2>&1 \
    | grep -E '^\s+(Simple|Facets):' | tr -d '\n' | sed 's/  */ /g'
  printf '\n'
}

echo "MotoGlow — rendering parts to $OUT/"
render motoglow_case.scad tub       motoglow_case_tub
render motoglow_case.scad lid       motoglow_case_lid
render motoglow_case.scad saddle    motoglow_tube_saddle
render strip_parts.scad   clip_x8   motoglow_strip_clips_x8
render strip_parts.scad   endcap_x4 motoglow_strip_endcaps_x4
echo "done."
