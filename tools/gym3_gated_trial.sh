#!/bin/bash
# QUEUED: the first feastgym-3 mirrored trial — gen099_gated vs champion (gen099_i19).
# gen099_gated does NOT exist yet and has no definition on disk. Drop the bot at
# bots/gen099_gated.py (or tell Claude which gate to apply to gen099_i19) and run:
#     bash tools/gym3_gated_trial.sh
# It runs the LAW-1 mirrored / LAW-2 ban-void battery via gym3_battery.sh and
# writes mining/gym3_ggated_report.txt (per-half + pooled MASS delta + gene readout).
set -eo pipefail
cd /Users/chrisli/Developer/competition/botbattle
if [ ! -f bots/gen099_gated.py ]; then
  echo "PENDING: bots/gen099_gated.py does not exist. Provide it (or its gate spec) first."
  exit 2
fi
nohup bash tools/gym3_battery.sh gen099_i19 gated bots/gen099_gated.py 20 \
  > mining/gym3_ggated_trial.driver.log 2>&1 &
echo "[gated-trial] launched mirrored gen099_gated vs gen099_i19, PID $! -> mining/gym3_ggated_report.txt"
