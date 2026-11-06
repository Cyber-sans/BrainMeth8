#!/usr/bin/env python3
"""Validate Common, Legendary and Mythic bounty isolation and prize redemption."""
import json
from pathlib import Path

root=Path(__file__).resolve().parent.parent
dp=root/"rules/brainmeth-rules/data/bountiful"
rl=root/"rules/brainmeth-rules/data/brainmeth/loot_table"
p=dp/"bounty_pools/brainmeth"
decree=json.loads((dp/"bounty_decrees/brainmeth/brainmeth_board.json").read_text())
assert decree["objectives"]==["common_objs","legendary_objs","mythic_objs"]
assert decree["rewards"]==["common_rews","legendary_rews","mythic_rews"]
assert not any(decree[k] for k in ("canSpawn","canReveal","canWanderBuy"))
assert {f.name for f in p.glob("*.json")}=={
    "common_objs.json","common_rews.json","legendary_objs.json","legendary_rews.json",
    "mythic_objs.json","mythic_rews.json"
}
read=lambda name: json.loads((p/name).read_text())
com_o,com_r=read("common_objs.json"),read("common_rews.json")
leg_o,leg_r=read("legendary_objs.json"),read("legendary_rews.json")
myth_o,myth_r=read("mythic_objs.json"),read("mythic_rews.json")
assert (len(com_o["content"]),len(com_r["content"]))==(60,60)
assert (len(leg_o["content"]),len(leg_r["content"]))==(8,40)
assert (len(myth_o["content"]),len(myth_r["content"]))==(2,2)
kinds={"common","legendary","plushie","trophy"}
for tier,(objs,rews) in {"common":(com_o,com_r),"legendary":(leg_o,leg_r),"mythic":(myth_o,myth_r)}.items():
    for role,pool in (("obj",objs),("rew",rews)):
        for key,item in pool["content"].items():
            assert item["type"]==("item" if role=="obj" else "command"),(tier,role,key)
            assert item["amount"]["min"]==item["amount"]["max"]>=1
            assert item["unitWorth"]>0 and item.get("repRequired",0)==0
            marker,=item["markers"]
            assert marker in kinds and set(item["forbidMarkers"])==kinds-{marker}
            assert item["rarity"]=={"common":"COMMON","legendary":"RARE","mythic":"EPIC"}[tier]
            if role=="obj":assert ":" in item["content"]
            else:
                if tier=="common":
                    assert key in com_o["content"],key
                    n=int(item["content"].rsplit("_",1)[-1])
                    assert 1<=n<=4
                    assert item["name"]==("??? Common Reward" if n==1 else f"??? {n} Common Rewards")
                    assert item["content"]==f'brainmethbounty grant "%PLAYER_NAME%" mystery_common_{n}'
                    assert item["weightMult"]==1
                elif tier=="legendary" and key=="seal_five_legendary":
                    assert item["name"]=="??? 5 Legendary Rewards"
                    assert item["content"]=='brainmethbounty grant "%PLAYER_NAME%" rare_seal_five_legendary'
                    assert item["weightMult"]==5
                else:
                    assert item["name"]=={"common":"??? Common Reward","legendary":"??? Legendary Reward","mythic":"??? Mythic Reward"}[tier]
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
# Bountiful's actual runtime filtering uses PoolEntry.forbids (type/content),
# not our human-readable markers/forbidMarkers. Verify all tier combinations.
all_reward_entries=[x for pool in (com_r,leg_r,myth_r) for x in pool["content"].values()]
for tier,objs in (("common",com_o),("legendary",leg_o),("mythic",myth_o)):
    for key,obj in objs["content"].items():
        actual={(v["type"],v["content"]) for v in obj.get("forbids",[])}
        expected={(reward["type"],reward["content"]) for reward in all_reward_entries
                  if reward["markers"]!=obj["markers"]}
        special=("command",'brainmethbounty grant "%PLAYER_NAME%" rare_seal_five_legendary')
        regular=("command",'brainmethbounty grant "%PLAYER_NAME%" mystery_legendary')
        old_common=("command",'brainmethbounty grant "%PLAYER_NAME%" mystery_common')
        common_commands={n:("command",f'brainmethbounty grant "%PLAYER_NAME%" mystery_common_{n}')
                         for n in range(1,5)}
        if tier=="legendary" and key=="four_calamities":
            expected.add(regular)
        else:
            expected.add(special)
        if tier=="common":
            correct_roll=int(com_r["content"][key]["content"].rsplit("_",1)[-1])
            expected.update(command for n,command in common_commands.items() if n!=correct_roll)
        else:
            expected.add(old_common) # Legacy command is excluded from non-Common pools
        assert actual==expected,(tier,key,"missing real tier exclusions",expected-actual,actual-expected)
        assert len(obj.get("forbids",[]))==len(actual),(tier,key,"duplicate exclusions")
        for reward in all_reward_entries:
            blocked=(reward["type"],reward["content"]) in actual
            expected_blocked=(reward["markers"]!=obj["markers"]
                or (tier=="legendary" and key=="four_calamities" and reward["content"]==regular[1])
                or (not (tier=="legendary" and key=="four_calamities") and reward["content"]==special[1])
                or (tier=="common" and reward["content"]!=common_commands[correct_roll][1]))
            assert blocked==expected_blocked,(tier,key,reward["content"])

