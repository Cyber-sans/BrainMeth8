#!/usr/bin/env python3
"""Offline validation for Brainmeth admin-only reward loot tables (batches 1–7)."""
from pathlib import Path
import json

root = Path(__file__).resolve().parent.parent
base = root / "rules/brainmeth-rules/data/brainmeth/loot_table/rewards"
expected = {
    "common/sponges": ("minecraft:sponge", 64, None),
    "common/trapped_chests": ("minecraft:trapped_chest", 5, None),
    "common/deepslate_emerald_ore": ("minecraft:deepslate_emerald_ore", 32, None),
    "uncommon/poo": ("minecraft:mud", 1, "poo"),
    "uncommon/firework_grimoire": ("minecraft:book", 1, "firework_grimoire"),
    "uncommon/rain_grimoire": ("minecraft:book", 1, "rain_grimoire"),
    "uncommon/levitation_grimoire": ("minecraft:book", 1, "levitation_grimoire"),
    "uncommon/healing_grimoire": ("minecraft:book", 1, "healing_grimoire"),
    "uncommon/lightning_grimoire": ("minecraft:book", 1, "lightning_grimoire"),
    "uncommon/knockback_stick": ("minecraft:stick", 1, "knockback_stick"),
    "uncommon/potion_everything": ("minecraft:potion", 1, "potion_everything"),
    "uncommon/potion_shrink": ("minecraft:potion", 1, "potion_shrink"),
    "uncommon/potion_grow": ("minecraft:potion", 1, "potion_grow"),
    "uncommon/potion_creative": ("minecraft:potion", 1, "potion_creative"),
    "uncommon/super_tnt": ("minecraft:tnt", 1, "super_tnt"),
    "uncommon/ultimate_chorus_fruit": ("minecraft:chorus_fruit", 8, "ultimate_chorus_fruit"),
    "uncommon/splash_binding": ("minecraft:splash_potion", 2, "splash_binding"),
    "uncommon/splash_vanishing": ("minecraft:splash_potion", 2, "splash_vanishing"),
    "uncommon/splash_coronavirus": ("minecraft:splash_potion", 3, "splash_coronavirus"),
    "uncommon/fake_tnt": ("minecraft:tnt", 3, "fake_tnt"),
    "uncommon/naughty_shovel": ("minecraft:iron_shovel", 1, "naughty_shovel"),
    "uncommon/time_traveller_watch": ("minecraft:clock", 1, "time_traveller_watch"),
    "uncommon/mild_inconvenience_staff": ("minecraft:stick", 1, "mild_inconvenience_staff"),
    "uncommon/summoning_bow": ("minecraft:bow", 1, "summoning_bow"),
    "uncommon/tree_of_life": ("minecraft:oak_sapling", 1, "tree_of_life"),
    "uncommon/orbital_strike_gun": ("minecraft:crossbow", 1, "orbital_strike_gun"),
    "uncommon/crystal_ball": ("minecraft:ender_eye", 1, "crystal_ball"),
    "uncommon/kill_switch": ("minecraft:stone_button", 1, "kill_switch"),
    "uncommon/cognitohazard_book": ("minecraft:written_book", 1, "cognitohazard_book"),
    "uncommon/crown_of_nothing": ("minecraft:golden_helmet", 1, "crown_of_nothing"),
    "uncommon/fake_death_certificate": ("minecraft:paper", 1, "fake_death_certificate"),
    "uncommon/butlers_bell": ("minecraft:bell", 1, "butlers_bell"),
    "uncommon/book_of_wisdom": ("minecraft:paper", 1, "book_of_wisdom"),
    "uncommon/replicating_cake": ("minecraft:cake", 1, "replicating_cake"),
    "uncommon/manifesto": ("minecraft:written_book", 4, "manifesto"),
    "uncommon/herobrine_head": ("minecraft:player_head", 1, "herobrine_head"),
    "uncommon/disc_flashing_lights": ("minecraft:music_disc_11", 1, "disc_flashing_lights"),
    "uncommon/disc_passionfruit": ("minecraft:music_disc_wait", 1, "disc_passionfruit"),
    "rare/king_of_brainmeth_crown": ("minecraft:netherite_helmet", 1, "king_of_brainmeth_crown"),
    "uncommon/random_plushie": ("perfectplushies:*", 1, None),
    "uncommon/random_trophy_set": ("trofers:*", 1, None),
}
actual = {str(p.relative_to(base)).removesuffix(".json") for p in base.rglob("*.json")}
assert actual == set(expected), (actual, set(expected))
for name, (base_item, amount, marker) in expected.items():
    data = json.loads((base / (name + ".json")).read_text(encoding="utf-8"))
    assert data["type"] == "minecraft:generic"
    pools = data["pools"]
    assert len(pools) == 1
    if name == "uncommon/random_plushie":
        assert pools[0]["rolls"] == 1
        entries = pools[0]["entries"]
        assert len(entries) == 47
        assert all(e["type"]=="minecraft:item" and e["name"].startswith("perfectplushies:")
                   and e.get("weight",1)==1 for e in entries)
        assert len({e["name"] for e in entries})==len(entries)
        continue
    if name == "uncommon/random_trophy_set":
        assert pools[0]["rolls"] == 1
        entries = pools[0]["entries"]
        assert len(entries) == 75
        selected_trophies = set()
        for nested in entries:
            assert nested["type"] == "minecraft:loot_table" and nested["weight"] == 1
            assert nested["value"]["type"] == "minecraft:generic"
            inner_pools = nested["value"]["pools"]
            assert len(inner_pools) == 1, "Trofers prizes already include their display stand"
            assert inner_pools[0]["rolls"] == 1
            assert len(inner_pools[0]["entries"]) == 1
            trophy = inner_pools[0]["entries"][0]
            assert trophy["type"] == "minecraft:item" and trophy["name"].startswith("trofers:")
            trophy_id = trophy["functions"][0]["components"]["trofers:trophy"]
            assert trophy_id.startswith("trofers:") and trophy_id not in selected_trophies
            selected_trophies.add(trophy_id)
        assert len(selected_trophies) == len(entries)
        continue
    if name == "uncommon/manifesto":
        assert pools[0]["rolls"] == 1
        groups = pools[0]["entries"]
        assert len(groups) == 1 and groups[0]["type"] == "minecraft:group"
        volumes = groups[0]["children"]
        assert len(volumes) == 4
        all_pages = []
        for number, volume in enumerate(volumes, 1):
            assert volume["name"] == "minecraft:written_book"
            comp = volume["functions"][0]["components"]
            assert comp["minecraft:custom_data"]["volume"] == number
            book = comp["minecraft:written_book_content"]
            assert book["author"] == "Marx & Engels" and len(book["pages"]) <= 100
            all_pages.extend(book["pages"])
        assert len(all_pages) > 250
        assert "WORKING MEN OF ALL COUNTRIES" in "".join(json.loads(page)["text"] for page in all_pages)
        continue
    rolls = amount if name in {"uncommon/splash_binding", "uncommon/splash_vanishing", "uncommon/splash_coronavirus"} else 1
    assert pools[0]["rolls"] == rolls, name
    entries = pools[0]["entries"]
    assert len(entries) == 1 and entries[0]["name"] == base_item
    functions = entries[0].get("functions", [])
    counts = [fn["count"] for fn in functions if fn["function"] == "minecraft:set_count"]
    assert counts == ([] if rolls > 1 or amount == 1 else [amount]), name
    comps = [fn["components"] for fn in functions if fn["function"] == "minecraft:set_components"]
    if marker:
        assert len(comps) == 1 and comps[0]["minecraft:custom_data"]["brainmeth_reward"] == marker
        if base_item in {"minecraft:potion", "minecraft:splash_potion"}:
            assert comps[0]["minecraft:max_stack_size"] == 1
            assert comps[0]["minecraft:potion_contents"] == {"potion": "minecraft:water"}
        if name in {"uncommon/poo", "uncommon/firework_grimoire", "uncommon/rain_grimoire", "uncommon/levitation_grimoire", "uncommon/healing_grimoire", "uncommon/lightning_grimoire", "uncommon/knockback_stick"}:
            assert comps[0]["minecraft:max_stack_size"] == 1
        if marker == "knockback_stick":
            assert comps[0]["minecraft:enchantments"]["levels"] == {"minecraft:knockback": 5}
            assert comps[0]["minecraft:max_damage"] == 100 and comps[0]["minecraft:damage"] == 0
        if marker == "replicating_cake":
            assert set(comps[0]) == {"minecraft:custom_data"}, (
                "Special cake must be visually identical to ordinary Cake"
            )
    else:
        assert not comps, name

code = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethRewards.java").read_text()
for marker in ("firework_grimoire", "rain_grimoire", "levitation_grimoire", "healing_grimoire", "lightning_grimoire", "firework_wand", "rain_wand", "levitation_wand", "healing_wand", "lightning_wand"):
    assert marker in code
for seconds in ("10 * 60", "24 * 60 * 60", "3 * 60 * 60", "10 * 60"):
    assert seconds in code
assert "extinguishing_grimoire" not in code and "repulsion_grimoire" not in code
assert "PendingLightning" in code and "hoverAboveTerrain" in code and "healNearby" in code
assert "FIREWORK_CAPACITY = 6" in code and "FIREWORKS_PER_USE = 20" in code
assert "FIREWORKS_PER_WAVE = 5" in code and "PendingFireworks" in code
assert "Left-click a block for 20 fireworks" in code
assert "HOVER_HEIGHT_BLOCKS = 5.0" in code and "HOVER_HORIZONTAL_BOOST = 1.6" in code
assert "ground.getLocation().y + HOVER_HEIGHT_BLOCKS" in code
assert "LivingDamageEvent.Post" in code and "weapon.hurtAndBreak(1, attacker, EquipmentSlot.MAINHAND)" in code
assert "Next charge in" not in code and "Already floating for another" not in code
consumables = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethConsumables.java").read_text()
for marker in ("potion_everything", "potion_shrink", "potion_grow", "potion_creative", "super_tnt", "ultimate_chorus_fruit", "splash_binding", "splash_vanishing", "splash_coronavirus", "fake_tnt"):
    assert marker in consumables, marker
