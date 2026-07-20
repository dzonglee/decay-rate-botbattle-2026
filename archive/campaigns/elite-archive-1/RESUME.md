# elite-archive-1 — 7-elite mirror finals gym

Archived at match 231903, world_tag `v3campaign-2:FINALS-7elite-mirror452:engine2026.1.13`.

## To resume this campaign later
1. `cp archive/campaigns/elite-archive-1/state_final.json evolution_v3/state.json`
2. Restore the mirror room in tools/ladder_v3.py `_draw_room()`:
     `s1 = s2 = s3 = CHAMPION_ANCHOR; world = [str(CHAMPION_ANCHOR)]*7`
   (a full working copy is saved here as `ladder_v3_ELITE.py`)
3. Set `WORLD_TAG = "v3campaign-2:FINALS-7elite-mirror452:engine2026.1.13"` (matches state → no flush)
4. `rm evolution_v3/variants/g*.py` then restart the ladder.

## Population (top ranks)
rank01 fit 20.61 n 72 id 1369 la-x1080-v1m1a1h4-011
rank02 fit 20.60 n 197 id 1333 inj2-lateguard-d1
rank03 fit 18.33 n 21 id 1377 x1204x1215-fine
rank04 fit 17.40 n 875 id 1045 x1012x966-fine
rank05 fit 16.75 n 497 id 1215 x1080x1112-fine
rank06 fit 16.56 n 94 id 1363 la-apexchild-v1m1a0h3-008
rank07 fit 16.38 n 92 id 1364 la-guardcyc-v1m1a0h5-009
rank08 fit 16.36 n 274 id 1308 x1232x1215-bold
rank09 fit 16.28 n 96 id 1366 x1215x1245-bold
rank10 fit 16.18 n 205 id 1334 inj2-lateguard-d2
rank11 fit 15.38 n 423 id 1245 x1054x1197-fine
rank12 fit 14.98 n 159 id 1345 x1291x1245-fine
rank13 fit 14.97 n 335 id 1291 x1112x1045-fine
rank14 fit 14.95 n 534 id 1204 x1165x1112-bold
rank15 fit 14.89 n 153 id 1350 x1291x1215-fine
... (40 total)
