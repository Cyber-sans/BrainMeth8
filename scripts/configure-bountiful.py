#!/usr/bin/env python3
"""Install our single custom Bountiful board catalogue on the selected isolated 1.21.1 world."""
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
# Keep base mod resources available for Bountiful, but exclude the regular
# vanilla bounty pools/decrees. Our datapack files live in brainmeth/ paths.
blocked=["bounty_pools/bountiful/*","bounty_decrees/bountiful/*"]
general["dataPathsToExclude"]=sorted(set(general.get("dataPathsToExclude",[])+blocked))
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
# Deliberately do not enable global board state. Avoid interfering with
# unrelated world boards, and let every local board share the catalogue.
board["globalBoardState"]=False
path.write_text(json.dumps(current,indent=2,ensure_ascii=False)+"\n")
print("Installed Brainmeth-only Bountiful settings: one objective, one reward, no expiry, 15m refresh.")
