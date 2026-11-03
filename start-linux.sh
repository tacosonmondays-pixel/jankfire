#!/bin/bash
cd "$(dirname "$0")"
command -v node >/dev/null 2>&1 || { echo "Install Node.js (LTS) from https://nodejs.org first."; exit 1; }
[ -d node_modules ] || npm install --no-audit --no-fund
JF_OPEN=1 node server.js
