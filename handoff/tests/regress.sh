#!/bin/bash
# Runs the Playwright regression scripts against fresh local servers on port 3000.
# usage: regress.sh [script names without .cjs ...]   (default: all groups)
SP=/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad
REPO=/home/user/jankfire
OUT=$SP/regress
mkdir -p "$OUT"
declare -A ENVS
ENVS[short]="JF_ROUND_KILLS=3"
ENVS[long]="JF_ROUND_KILLS=50"
ENVS[bomb]="JF_BOMB_WINS=2 JF_BOMB_ROUND=60 JF_BOMB_FUSE=12"
declare -A GROUP
GROUP[short]="t_replay"
GROUP[long]="t_items t_katana t_streak t_rand t_cos t_skins t_hotbar t_crates t_outfit t_anim t_ads t_knives t_botgrap t_flash t_bazaar_views"
GROUP[bomb]="t_bomb"
want=" $* "
pass=0; fail=0; failed=""
for g in short long bomb; do
  list=""
  for t in ${GROUP[$g]}; do
    if [ $# -eq 0 ] || [[ "$want" == *" $t "* ]]; then list="$list $t"; fi
  done
  [ -z "$list" ] && continue
  rm -rf "$OUT/data-$g"
  cd $REPO
  env ${ENVS[$g]} JF_DATA_DIR=$OUT/data-$g PORT=3000 node server.js > "$OUT/server-$g.log" 2>&1 &
  SPID=$!
  for i in $(seq 1 40); do curl -s localhost:3000/health > /dev/null && break; sleep 0.25; done
  for t in $list; do
    mkdir -p "$OUT/$t"
    timeout 300 node "$SP/$t.cjs" "$OUT/$t" > "$OUT/$t.log" 2>&1
    code=$?
    if [ $code -eq 0 ] && tail -3 "$OUT/$t.log" | grep -q "no errors"; then
      pass=$((pass+1)); echo "PASS $t"
    else
      fail=$((fail+1)); failed="$failed $t"; echo "FAIL $t (exit $code)"; tail -15 "$OUT/$t.log" | sed 's/^/    /'
    fi
  done
  kill $SPID 2>/dev/null; wait $SPID 2>/dev/null
  if grep -qiE "error|exception" "$OUT/server-$g.log"; then echo "server log ($g) mentions errors:"; grep -iE "error|exception" "$OUT/server-$g.log" | head -10 | sed 's/^/    /'; fi
done
echo "passed $pass, failed $fail${failed:+:$failed}"
