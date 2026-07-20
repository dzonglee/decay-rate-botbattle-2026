#!/bin/bash
# GAMELOG JANITOR (Chris's strategy 2026-07-10): enforce the 35GB cap (delete
# oldest first) + run the batch forensic every 250 logged matches.
# Run as a loop-daemon: while :; do bash tools/gamelog_janitor.sh; sleep 600; done
set -uo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
DIR="$REPO/evolution_v2/gamelogs"
CAP_GB=35
BATCH=250
cd "$REPO"; [ -d "$DIR" ] || exit 0

# 1) storage cap: delete oldest .json.gz until under CAP
CAP_KB=$((CAP_GB * 1024 * 1024))
while :; do
  USED_KB=$(du -sk "$DIR" | awk '{print $1}')
  [ "$USED_KB" -le "$CAP_KB" ] && break
  OLDEST=$(ls -t "$DIR"/*.json.gz 2>/dev/null | tail -20)
  [ -z "$OLDEST" ] && break
  echo "$OLDEST" | xargs rm -f
  echo "$(date -u +%FT%TZ) [janitor] over ${CAP_GB}GB (${USED_KB}KB) -> pruned 20 oldest" >> mining/gamelog_janitor.log
done

# 2) batch forensic every 250 logs (lifetime counter survives pruning)
TOTAL_MARK=mining/gamelog_total_seen
LAST_BATCH=mining/gamelog_last_batch
CUR=$(ls "$DIR" | grep -c ".json.gz$" || echo 0)
PREV_TOTAL=$(cat "$TOTAL_MARK" 2>/dev/null || echo 0)
PREV_FILES=$(cat "${TOTAL_MARK}.files" 2>/dev/null || echo 0)
# lifetime total grows by (new files appeared since last tick, net of pruning is ignored:
# count via newest filename ordering isn't reliable -> use mtime-newer counting)
NEW=$(find "$DIR" -name "*.json.gz" -newer "$TOTAL_MARK" 2>/dev/null | wc -l | tr -d " ")
[ -f "$TOTAL_MARK" ] || NEW=$CUR
TOTAL=$((PREV_TOTAL + NEW))
echo "$TOTAL" > "$TOTAL_MARK"
LB=$(cat "$LAST_BATCH" 2>/dev/null || echo 0)
DUE=$((TOTAL / BATCH))
if [ "$DUE" -gt "$LB" ]; then
  N=$BATCH; [ "$CUR" -lt "$BATCH" ] && N=$CUR
  python3 tools/gamelog_analyze.py "$DIR" "$DUE" "$N" > "mining/gamelog_batch_${DUE}.md" 2>&1 \
    && echo "$DUE" > "$LAST_BATCH" \
    && echo "$(date -u +%FT%TZ) [janitor] batch $DUE forensic -> mining/gamelog_batch_${DUE}.md (total logged: $TOTAL)" >> mining/gamelog_janitor.log
fi
