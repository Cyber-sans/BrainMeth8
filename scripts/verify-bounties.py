#!/usr/bin/env python3
"""Validate the two Brainmeth bounty tiers, mystery prize pools and collector protection."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
dp=root/"rules/brainmeth-rules/data/bountiful"
rl=root/"rules/brainmeth-rules/data/brainmeth/loot_table"
p=dp/"bounty_pools/brainmeth"
decree=json.loads((dp/"bounty_decrees/brainmeth/brainmeth_board.json").read_text())
assert decree["objectives"]==["common_objs","legendary_objs"]
assert decree["rewards"]==["common_rews","legendary_rews"]
assert not any(decree[k] for k in ("canSpawn","canReveal","canWanderBuy"))
assert {f.name for f in p.glob("*.json")}=={
    "common_objs.json","common_rews.json","legendary_objs.json","legendary_rews.json"
}
read=lambda name: json.loads((p/name).read_text())
com_o,com_r=read("common_objs.json"),read("common_rews.json")
leg_o,leg_r=read("legendary_objs.json"),read("legendary_rews.json")
assert (len(com_o["content"]),len(com_r["content"]))==(26,29)
assert (len(leg_o["content"]),len(leg_r["content"]))==(10,38)
kinds={"common","legendary","dragon","plushie","trophy"}
for tier,(objs,rews) in {"common":(com_o,com_r),"legendary":(leg_o,leg_r)}.items():
    for role,pool in (("obj",objs),("rew",rews)):
        for key,item in pool["content"].items():
            assert item["type"]==("item" if role=="obj" else "command"),(tier,role,key)
            assert item["amount"]["min"]==item["amount"]["max"]>=1
            assert item["unitWorth"]>0 and item.get("repRequired",0)==0
            marker,=item["markers"]
            assert marker in kinds and set(item["forbidMarkers"])==kinds-{marker}
            assert item["rarity"]==("COMMON" if tier=="common" else "RARE")
            if role=="obj":assert ":" in item["content"]
            else:
                assert item["name"]==("??? Common Reward" if tier=="common" else "??? Legendary Reward")
                alias={"common":"mystery_common","legendary":"mystery_legendary",
                       "dragon":"mystery_dragon","plushie":"mystery_plushie",
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
assert sum(e["markers"]==["legendary"] for e in leg_o["content"].values())==7
assert sum(e["markers"]==["legendary"] for e in leg_r["content"].values())==35
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
# Bountiful normalises weights by entry count. At starter reputation 0,
# common has rarity weight 1024 and RARE has 256/2.25**2.
# This is a baseline ratio, not a guarantee: reputation changes rarity weights.
common_weight=sum(e["weightMult"] for e in com_r["content"].values())/len(com_r["content"])*com_r["weightMult"]*1024
legendary_weight=sum(e["weightMult"] for e in leg_r["content"].values())/len(leg_r["content"])*leg_r["weightMult"]*(256/2.25**2)
legendary_fraction=legendary_weight/(common_weight+legendary_weight)
assert 0.47<=legendary_fraction<=0.53,legendary_fraction
# The only two random reward aggregate pools. Three collector challenges
# remain entries inside Legendary, not additional reward pools.
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
for marker in ("dragon","plushie","trophy"):
    assert sum(v["markers"]==[marker] for v in leg_o["content"].values())==1
    assert sum(v["markers"]==[marker] for v in leg_r["content"].values())==1
assert leg_o["content"]["rare_plushie"]["content"]=="perfectplushies:sirjain_plushie_rare"
ward=leg_o["content"]["warden_trophy"]
assert ward["content"]=="trofers:large_pillar" and ward["components"]=={"trofers:trophy":"trofers:warden"}
assert leg_r["content"]["king_crown"]["markers"]==["plushie"]
assert leg_r["content"]["kill_switch"]["markers"]==["trophy"]
assert leg_r["content"]["dragon_egg"]["markers"]==["dragon"]
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
assert 'loot(server,name,"brainmeth:bounties/rewards/legendary_pool")' in java
assert "Mystery reward revealed! Check your inventory." in java
assert "DRAGON_EGG_CLAIMS" in java and "dragon_egg" in java and "kill_switch" in java
config=(root/"scripts/configure-bountiful.py").read_text()
assert 'bounty_pools/bountiful/*' in config and 'bounty_decrees/bountiful/*' in config
assert 'board["villageGenFrequency"]=1.0' in config
assert '"reverseMatchingAlgorithm":False' in config
assert not (dp/"recipe/bountyboard.json").exists()
assert not (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyBoards.java").exists()
print(f"Brainmeth Bountiful verified: two categories, 26 Common and 10 Legendary objectives; 29 Common and 35 random Legendary prizes; special collectors protected; baseline {legendary_fraction:.1%} Legendary.")
