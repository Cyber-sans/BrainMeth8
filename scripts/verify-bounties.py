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
expected_counts={"common":(13,13),"uncommon":(13,16),"rare":(7,35),"special":(3,3)}
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
# Require processed outputs from Vinery/HerbalBrews, not raw ingredients.
finished={
    "lilitu_wine":("vinery:lilitu_wine",12),
    "cherry_wine":("vinery:cherry_wine",8),
    "coffee":("herbalbrews:coffee",12),
    "oolong_tea":("herbalbrews:oolong_tea",12),
    "milk_coffee":("herbalbrews:milk_coffee",8),
    "yerba_mate_tea":("herbalbrews:yerba_mate_tea",8),
}
for key,(item,quantity) in finished.items():
    data=tiers["common"][0][key]
    assert data["content"]==item and data["amount"]=={"min":quantity,"max":quantity},key
for old in ("red_savanna_grape","dark_cherry","coffee_beans","dried_oolong_tea"):
    assert old not in tiers["common"][0]
assert tiers["uncommon"][0]["rooibos_tea"]["content"]=="herbalbrews:rooibos_tea"
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
# Blind rewards: contracts expose only one of two visible labels and opaque
# server commands; the real prize is drawn on redemption, never sent in
# the preview. Preserve objective markers and special item exclusivity.
mystery_aliases={
    "common": "mystery_common", "uncommon": "mystery_uncommon",
    "rare": "mystery_legendary",
}
for group,(objectives,prizes) in tiers.items():
    for key,item in prizes.items():
        expected_label = "??? Common Reward" if group in ("common","uncommon") else "??? Legendary Reward"
        assert item["name"]==expected_label,(group,key,item["name"])
        alias=(mystery_aliases[group] if group!="special" else {
            "dragon_egg":"mystery_dragon",
            "king_crown":"mystery_plushie",
            "kill_switch":"mystery_trophy",
        }[key])
        assert item["content"] == f'brainmethbounty grant "%PLAYER_NAME%" {alias}', (group,key)
for tier,expected_size in (("common",13),("uncommon",16),("rare",35)):
    aggregate=json.loads((rl/"bounties/rewards"/(tier+"_pool.json")).read_text())
    assert aggregate["type"]=="minecraft:generic"
    pool=aggregate["pools"]
    assert len(pool)==1 and pool[0]["rolls"]==1
    entries=pool[0]["entries"]
    assert len(entries)==expected_size,(tier,len(entries))
    assert len({entry["value"] for entry in entries})==expected_size
    assert all(entry["type"]=="minecraft:loot_table" for entry in entries)
    expected_table=(
        {"brainmeth:bounties/rewards/"+tier+"/"+key for key in tiers[tier][1]}
        if tier in ("common","uncommon")
        else {"brainmeth:rewards/uncommon/"+key for key in tiers["rare"][1]})
    assert {entry["value"] for entry in entries}==expected_table, tier
bridge=(root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyDelivery.java").read_text()
for code in ("mystery_common","mystery_uncommon","mystery_legendary",
             "mystery_dragon","mystery_plushie","mystery_trophy"):
    assert code in bridge
assert "Mystery reward revealed! Check your inventory." in bridge
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
print("Brainmeth Bountiful verified: 13 Common, 13 Uncommon, 10 Rare challenges; 64 reward options, tier isolation and exclusive crown/switch.")