# Uncommon is now an internal legacy-loot-directory name, NOT an active bounty tier.
assert all(x["markers"]==["common"] for x in com_o["content"].values())
assert all(x["markers"]==["common"] for x in com_r["content"].values())
# Rebalanced Common quantities account for brewing time, mob farming,
# crafting throughput, resource scarcity and exploration. Keep equal internal
# worth for fair reward matching without treating item counts as equal effort.
expected_amounts={
    "chrysalis": 32,
    "snail_shell": 32,
    "lizard_tail": 12,
    "snort_pottery_sherd": 1,
    "resin_clump": 64,
    "lilitu_wine": 2,
    "cherry_wine": 3,
    "coffee": 16,
    "oolong_tea": 8,
    "milk_coffee": 16,
    "yerba_mate_tea": 6,
    "soul_crystal": 2,
    "resonarium": 16,
    "temple_gloomsherd": 1,
    "echo_log": 48,
    "shellstone_bricks": 32,
    "chorus_wine": 2,
    "rooibos_tea": 6,
    "netherite_door": 1,
    "sniffer_egg": 1,
    "recovery_compass": 1,
    "ominous_trial_key": 1,
    "music_disc_pigstep": 1,
    "creaking_heart": 2,
    "sack_workshop": 12,
    "apple_cider": 4,
    "apple_wine": 4,
    "mead": 4,
    "glowing_wine": 4,
    "solaris_wine": 3,
    "kelp_cider": 4,
    "eiswein": 3,
    "aegis_wine": 2,
    "villagers_fright": 3,
    "clark_wine": 3,
    "jellie_wine": 1,
    "noir_wine": 4,
    "red_wine": 4,
    "strad_wine": 3,
    "cristel_wine": 2,
    "jo_special_mixture": 3,
    "bolvar_wine": 2,
    "magnetic_wine": 3,
    "stal_wine": 3,
    "chenet_wine": 3,
    "bottle_mojang_noir": 2,
    "creepers_crush": 3,
    "mellohi_wine": 3,
    "green_tea": 8,
    "black_tea": 8,
    "hibiscus_tea": 6,
    "lavender_tea": 6,
    "breeze_rod": 16,
    "sculk_catalyst": 8,
    "fur": 32,
    "antler": 12,
    "glow_goop": 24,
    "tooth": 16,
    "scorpion_poison_gland": 4,
    "hide": 24,
}
assert set(com_o["content"])==set(expected_amounts)
assert "rope" not in com_o["content"] and "rope" not in com_r["content"]
for key,amount in expected_amounts.items():
    entry=com_o["content"][key]
    assert entry["amount"]=={"min":amount,"max":amount},key
    assert abs(entry["unitWorth"]*amount-16000)<0.01,key
assert com_o["content"]["sack_workshop"]["content"]=="supplementaries:sack"
assert not any(x["content"] in ("supplementaries:flax","minecraft:snort_pottery_sherd")
               for k,x in com_o["content"].items() if k=="sack_workshop")
