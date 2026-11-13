#!/bin/bash
# run: runws.sh <checkout> <port> test...
D=$1; P=$2; shift 2
cd $D
for f in "$@"; do
  PORT=$P JF_TRAFFIC=off node server.js > /tmp/srv_$P.log 2>&1 &
  S=$!
  for i in $(seq 1 60); do curl -s localhost:$P >/dev/null && break; sleep 0.25; done
  R=$(timeout 150 node tests/$f.cjs $P 2>&1 | grep -E "FAIL|ALL OK|FAILED|passed" | tr '\n' ' ')
  echo "$f: $R"
  kill $S; wait $S 2>/dev/null
done
