#!/usr/bin/env bash
# Review sheet from shots.cjs screenshots: one row per weapon: OLD (code model) | BLENDER | BLENDER aiming (or in use),
# cropped to the viewmodel, labelled. usage: tools/blender/compose.sh <shotDir> <out.jpg> <toohd|potato> <name>...
#   (names as shots.cjs writes them: the weapon id, or the skin's model id)
D=$1; OUT=$2; T=$3; shift 3
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
[ -f "$FONT" ] || FONT=$(fc-match -f '%{file}' 'sans:bold' 2>/dev/null)
rows=(); n=0
for g in "$@"; do
  r=$D/_row_${T}_$g.png
  lab() { echo "drawtext=fontfile=$FONT:text='$1':x=10:y=10:fontsize=22:fontcolor=$2:box=1:boxcolor=black@0.6:boxborderw=6"; }
  ffmpeg -loglevel error -y -i "$D/${T}_${g}_code_hip.png" -i "$D/${T}_${g}_glb_hip.png" -i "$D/${T}_${g}_glb_ads.png" -filter_complex \
    "[0]crop=iw*2/3:ih*2/3:iw/3:ih/3,scale=480:300,$(lab "$g  OLD" white)[a];[1]crop=iw*2/3:ih*2/3:iw/3:ih/3,scale=480:300,$(lab BLENDER 0xffe14d)[b];\
[2]crop=iw*2/3:ih*2/3:iw/3:ih/3,scale=480:300,$(lab 'BLENDER  AIM / USE' 0xffe14d)[c];[a][b][c]hstack=3" "$r" && { rows+=(-i "$r"); n=$((n+1)); }
done
[ $n -gt 1 ] && f="vstack=$n" || f="null"
ffmpeg -loglevel error -y "${rows[@]}" -filter_complex "$f" -q:v 4 "$OUT"
rm -f "$D"/_row_"${T}"_*.png
echo "$OUT ($n rows)"