assert all(abs(x["unitWorth"]-16000)<0.01 for x in com_r["content"].values())
assert len({x["content"] for x in com_o["content"].values()})==len(com_o["content"])

# Four Common payout levels. One independent mystery roll per unit, with
# the Ancient Invitation chance applied separately to each roll.
common_payouts={
    1:("chrysalis","snail_shell","lizard_tail","resin_clump","coffee","oolong_tea","milk_coffee","yerba_mate_tea","shellstone_bricks","rooibos_tea","sack_workshop","apple_cider","apple_wine","mead","glowing_wine","kelp_cider","noir_wine","red_wine","green_tea","black_tea","hibiscus_tea","lavender_tea","fur","glow_goop","tooth","hide"),
    2:("lilitu_wine","cherry_wine","resonarium","echo_log","chorus_wine","sniffer_egg","creaking_heart","solaris_wine","eiswein","aegis_wine","villagers_fright","clark_wine","strad_wine","cristel_wine","jo_special_mixture","bolvar_wine","magnetic_wine","stal_wine","chenet_wine","bottle_mojang_noir","creepers_crush","mellohi_wine","breeze_rod","sculk_catalyst","antler","scorpion_poison_gland"),
    3:("snort_pottery_sherd","soul_crystal","temple_gloomsherd","netherite_door","recovery_compass","ominous_trial_key","jellie_wine"),
    4:("music_disc_pigstep",)
}
assert sum(map(len,common_payouts.values()))==60
for n,keys in common_payouts.items():
    for key in keys:
        entry=com_r["content"][key]
        assert entry["content"]==f'brainmethbounty grant "%PLAYER_NAME%" mystery_common_{n}'
        assert entry["amount"]=={"min":1,"max":1}
        obj=com_o["content"][key]
        excluded={x["content"] for x in obj["forbids"]}
        for other in range(1,5):
            command=f'brainmethbounty grant "%PLAYER_NAME%" mystery_common_{other}'
            assert (command in excluded)==(other!=n),(key,n,other)
assert set(com_r["content"])==set(com_o["content"])
assert all(x["weightMult"]==1 for x in com_r["content"].values())
for pool in (leg_o,myth_o):
    for obj in pool["content"].values():
        excludes={x["content"] for x in obj["forbids"]}
        for n in range(1,5):
            assert f'brainmethbounty grant "%PLAYER_NAME%" mystery_common_{n}' in excludes


assert sum(e["markers"]==["legendary"] for e in leg_o["content"].values())==8
# Heart of the Deep is easier to farm than the other Legendary trophies.
heart=leg_o["content"]["heart_of_the_deep"]
assert heart["content"]=="deeperdarker:heart_of_the_deep"
assert heart["amount"]=={"min":2,"max":2}
assert heart["unitWorth"]==22500 and heart["amount"]["min"]*heart["unitWorth"]==45000
assert sum(e["markers"]==["legendary"] for e in leg_r["content"].values())==40
special_command='brainmethbounty grant "%PLAYER_NAME%" rare_seal_five_legendary'
normal_command='brainmethbounty grant "%PLAYER_NAME%" mystery_legendary'
seal_reward=leg_r["content"]["seal_five_legendary"]
assert seal_reward["content"]==special_command
assert seal_reward["amount"]=={"min":1,"max":1}
assert seal_reward["unitWorth"]==45000
for key,obj in leg_o["content"].items():
    blocked={x["content"] for x in obj["forbids"]}
    assert (normal_command in blocked)==(key=="four_calamities")
    assert (special_command in blocked)==(key!="four_calamities")

