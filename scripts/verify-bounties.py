#!/usr/bin/env python3
"""Validate Common, Legendary and Mything bounty isolation and prize redemption."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
dp=root/"rules/brainmeth-rules/data/bountiful"
rl=root/"rules/brainmeth-rules/data/brainmeth/loot_table"
p=dp/"bounty_pools/brainmeth"
decree=json.loads((dp/"bounty_decrees/brainmeth/brainmeth_board.json").read_text())
assert decree["objectives"]==["common_objs","legendary_objs","mything_objs"]
assert decree["rewards"]==["common_rews","legendary_rews","mything_rews"]
assert not any(decree[k] for k in ("canSpawn","canReveal","canWanderBuy"))
assert {f.name for f in p.glob("*.json")}=={
    "common_objs.json","common_rews.json","legendary_objs.json","legendary_rews.json",
    "mything_objs.json","mything_rews.json"
}
read=lambda name: json.loads((p/name).read_text())
com_o,com_r=read("common_objs.json"),read("common_rews.json")
leg_o,leg_r=read("legendary_objs.json"),read("legendary_rews.json")
myth_o,myth_r=read("mything_objs.json"),read("mything_rews.json")
assert (len(com_o["content"]),len(com_r["content"]))==(26,29)
assert (len(leg_o["content"]),len(leg_r["content"]))==(8,36)
assert (len(myth_o["content"]),len(myth_r["content"]))==(2,2)
kinds={"common","legendary","plushie","trophy"}
for tier,(objs,rews) in {"common":(com_o,com_r),"legendary":(leg_o,leg_r),"mything":(myth_o,myth_r)}.items():
    for role,pool in (("obj",objs),("rew",rews)):
        for key,item in pool["content"].items():
            assert item["type"]==("item" if role=="obj" else "command"),(tier,role,key)
            assert item["amount"]["min"]==item["amount"]["max"]>=1
            assert item["unitWorth"]>0 and item.get("repRequired",0)==0
            marker,=item["markers"]
            assert marker in kinds and set(item["forbidMarkers"])==kinds-{marker}
            assert item["rarity"]=={"common":"COMMON","legendary":"RARE","mything":"EPIC"}[tier]
            if role=="obj":assert ":" in item["content"]
            else:
                assert item["name"]=={"common":"??? Common Reward","legendary":"??? Legendary Reward","mything":"??? Mything Reward"}[tier]
                alias={"common":"mystery_common","legendary":"mystery_legendary",
                       "plushie":"mystery_plushie",
                       "trophy":"mystery_trophy"}[marker]
                assert item["content"]==f'brainmethbounty grant "%PLAYER_NAME%" {alias}'
    for obj in objs["content"].values():
        matches=[r for r in rews["content"].values()
                 if not (set(obj["forbidMarkers"])&set(r["markers"])
                         or set(r["forbidMarkers"])&set(obj["markers"]))]
        assert matches,(tier,obj["name"])
        assert all(r["markers"]==obj["markers"] for r in matches)
        assert any(abs(r["amount"]["min"]*r["unitWorth"]-obj["amount"]["min"]*obj["unitWorth"])
                   <=0.25*r["amount"]["min"]*r["unitWorth"] for r in matches),(tier,obj["name"])
# Uncommon is now an internal legacy-loot-directory name, NOT an active bounty tier.
assert all(x["markers"]==["common"] for x in com_o["content"].values())
assert all(x["markers"]==["common"] for x in com_r["content"].values())
assert sum(e["markers"]==["legendary"] for e in leg_o["content"].values())==8
assert sum(e["markers"]==["legendary"] for e in leg_r["content"].values())==36
# Verify the recent finished-beverage changes survived the merge.
finished={
    "lilitu_wine":("vinery:lilitu_wine",12),
    "cherry_wine":("vinery:cherry_wine",8),
    "coffee":("herbalbrews:coffee",12),
    "oolong_tea":("herbalbrews:oolong_tea",12),
    "milk_coffee":("herbalbrews:milk_coffee",8),
    "yerba_mate_tea":("herbalbrews:yerba_mate_tea",8),
    "rooibos_tea":("herbalbrews:rooibos_tea",10),
    "chorus_wine":("vinery:chorus_wine",10),
}
for key,(item,quantity) in finished.items():
    data=com_o["content"][key]
    assert data["content"]==item and data["amount"]=={"min":quantity,"max":quantity}
for old in ("red_savanna_grape","dark_cherry","coffee_beans","dried_oolong_tea"):
    assert old not in com_o["content"]
# Bountiful normalises pool entry weights by pool size and uses reward-first
# generation. At reputation 0 its native rarity weights are COMMON=1024,
# RARE=256 and EPIC=128 (no scaling penalty at zero reputation).
assert (com_r["weightMult"],leg_r["weightMult"],myth_r["weightMult"])==(1,4,0.16)
assert (com_o["weightMult"],leg_o["weightMult"],myth_o["weightMult"])==(1,4,0.16)
weights={
    "common":com_r["weightMult"]*1024*sum(e["weightMult"] for e in com_r["content"].values())/len(com_r["content"]),
    "legendary":leg_r["weightMult"]*256*sum(e["weightMult"] for e in leg_r["content"].values())/len(leg_r["content"]),
    "mything":myth_r["weightMult"]*128*sum(e["weightMult"] for e in myth_r["content"].values())/len(myth_r["content"])
}
rates={tier:weight/sum(weights.values()) for tier,weight in weights.items()}
assert 0.48<=rates["common"]<=0.51,rates
assert 0.48<=rates["legendary"]<=0.51,rates
assert 0.005<=rates["mything"]<=0.02,rates
# Two random loot tables; Mything has two fixed rewards in its own Bountiful pool.
loots=rl/"bounties/rewards"
assert {f.name for f in loots.glob("*_pool.json")}=={"common_pool.json","legendary_pool.json"}
expected_common={
    *(f"brainmeth:bounties/rewards/common/{k}" for k in (
        "cherry_wood","mangrove_timber","warped_timber","crimson_timber","pale_oak",
        "calcite","terracotta_palette","copper_construction","lanterns",
        "mushroom_architecture","landscaper","mudbricks","decorated_pots")),
    *(f"brainmeth:bounties/rewards/uncommon/{k}" for k in (
        "sponges","powered_rails","blue_ice","sea_lanterns","froglights",
        "end_rods","shroomlights","gilded_blackstone","crying_obsidian",
        "dark_prismarine","quartz","coral","shellstone","ore_display",
        "copper_masterwork","spore_blossom"))
}
expected_legendary={f"brainmeth:rewards/uncommon/{key}" for key,item
                    in leg_r["content"].items() if item["markers"]==["legendary"]}
for pool_name,expected in (("common",expected_common),("legendary",expected_legendary)):
    data=json.loads((loots/(pool_name+"_pool.json")).read_text())
    assert data["type"]=="minecraft:generic" and len(data["pools"])==1
    entries=data["pools"][0]["entries"]
    assert data["pools"][0]["rolls"]==1
    assert len(entries)==len(expected) and len({e["value"] for e in entries})==len(entries)
    assert {e["value"] for e in entries}==expected
    assert all(e["type"]=="minecraft:loot_table" for e in entries)
# No prize loss: validate nested loot table files, including legacy uncommon assets.
for pool in (("common",["common","uncommon"]),("legendary",["rare"])):
    _,dirs=pool
    for directory in dirs:
        folder=loots/directory
        assert folder.is_dir()
        assert all(json.loads(f.read_text())["type"]=="minecraft:generic" for f in folder.glob("*.json"))
assert len(expected_common)==29 and len(expected_legendary)==35
assert leg_o["content"]["dragon_egg"]["content"]=="minecraft:dragon_egg"
assert leg_o["content"]["dragon_egg"]["markers"]==["legendary"]
assert leg_r["content"]["dragon_egg"]["markers"]==["legendary"]
assert leg_r["content"]["dragon_egg"]["content"]=='brainmethbounty grant "%PLAYER_NAME%" mystery_legendary'
for marker in ("plushie","trophy"):
    assert sum(x["markers"]==[marker] for x in myth_o["content"].values())==1
    assert sum(x["markers"]==[marker] for x in myth_r["content"].values())==1
assert myth_o["content"]["rare_plushie"]["content"]=="perfectplushies:sirjain_plushie_rare"
ward=myth_o["content"]["warden_trophy"]
assert ward["content"]=="trofers:large_pillar" and ward["components"]=={"trofers:trophy":"trofers:warden"}
assert myth_r["content"]["king_crown"]["markers"]==["plushie"]
assert myth_r["content"]["kill_switch"]["markers"]==["trophy"]
assert "king_crown" not in expected_legendary and "kill_switch" not in expected_legendary
seal=leg_o["content"]["four_calamities"]
assert seal["components"]=={"minecraft:custom_data":{"brainmeth_bounty":"four_calamities_seal"}}
recipe=json.loads((rl.parent/"recipe/four_calamities_seal.json").read_text())
assert {i["item"] for i in recipe["ingredients"]}=={
    "bosses_of_mass_destruction:"+s for s in ("ancient_anima","blazing_eye","obsidian_heart","void_thorn")}
assert recipe["result"]["components"]["minecraft:custom_data"]["brainmeth_bounty"]=="four_calamities_seal"
java=(root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyDelivery.java").read_text()
for alias in ("mystery_common","mystery_uncommon","mystery_legendary",
              "mystery_dragon","mystery_plushie","mystery_trophy"):
    assert alias in java
assert 'id.equals("mystery_uncommon"))loot="brainmeth:bounties/rewards/common_pool"' in java
assert 'id.equals("mystery_legendary"))loot="brainmeth:bounties/rewards/legendary_pool"' in java
assert 'id.equals("mystery_dragon"))loot="brainmeth:bounties/rewards/legendary_pool"' in java
assert "Mystery reward revealed! Check your inventory." in java
assert "DRAGON_EGG_CLAIMS" not in java and "brainmeth-dragon-egg-claims" not in java
assert '"give "+name+" minecraft:dragon_egg' not in java
assert "dragon_egg" in java and "kill_switch" in java
config=(root/"scripts/configure-bountiful.py").read_text()
assert 'bounty_pools/bountiful/*' in config and 'bounty_decrees/bountiful/*' in config
assert 'board["villageGenFrequency"]=1.0' in config
assert '"reverseMatchingAlgorithm":False' in config
assert not (dp/"recipe/bountyboard.json").exists()
assert not (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyBoards.java").exists()
print(f"Brainmeth Bountiful verified: 26 Common, 8 Legendary, 2 Mything objectives; two random shipment pools, one fixed collector pool; starting odds {rates}.")
