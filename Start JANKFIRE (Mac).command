#!/bin/bash
cd "$(dirname "$0")"
if ! command -v node >/dev/null 2>&1; then
  echo ""
  echo "  JANKFIRE needs Node.js to run the server."
  echo "  Opening the download page. Install the LTS version, then double-click this file again."
  open "https://nodejs.org/en/download"
  read -n 1 -s -r -p "  press any key to close"
  exit 1
fi
[ -d node_modules ] || { echo "First run: installing, this takes a minute..."; npm install --no-audit --no-fund; }
JF_OPEN=1 node server.js