# Verify the recent finished-beverage changes survived the merge.
finished={
    "lilitu_wine":("vinery:lilitu_wine",2),
    "cherry_wine":("vinery:cherry_wine",3),
    "coffee":("herbalbrews:coffee",16),
    "oolong_tea":("herbalbrews:oolong_tea",8),
    "milk_coffee":("herbalbrews:milk_coffee",16),
    "yerba_mate_tea":("herbalbrews:yerba_mate_tea",6),
    "chorus_wine":("vinery:chorus_wine",2),
    "rooibos_tea":("herbalbrews:rooibos_tea",6),
    "apple_cider":("vinery:apple_cider",4),
    "apple_wine":("vinery:apple_wine",4),
    "mead":("vinery:mead",4),
    "glowing_wine":("vinery:glowing_wine",4),
    "solaris_wine":("vinery:solaris_wine",3),
    "kelp_cider":("vinery:kelp_cider",4),
    "eiswein":("vinery:eiswein",3),
    "aegis_wine":("vinery:aegis_wine",2),
    "villagers_fright":("vinery:villagers_fright",3),
    "clark_wine":("vinery:clark_wine",3),
    "jellie_wine":("vinery:jellie_wine",1),
    "noir_wine":("vinery:noir_wine",4),
    "red_wine":("vinery:red_wine",4),
    "strad_wine":("vinery:strad_wine",3),
    "cristel_wine":("vinery:cristel_wine",2),
    "jo_special_mixture":("vinery:jo_special_mixture",3),
    "bolvar_wine":("vinery:bolvar_wine",2),
    "magnetic_wine":("vinery:magnetic_wine",3),
    "stal_wine":("vinery:stal_wine",3),
    "chenet_wine":("vinery:chenet_wine",3),
    "bottle_mojang_noir":("vinery:bottle_mojang_noir",2),
    "creepers_crush":("vinery:creepers_crush",3),
    "mellohi_wine":("vinery:mellohi_wine",3),
    "green_tea":("herbalbrews:green_tea",8),
    "black_tea":("herbalbrews:black_tea",8),
    "hibiscus_tea":("herbalbrews:hibiscus_tea",6),
    "lavender_tea":("herbalbrews:lavender_tea",6),
}
for key,(item,quantity) in finished.items():
    data=com_o["content"][key]
    assert data["content"]==item and data["amount"]=={"min":quantity,"max":quantity}
for old in ("red_savanna_grape","dark_cherry","coffee_beans","dried_oolong_tea"):
    assert old not in com_o["content"]
# Bountiful normalises pool entry weights by pool size and uses reward-first
# generation. At reputation 0 its native rarity weights are COMMON=1024,
# RARE=256 and EPIC=128 (no scaling penalty at zero reputation).
assert com_r["weightMult"]==1 and myth_r["weightMult"]==0.16
# 39 normal + 1 Seal-exclusive entry at weight 5. Scale the pool multiplier
# by 40/44 so the aggregate Legendary generation odds remain unchanged.
assert abs(leg_r["weightMult"]-40/11)<1e-9
assert (com_o["weightMult"],leg_o["weightMult"],myth_o["weightMult"])==(1,4,0.16)
weights={
    "common":com_r["weightMult"]*1024*sum(e["weightMult"] for e in com_r["content"].values())/len(com_r["content"]),
    "legendary":leg_r["weightMult"]*256*sum(e["weightMult"] for e in leg_r["content"].values())/len(leg_r["content"]),
    "mythic":myth_r["weightMult"]*128*sum(e["weightMult"] for e in myth_r["content"].values())/len(myth_r["content"])
}
rates={tier:weight/sum(weights.values()) for tier,weight in weights.items()}
assert 0.48<=rates["common"]<=0.51,rates
assert 0.48<=rates["legendary"]<=0.51,rates
assert 0.005<=rates["mythic"]<=0.02,rates
# Two random loot tables; Mythic has two fixed rewards in its own Bountiful pool.
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
        "dark_prismarine","coral","shellstone","ore_display",
        "copper_masterwork","spore_blossom")),
    *(f"brainmeth:bounties/rewards/common/{k}" for k in (
        "builders_toolbelt","copper_restoration","mob_head","goat_horn",
        "firework_display","enchanted_golden_apple","rabbit_banquet",
        "saturation_stew","chorus_fruit","invisible_frames",
        "sculk_stone","bloom_wood","cobwebs","cave_vegetation"))
}
expected_legendary={f"brainmeth:rewards/uncommon/{key}" for key,item
                    in leg_r["content"].items() if item["markers"]==["legendary"] and key not in ("dragon_egg","seal_five_legendary")}
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
assert len(expected_common)==42 and len(expected_legendary)==38
# Decorative bundles are actual available modded/vanilla item IDs. Every
# component is an independent pool so the player receives all promised stacks.
new_bundles={
    "sculk_stone":[("deeperdarker:sculk_stone_bricks",64),
                    ("deeperdarker:sculk_stone_tiles",64)],
    "bloom_wood":[("deeperdarker:blooming_stem",64),
                  ("deeperdarker:bloom_planks",64)],
    "cobwebs":[("minecraft:cobweb",32)],
    "cave_vegetation":[("minecraft:hanging_roots",32),
                       ("minecraft:big_dripleaf",32),
                       ("minecraft:pointed_dripstone",32)]
}
for name,expected in new_bundles.items():
    bundle=json.loads((loots/"common"/(name+".json")).read_text())
    assert bundle["type"]=="minecraft:generic"
    assert len(bundle["pools"])==len(expected)
    for pool,(item,count) in zip(bundle["pools"],expected):
        assert pool["rolls"]==1 and len(pool["entries"])==1
        entry=pool["entries"][0]
        assert entry["type"]=="minecraft:item" and entry["name"]==item
        assert entry["functions"]==[{"function":"minecraft:set_count","count":count}]