assert "10 * 60" in consumables and "CREATIVE_SECONDS = 2" in consumables
assert "4.0 * Math.cbrt(20)" in consumables
assert "the energy of 20 TNT." in (base/"uncommon/super_tnt.json").read_text()
assert "getGameModeForPlayer() == GameType.SURVIVAL" in consumables
assert "instabuild = true" not in consumables and "setGameMode(GameType.CREATIVE)" not in consumables
assert "MAX_FAKE_BLOCKS = 256" in consumables
gadgets = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethGadgets.java").read_text()
for timed_file in ("BrainmethRewards.java", "BrainmethOddities.java", "BrainmethGadgets.java", "BrainmethOrbitalGun.java", "BrainmethWisdom.java"):
    source = (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth"/timed_file).read_text()
    assert "displayClientMessage" not in source, timed_file
    assert "seconds to next charge" not in source and "ready in " not in source, timed_file
for silent_file in ("BrainmethConsumables.java", "BrainmethTreeOfLife.java"):
    source = (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth"/silent_file).read_text()
    assert "displayClientMessage" not in source, silent_file
assert "Returned to where you were" not in gadgets
# Preserve actual reward payloads and critical restart notice, not generic status messages.
oddities = (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethOddities.java").read_text()
wisdom = (root/"custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethWisdom.java").read_text()
assert "showTitle(online,message)" in oddities and "KILL SWITCH! Restarting" in oddities
assert "A Whisper from Beyond" in oddities and '"<Wanda> "' in wisdom
tree = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethTreeOfLife.java").read_text()
for marker in ("naughty_shovel", "time_traveller_watch", "mild_inconvenience_staff", "summoning_bow"):
    assert marker in gadgets, marker
assert "CROUCH_UNTIL" in gadgets and "20);" in gadgets
assert "HISTORY_LOOKBACK_MS = 15000L" in gadgets and "WATCH_COOLDOWN = 6 * 3600L" in gadgets
assert "SHOVEL_REGEN = 6 * 3600L" in gadgets and "STAFF_REGEN = 20 * 60L" in gadgets
assert "onArrowHit" in gadgets and "onAnvil" in gadgets
assert "tree_of_life" in tree
assert "HEIGHT = 96" in tree and "CROWN_RADIUS = 39" in tree and "CROWN_HEIGHT = 24" in tree
assert "BUILD_BUDGET_PER_TICK = 650" in tree and "item.shrink(64)" in tree
assert "CropGrowEvent.Pre.Result.DO_NOT_GROW" in tree
assert "save(server)" in tree and "job.progress" in tree and "!level.hasChunkAt(at)" in tree
assert "MAX_PLAN_BLOCKS = 190_000" in tree
orbital = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethOrbitalGun.java").read_text()
assert "orbital_strike_gun" in orbital
assert "RANGE = 128" in orbital and "RECHARGE_SECONDS = 10 * 60" in orbital
assert "MAX_ACTIVE_STRIKES = 8" in orbital and "level.destroyBlock(strike.target, false, shooter)" in orbital
assert "state.hasBlockEntity()" in orbital and "state.getDestroySpeed(level, pos) < 0" in orbital
assert "getGameTime() < strike.impactTick" in orbital and "if (strike.shooter.equals(shooter.getUUID()))" in orbital
assert "level.explode(" not in orbital and "level.addFreshEntity(" not in orbital
assert not any("rare_music_disc" in filename for filename in actual)
oddities = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethOddities.java").read_text()
wisdom = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethWisdom.java").read_text()
cake = (root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth/BrainmethReplicatingCake.java").read_text()
for key in ("crystal_ball", "kill_switch", "cognitohazard_book", "crown_of_nothing", "fake_death_certificate", "butlers_bell", "manifesto"):
    assert key in oddities, key
assert "BRAINMETH_ALLOW_KILLSWITCH" in oddities and '"stop"' in oddities
assert "ClientboundSetTitleTextPacket" in oddities and "brainmeth-crystal-messages.json" in oddities
assert "colouredWhisper" in oddities and "WHISPER_PALETTE" in oddities
assert "showTitle(player,m.body())" in oddities
assert "Message from "+chr(34)+"+sender" not in oddities
assert 'sender+": "+body' not in oddities
assert "King of Absolutely Nothing" in oddities and "Mr. Deeds" in oddities
assert "A fresh start will put you on your way." in wisdom and "Nothing is exactly as it seems." in wisdom
assert "Wanda" in wisdom and "now+3600L" in wisdom
assert "SLICE_REGEN_SECONDS = 10 * 60L" in cake
assert "newBites >= 6" in cake and "nextSlice > 0L || bites >= 6" in cake
assert "remainingBites == 0 ? 0L" in cake and "getFoodData().eat(2,0.1F)" in cake
assert "brainmeth-replicating-cakes.json" in cake and 'root.addProperty("version",2)' in cake
assert "brainmeth-replicating-cakes.v1-backup.json" in cake
assert "REPLICATION_INTERVAL" not in cake and "Direction.NORTH" not in cake
assert "No special hint on placement" in cake
assert 'BRAINMETH_ALLOW_KILLSWITCH: "true"' in (root / "compose.yaml").read_text()
assert not (base / "uncommon/rare_music_disc.json").exists()
for slug, original in (("flashing_lights",{"sound_id":"brainmeth:flashing_lights"}), ("passionfruit","minecraft:music_disc.wait")):
    song_path = root / f"rules/brainmeth-rules/data/brainmeth/jukebox_song/{slug}.json"
    song = json.loads(song_path.read_text())
    assert song["sound_event"] == original, "Incorrect jukebox sound event"
    assert ("PLACEHOLDER AUDIO" in song["description"]["text"]) == (slug == "passionfruit")
    assert song["length_in_seconds"] > 0 and 0 <= song["comparator_output"] <= 15
    item = json.loads((base/f"uncommon/disc_{slug}.json").read_text())
    playable = item["pools"][0]["entries"][0]["functions"][0]["components"]["minecraft:jukebox_playable"]
    assert playable["song"] == f"brainmeth:{slug}"
head_item = json.loads((base/"uncommon/herobrine_head.json").read_text())
assert head_item["pools"][0]["entries"][0]["functions"][0]["components"]["minecraft:profile"]["name"]=="MHF_Herobrine"
assert not any("rare_music_disc" in filename for filename in actual)
print("Reward batches 1-7 verified: 40 top-level tables with 47 plushie choices and 75 single combined trophies.")
