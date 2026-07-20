#!/bin/bash
# THE ONLY WRITER of config/current_development_champion.txt. Promotion requires an
# n>=100 champion-challenge confirmation whose POOLED delta >= +2.5. Logs hash+timestamp.
# Args: $1=new_champion_path  $2=confirmation_report_path
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle; cd "$REPO"
NEW="$1"; REP="$2"; CUR=$(cat config/current_development_champion.txt)
DP=$(awk '/--- POOLED ---/{f=1} f&&/PAIRED MASS DELTA/{print; exit}' "$REP" 2>/dev/null | grep -oE '[+-][0-9.]+' | head -1 || echo 0)
if awk "BEGIN{exit !($DP>=2.5)}"; then
  ts=$(date -u +%FT%TZ)
  echo "$ts  PROMOTE  $CUR -> $NEW  pooled_delta=$DP  new_sha=$(shasum -a 256 "$NEW"|cut -c1-16)  report=$REP" >> config/promotion_log.txt
  echo "$NEW" > config/current_development_champion.txt
  echo "PROMOTED -> $NEW (pooled delta $DP, logged to config/promotion_log.txt)"
else
  echo "REFUSED: pooled delta ${DP} < +2.5 — pointer unchanged (guarded)"
fi
