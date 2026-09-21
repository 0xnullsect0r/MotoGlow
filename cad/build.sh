#!/usr/bin/env bash
# Render every MotoGlow printed part to STL.
#   ./build.sh            -> stl/ alongside this script
#   ./build.sh /some/dir  -> somewhere else
#
# The board data and the fit check run first, and a failure stops the build.
# The case and the board were once designed against separate assumptions and
# each passed its own checks while being mutually impossible; printing is the
# expensive place to discover that.
set -euo pipefail
cd "$(dirname "$0")"
OUT="${1:-stl}"
mkdir -p "$OUT"

PCB_DIR=../hardware/motoglow-pcb
if python3 -c "import pcbnew" 2>/dev/null; then
  echo "Refreshing board data and checking fit"
  ( cd "$PCB_DIR" && python3 export_pcb_data.py >/dev/null && python3 verify_fit.py ) \
    | sed 's/^/  /'
else
  echo "!! pcbnew not available - using the committed pcb_data.scad unchecked"
fi
echo

render() {  # render <file> <part> <outname>
  printf '  %-30s' "$3.stl"
  openscad --export-format binstl -D "part=\"$2\"" -o "$OUT/$3.stl" "$1" 2>&1 \
    | grep -E '^\s+(Simple|Facets):' | tr -d '\n' | sed 's/  */ /g'
  printf '\n'
}

echo "Rendering parts to $OUT/"
render motoglow_case.scad tub       motoglow_case_tub
render motoglow_case.scad lid       motoglow_case_lid
render motoglow_case.scad saddle    motoglow_tube_saddle
render strip_parts.scad   clip_x8   motoglow_strip_clips_x8
render strip_parts.scad   endcap_x4 motoglow_strip_endcaps_x4
echo "done."