ancient=(root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethAncientInvitation.java").read_text()
assert "ORIGINAL_COMMON_REWARDS = 42;" in ancient
assert "ORIGINAL_COMMON_REWARDS + 1" in ancient

# Validate custom building tools, food, instruments and invisible frame metadata.
extra=("builders_toolbelt","copper_restoration","mob_head","goat_horn",
       "firework_display","enchanted_golden_apple","rabbit_banquet",
       "saturation_stew","chorus_fruit","invisible_frames")
assert len(extra)==10
def reward_entries(key):
    obj=json.loads((loots/"common"/(key+".json")).read_text())
    assert obj["type"]=="minecraft:generic"
    return obj,[entry for pool in obj["pools"] for entry in pool["entries"]]
def components(entry):
    d={}
    for f in entry.get("functions",[]):
        if f["function"]=="minecraft:set_components":
            d.update(f["components"])
    return d
for name in extra:
    tab,entries=reward_entries(name)
    assert all(e["type"]=="minecraft:item" for e in entries)
assert [e["name"] for e in reward_entries("builders_toolbelt")[1]]==[
    "supplementaries:wrench","supplementaries:slingshot","supplementaries:rope_arrow"]
assert [e["name"] for e in reward_entries("copper_restoration")[1]]==[
    "supplementaries:soap","minecraft:honeycomb"]
assert len(reward_entries("mob_head")[1])==6
horns=reward_entries("goat_horn")[1]
assert len(horns)==8 and len({components(x)["minecraft:instrument"] for x in horns})==8
fire=reward_entries("firework_display")[1]
assert len(fire)==3 and {components(x)["minecraft:fireworks"]["explosions"][0]["shape"] for x in fire}=={"star","creeper","burst"}
assert reward_entries("enchanted_golden_apple")[1][0]["name"]=="minecraft:enchanted_golden_apple"
assert reward_entries("rabbit_banquet")[0]["pools"][0]["rolls"]==4
assert reward_entries("saturation_stew")[0]["pools"][0]["rolls"]==3
assert components(reward_entries("saturation_stew")[1][0])["minecraft:suspicious_stew_effects"][0]["id"]=="minecraft:saturation"
assert reward_entries("chorus_fruit")[1][0]["name"]=="minecraft:chorus_fruit"
frames=reward_entries("invisible_frames")[1]
assert [e["name"] for e in frames]==["minecraft:item_frame","minecraft:glow_item_frame"]
for e in frames:
    assert components(e)["minecraft:entity_data"]=={"id":e["name"],"Invisible":1}
    assert "Invisible" in json.loads(components(e)["minecraft:item_name"])["text"]
# Valuable nonrenewable or hard-to-farm shipments are smaller than
# ordinary builder shipments; no single pool dominates the mystery draw.
balanced_shipments={
    "sponges": 16,
    "ore_display": [12, 12],
    "spore_blossom": 8,
    "blue_ice": 32,
    "gilded_blackstone": 32,
    "froglights": 32,
    "coral": 32
}
for key,count in balanced_shipments.items():
    path=rl/"bounties/rewards/uncommon"/(key+".json")
    gift=json.loads(path.read_text())
    counts=[f["count"] for pool in gift["pools"] for entry in pool["entries"]
            for f in entry.get("functions",[]) if f["function"]=="minecraft:set_count"]
    assert counts==(count if isinstance(count,list) else [count]),(key,counts)

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
expected_seal_components={
    "minecraft:custom_data":{"brainmeth_bounty":"four_calamities_seal"},
    "minecraft:item_name":{"text":"Seal of the Four Calamities","color":"dark_purple","italic":False}
}
assert seal["components"]==expected_seal_components
assert seal["name"]=="Seal of the Four Calamities"
recipe=json.loads((rl.parent/"recipe/four_calamities_seal.json").read_text())
assert {i["item"] for i in recipe["ingredients"]}=={
    "bosses_of_mass_destruction:"+s for s in ("ancient_anima","blazing_eye","obsidian_heart","void_thorn")}
assert recipe["result"]["components"]=={
    **expected_seal_components,"minecraft:enchantment_glint_override":True
}
# The dispatcher maps rare_seal_five_legendary to the matching rare/ loot table.
# Five outer rolls each call the existing Legendary pool for an independent draw.
seal_table=json.loads((loots/"rare/seal_five_legendary.json").read_text())
assert seal_table["type"]=="minecraft:generic"
assert len(seal_table["pools"])==1
assert seal_table["pools"][0]["rolls"]==5
assert seal_table["pools"][0]["entries"]==[{
    "type":"minecraft:loot_table",
    "value":"brainmeth:bounties/rewards/legendary_pool"
}]
java=(root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyDelivery.java").read_text()
for alias in ("mystery_common","mystery_uncommon","mystery_legendary",
              "mystery_dragon","mystery_plushie","mystery_trophy"):
    assert alias in java
assert 'id.equals("mystery_uncommon"))loot="brainmeth:bounties/rewards/common_pool"' in java
assert 'id.matches("mystery_common_[1-4]")' in java
assert 'case "mystery_common_4" -> 4;' in java
assert 'for (int i = 0; i < commonRolls; i++)' in java
assert 'BrainmethAncientInvitation.grantCommon(target)' in java
assert 'id.equals("mystery_legendary"))loot="brainmeth:bounties/rewards/legendary_pool"' in java
assert 'id.equals("mystery_dragon"))loot="brainmeth:bounties/rewards/legendary_pool"' in java
assert "Mystery reward revealed! Check your inventory." in java
assert "DRAGON_EGG_CLAIMS" not in java and "brainmeth-dragon-egg-claims" not in java
assert '"give "+name+" minecraft:dragon_egg' not in java
assert "dragon_egg" in java and "kill_switch" in java
deployment=(root/"scripts/deploy.sh").read_text()
assert "for obsolete in mything_objs.json mything_rews.json" in deployment
assert "rm -f \"$BOUNTY_POOL_DEST/$obsolete\"" in deployment
assert '"$OLD_REWARD_POOLS/uncommon_pool.json"' in deployment
assert '"$OLD_REWARD_POOLS/rare_pool.json"' in deployment
config=(root/"scripts/configure-bountiful.py").read_text()
assert 'bounty_pools/bountiful/*' in config and 'bounty_decrees/bountiful/*' in config
assert 'board["updateFrequencySecs"]=60' in config
assert 'board["villageGenFrequency"]=1' in config
assert 'board.pop("globalBoardState",None)' in config
assert '"reverseMatchingAlgorithm":False' in config
assert not (dp/"recipe/bountyboard.json").exists()
assert not (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethBountyBoards.java").exists()
print(f"Brainmeth Bountiful verified: 60 Common, 8 Legendary, 2 Mythic objectives; two random shipment pools, one fixed collector pool; starting odds {rates}.")
