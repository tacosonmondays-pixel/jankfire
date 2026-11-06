#!/usr/bin/env bash
# Build every Blender model (glb into public/models/, sheet into tools/blender/sheets/), 3 at a time.
# usage: tools/blender/make_all.sh [flags for the scripts, e.g. --no-sheet]
cd "$(dirname "$0")/../.." || exit 1
command -v blender >/dev/null || { echo "blender not found: apt-get install -y blender python3-numpy libegl1 libgl1-mesa-dri libegl-mesa0"; exit 1; }
log=$(ls tools/blender/make_*.py | xargs -P 3 -I{} sh -c 'blender -b --python {} -- '"$*"' 2>&1 | grep -E "JF_|Traceback|Error:"')
echo "$log"
! echo "$log" | grep -q Traceback
