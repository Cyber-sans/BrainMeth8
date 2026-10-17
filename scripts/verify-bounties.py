#!/usr/bin/env python3
"""Validate admin-issued Brainmeth decrees and reward tier isolation."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
dp=root/"rules/brainmeth-rules/data/bountiful"
rl=root/"rules/brainmeth-rules/data/brainmeth/loot_table"
decree=json.loads((dp/"bounty_decrees/brainmeth/brainmeth_board.json").read_text())
assert decree["objectives"]==["common_objs","uncommon_objs","rare_objs","special_objs"]
assert decree["rewards"]==["common_rews","uncommon_rews","rare_rews","special_rews"]
assert not decree["canSpawn"] and not decree["canReveal"] and not decree["canWanderBuy"]
kinds=("common","uncommon","rare","dragon","plushie","trophy")
expected_counts={"common":(11,13),"uncommon":(13,16),"rare":(7,35),"special":(3,3)}
tiers={}
for group in ("common","uncommon","rare","special"):
    p=dp/"bounty_pools/brainmeth"
    objs=json.loads((p/(group+"_objs.json")).read_text())["content"]
    rews=json.loads((p/(group+"_rews.json")).read_text())["content"]
    if group!="rare":
        assert len(objs)==expected_counts[group][0],(group,len(objs))
    else:
        assert len(objs)==expected_counts[group][0]
    tiers[group]=(objs,rews)
    for role,items in (("obj",objs),("rew",rews)):
        for key,value in items.items():
            assert value["amount"]["min"]==value["amount"]["max"]
            assert value["amount"]["min"]>=1 and value["unitWorth"]>0
            assert value.get("repRequired",0)==0
            assert len(value["markers"])==1
            marker=value["markers"][0]
            assert marker in kinds
            assert set(value["forbidMarkers"])==set(kinds)-{marker}
            assert value["type"]==("item" if role=="obj" else "command")
            if role=="rew":
                assert value["content"].startswith('brainmethbounty grant "%PLAYER_NAME%" ')
            if role=="obj":
                assert ":" in value["content"]
# Every initial reward has at least one matching objective, and vice versa.
objectives={marker:[] for marker in kinds}
rewards={marker:[] for marker in kinds}
for o,r in tiers.values():
    for entry in o.values():objectives[entry["markers"][0]].append(entry)
    for entry in r.values():rewards[entry["markers"][0]].append(entry)
for marker in kinds:
    assert objectives[marker] and rewards[marker],marker
    for obj in objectives[marker]:
        assert all(
            (rew["markers"][0]==marker)==(
                not bool(set(obj["forbidMarkers"])&set(rew["markers"]))
                and not bool(set(rew["forbidMarkers"])&set(obj["markers"])))
            for pool in tiers.values() for rew in pool[1].values())
assert len(tiers["rare"][1])==35,len(tiers["rare"][1])
assert "kill_switch" not in tiers["rare"][1] and "king_of_brainmeth_crown" not in tiers["rare"][1]
assert tiers["special"][0]["rare_plushie"]["content"]=="perfectplushies:sirjain_plushie_rare"
ward=tiers["special"][0]["warden_trophy"]
assert ward["content"]=="trofers:large_pillar" and ward["components"]=={"trofers:trophy":"trofers:warden"}
assert tiers["special"][1]["king_crown"]["markers"]==["plushie"]
assert tiers["special"][1]["kill_switch"]["markers"]==["trophy"]
assert tiers["special"][1]["dragon_egg"]["markers"]==["dragon"]
seal=tiers["rare"][0]["four_calamities"]
assert seal["components"]=={"minecraft:custom_data":{"brainmeth_bounty":"four_calamities_seal"}}
recipe=json.loads((rl.parent/"recipe/four_calamities_seal.json").read_text())
assert {i["item"] for i in recipe["ingredients"]}=={
    "bosses_of_mass_destruction:"+s for s in ("ancient_anima","blazing_eye","obsidian_heart","void_thorn")}
assert recipe["result"]["components"]["minecraft:custom_data"]["brainmeth_bounty"]=="four_calamities_seal"
# Reward command definitions must actually have matching loot tables and supply their declared items.
for tier in ("common","uncommon"):
    for key in tiers[tier][1]:
        payload=json.loads((rl/"bounties/rewards"/tier/(key+".json")).read_text())
        assert len(payload["pools"])>=1 and all(p["rolls"]==1 for p in payload["pools"])
        assert all(entry["type"]=="minecraft:item" and entry["name"].count(":")==1
                   for p in payload["pools"] for entry in p["entries"])
rare_pool=json.loads((rl/"bounties/rewards/rare_pool.json").read_text())["pools"][0]["entries"]
assert len(rare_pool)==35 and len({e["value"] for e in rare_pool})==35
assert "disc_passionfruit" not in tiers["rare"][1]
assert all("disc_passionfruit" not in e["value"] for e in rare_pool)
assert not (rl/"bounties/rewards/rare/disc_passionfruit.json").exists()
for key in tiers["rare"][1]:
    target=rl/"bounties/rewards/rare"/(key+".json")
    data=json.loads(target.read_text())
    assert data["pools"][0]["entries"][0]["value"]=="brainmeth:rewards/uncommon/"+key
assert "king_of_brainmeth_crown" not in (e["value"] for e in rare_pool)
assert "kill_switch" not in (e["value"] for e in rare_pool)
crown=json.loads((rl/"rewards/rare/king_of_brainmeth_crown.json").read_text())
assert crown["pools"][0]["entries"][0]["functions"][0]["components"]["minecraft:custom_data"]["brainmeth_reward"]=="king_of_brainmeth_crown"
java=(root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyDelivery.java").read_text()
assert "DRAGON_EGG_CLAIMS" in java and "dragon_egg" in java and "kill_switch" in java
config_script=(root/"scripts/configure-bountiful.py").read_text()
assert 'bounty_pools/bountiful/*' in config_script and 'bounty_decrees/bountiful/*' in config_script
# Normal Bountiful boards, crafting, village spawning and default decrees remain available.
assert 'board["villageGenFrequency"]=1.0' in config_script
assert 'if p not in previous_brainmeth_exclusions' in config_script
assert not (dp/"recipe/bountyboard.json").exists()
assert not (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyBoards.java").exists()
print("Brainmeth Bountiful verified: 11 Common, 13 Uncommon, 10 Rare challenges; 64 reward options, tier isolation and exclusive crown/switch.")
