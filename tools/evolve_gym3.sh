#!/bin/bash
# ============================================================================
# feastgym-3  (YM_V3-evolution)  — LAUNCH SCRIPT
# Flip exactly ONE variable ($BASE) and run. Nothing else needs editing.
#   BASE=gen099_i19  bash tools/evolve_gym3.sh      # if the A/B names i19
#   BASE=gen51_feast bash tools/evolve_gym3.sh      # if the A/B names feast
# ============================================================================
set -euo pipefail
REPO=/Users/chrisli/Developer/competition/botbattle
VENV=/Users/chrisli/Developer/competition/evolution-2/.venv   # the only venv with agario-kit 2026.1.12
cd "$REPO"
source "$VENV/bin/activate"

# ---- THE ONE VARIABLE ------------------------------------------------------
BASE="${BASE:-}"          # <-- gen099_i19  OR  gen51_feast   (Chris names it)
# ---------------------------------------------------------------------------

if [ -z "$BASE" ]; then
  echo "STOP: \$BASE unset. Launch with:  BASE=gen099_i19 bash tools/evolve_gym3.sh   (or gen51_feast)"
  exit 2
fi
case "$BASE" in
  gen099_i19)  RIVAL=gen51_feast ;;
  gen51_feast) RIVAL=gen099_i19 ;;
  gen099_m12b) RIVAL=gen51_feast ;;   # .12 mass-correct base (feastgym3-v12)
  elite_g30)   RIVAL=gen51_feast ;;   # shipped .12 champion (feastgym3-v13; i19-lineage)
  *) echo "STOP: \$BASE must be gen099_i19, gen51_feast, gen099_m12b, or elite_g30 (got '$BASE')"; exit 2 ;;
esac

# --- gates (fail closed) ---
for b in "bots/$BASE.py" "bots/$RIVAL.py" bots/champion_gen134.py \
         bots/mimic_t1.py bots/mimic_t15.py bots/sluggish.py bots/hungry_shy.py; do
  [ -f "$b" ] || { echo "STOP: missing $b"; exit 2; }
done
V=$(pip show agario-kit 2>/dev/null | awk '/^Version/{print $2}')
[ "$V" = "2026.1.12" ] || { echo "STOP: agario-kit $V != 2026.1.12"; exit 2; }
python3 tools/speed_patch.py set 0.01     # screening speed (deterministic launch)

# clean --reset: archive any prior evolution_v2 tree + stale milestone markers
if [ -d evolution_v2 ]; then
  mv evolution_v2 "evolution_v2.bak.$(date +%Y%m%d_%H%M%S)"
  echo "[feastgym-3] archived prior evolution_v2 tree"
fi
rm -f mining/gym3_last_peak mining/gym3_last_milestone

echo "[feastgym-3] base=$BASE  rival(archetype)=$RIVAL"
echo "[feastgym-3] archetypes = champion_gen134 + $RIVAL   (rival doctrine stays in the room)"
echo "[feastgym-3] pressure seats = mimic_t1 + mimic_t15 + sluggish + hungry_shy  (2 pop seats/match)"
nohup python3 tools/evolve_v2.py \
  --base    bots/$BASE.py \
  --league --reset \
  --pop 20 --gens 999 --games 12 --parallel 12 \
  --archetypes bots/champion_gen134.py,bots/$RIVAL.py \
  --prey       bots/mimic_t1.py,bots/mimic_t15.py,bots/sluggish.py,bots/hungry_shy.py \
  > evolution_run.log 2>&1 &
PID=$!
echo "$PID" > feastgym3.pid
echo "BASE=$BASE" > feastgym3.base       # milestone cron reads this
echo "[feastgym-3] launched PID $PID -> $REPO/evolution_run.log  (base recorded in feastgym3.base)"
