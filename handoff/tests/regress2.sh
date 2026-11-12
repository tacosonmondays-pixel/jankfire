#!/bin/bash
# Full Playwright regression against fresh servers started from ANY checkout, on ANY port.
# usage: regress2.sh <repo dir> <port> [test names without .cjs ...]   (default: every group)
# Results: $SP/regress-<port>/<test>.log (+ screenshots in $SP/regress-<port>/<test>/), summary on stdout.
SP=/tmp/claude-0/-home-user-jankfire/c08cafbd-bcf7-5220-b480-982798f055dc/scratchpad
REPO=$(cd "${1:?usage: regress2.sh <repo dir> <port> [tests]}" && pwd); PORT=${2:?port}; shift 2
OUT=$SP/regress-$PORT; mkdir -p "$OUT/scripts"
# per-port copies of the scripts (most hard-code port 3000)
for f in "$SP"/t_*.cjs; do sed "s/localhost:3000/localhost:$PORT/g" "$f" > "$OUT/scripts/$(basename "$f")"; done
declare -A ENVS GROUP
ENVS[short]="JF_ROUND_KILLS=3";                                  GROUP[short]="t_replay"
ENVS[long]="JF_ROUND_KILLS=50";                                  GROUP[long]="t_items t_katana t_streak t_rand t_cos t_skins t_hotbar2 t_crates t_outfit t_anim t_ads t_knives t_botgrap t_flash t_bazaar_views"
ENVS[bomb]="JF_BOMB_WINS=2 JF_BOMB_ROUND=60 JF_BOMB_FUSE=12";    GROUP[bomb]="t_bomb"
ENVS[guns]="JF_ROUND_KILLS=50";                                  GROUP[guns]="t_guns t_gunsoak" # (remote_check needs a tool that was never committed; dropped)
want=" $* "; pass=0; fail=0; failed=""
for g in short long bomb guns; do
  list=""
  for t in ${GROUP[$g]}; do if [ -z "${want// /}" ] || [[ "$want" == *" $t "* ]]; then list="$list $t"; fi; done
  [ -z "$list" ] && continue
  rm -rf "$OUT/data-$g"
  (cd "$REPO" && exec env ${ENVS[$g]} JF_DATA_DIR="$OUT/data-$g" PORT=$PORT node server.js > "$OUT/server-$g.log" 2>&1) &
  SPID=$!
  for i in $(seq 1 60); do curl -s "localhost:$PORT/health" > /dev/null && break; sleep 0.25; done
  for t in $list; do
    mkdir -p "$OUT/$t"
    case $t in
      t_guns|t_gunsoak|t_hotbar2) cmd=(node "$OUT/scripts/$t.cjs" "$PORT" "$OUT/$t") ;;
      remote_check) cmd=(node "$SP/wf_blades/review/tools/remote_check.cjs" "$PORT") ;;
      *) cmd=(node "$OUT/scripts/$t.cjs" "$OUT/$t") ;;
    esac
    PORT=$PORT timeout 420 "${cmd[@]}" > "$OUT/$t.log" 2>&1; code=$?
    ok=0
    if [ "$t" = remote_check ]; then [ $code -eq 0 ] && [ "$(grep -c '"remoteError": null' "$OUT/$t.log")" -ge 10 ] && ok=1
    elif [ $code -eq 0 ] && tail -3 "$OUT/$t.log" | grep -q "no errors"; then ok=1; fi
    if [ $ok = 1 ]; then pass=$((pass+1)); echo "PASS $t | $(grep -vE '^\s*$' "$OUT/$t.log" | tail -2 | head -1 | cut -c1-200)"
    else fail=$((fail+1)); failed="$failed $t"; echo "FAIL $t (exit $code)"; tail -12 "$OUT/$t.log" | cut -c1-300 | sed 's/^/    /'; fi
  done
  kill $SPID 2>/dev/null; pkill -P $SPID 2>/dev/null; wait $SPID 2>/dev/null
  if grep -qiE "error|exception" "$OUT/server-$g.log"; then echo "server log ($g) mentions errors:"; grep -iE "error|exception" "$OUT/server-$g.log" | head -8 | cut -c1-300 | sed 's/^/    /'; fi
done
echo "passed $pass, failed $fail${failed:+:$failed}"
