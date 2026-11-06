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
board["updateFrequencySecs"]=60
# Restore normal village board generation. Decree JSON (canSpawn=false,
# canReveal=false, canWanderBuy=false) prevents random Brainmeth decrees.
# The former operator-only board policy has been removed.
# This is an integer in Bountiful's serializer. A float makes the entire
# config fail to deserialize, causing Bountiful to overwrite it with defaults.
board["villageGenFrequency"]=1
# Legacy/unsupported key: unknown fields also break Bountiful deserialization.
board.pop("globalBoardState",None)
path.write_text(json.dumps(current,indent=2,ensure_ascii=False)+"\n")
print("Configured normal Bountiful boards/decrees plus admin-only Brainmeth decree; one objective/reward, no expiry, 1m refresh.")
