#!/usr/bin/env python3
"""Configure Bountiful with vanilla boards and admin-issued Brainmeth decrees."""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument("--data-root",type=Path,required=True)
args=parser.parse_args()
path=args.data_root/"config/bountiful/bountiful.json"
path.parent.mkdir(parents=True,exist_ok=True)
if path.exists():
    try:current=json.loads(path.read_text())
    except json.JSONDecodeError as exc:raise RuntimeError(
        "Bountiful config is not standard JSON; refusing to replace existing config") from exc
else:current={}
general=current.setdefault("general",{})
# Restore Bountiful's ordinary pools/decrees, including on worlds that
# previously ran the Brainmeth-only configuration. Preserve other exclusions.
previous_brainmeth_exclusions={"bounty_pools/bountiful/*","bounty_decrees/bountiful/*"}
general["dataPathsToExclude"]=[
    p for p in general.get("dataPathsToExclude",[])
    if p not in previous_brainmeth_exclusions
]
bounty=current.setdefault("bounty",{})
bounty.update({
    "initialCountPreference":{"min":1,"max":1},
    "fillerCountPreference":{"min":1,"max":1},
    "reverseMatchingAlgorithm":False,
    "shouldHaveTimersAndExpire":False,
    "allowDecreeMixing":False
})
board=current.setdefault("board",{})
board["updateFrequencySecs"]=900
# Restore normal village board generation. Decree JSON (canSpawn=false,
# canReveal=false, canWanderBuy=false) prevents random Brainmeth decrees.
# The former operator-only board policy has been removed.
board["villageGenFrequency"]=1.0
# Deliberately do not enable global board state. Avoid interfering with
# unrelated world boards, and let every local board share the catalogue.
board["globalBoardState"]=False
path.write_text(json.dumps(current,indent=2,ensure_ascii=False)+"\n")
print("Configured normal Bountiful boards/decrees plus admin-only Brainmeth decree; one objective/reward, no expiry, 15m refresh.")
