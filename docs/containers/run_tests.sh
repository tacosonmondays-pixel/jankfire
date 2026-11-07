#!/bin/bash
# the gift + batch tests on a fresh file store. usage: run_tests.sh <port> <scratch dir>
PORT=${1:-3110}; D=${2:-/tmp/jfgift}; R=$(cd "$(dirname "$0")/../.." && pwd)
rm -rf "$D" && mkdir -p "$D"
start() { (cd "$R" && JF_DATA_DIR="$D" PORT=$PORT exec node --max-old-space-size=256 server.js > "$D/server.log" 2>&1) & SPID=$!; for i in $(seq 1 80); do curl -s "localhost:$PORT/health" > /dev/null && break; sleep 0.25; done; }
start; node "$R/docs/containers/t_gift_rollmany.mjs" $PORT "$D" 1 || F=1; kill $SPID; wait $SPID 2>/dev/null
# "twins": giftee's login, no gifts, no containers (as if it signed up before the gift)
python3 - "$D/jankfire-db.json" <<'PY'
import json, sys; p = sys.argv[1]; d = json.load(open(p)); u = dict(d['users']['giftee'])
u.update(name='twins', name_lower='twins', crates=0, bags=0, boxes=0, inv={}); d['users']['twins'] = u; json.dump(d, open(p, 'w'))
PY
start; node "$R/docs/containers/t_gift_rollmany.mjs" $PORT "$D" 2 || F=1; kill $SPID; wait $SPID 2>/dev/null
echo "server log: $(grep -ciE 'error|warn|flags' "$D/server.log") error/warning lines"
exit ${F:-0}
