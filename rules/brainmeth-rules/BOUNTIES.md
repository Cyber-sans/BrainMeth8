# Brainmeth Community Bounties — NeoForge 1.21.1

Bountiful boards remain completely normal: players can craft, place, break,
move and use them, and boards generate naturally in villages. Vanilla Bountiful
decrees and contracts remain available. The **Brainmeth Community Bounties**
decree is special: it never generates, reveals from blank decrees, or appears
in wandering-trader offers. Only an operator can issue it.

## Contract pickup quota

Each player may **take a maximum of three bounty papers from boards
containing the Brainmeth Community Bounties decree per Minecraft day**,
across all such boards. Ordinary Bountiful boards without that decree
remain unrestricted. The quota counts **taking**, not completing:
dropping or abandoning a contract does not refund the slot. Both normal
clicking and shift-clicking are intercepted on the server before pickup;
the fourth attempted pickup is rejected with a message. Failed transfers
(e.g. an inventory with no space) should not consume quota. A fresh
Minecraft day (world day-time crossing a multiple of 24000 ticks, including
sleeping) resets the quota. Counts persist to
`world/brainmeth-bounty-take-limits.json` across server restarts.

This change adds a server-side Mixin to `brainmeth-core` targeting
Bountiful's board inventory and must be tested in-game on the installed
Bountiful version. Test: 3 normal pickups, fourth refused, shift-click
refused, another Brainmeth board refused, ordinary board allowed, fresh
day resets, reconnect/restart does not reset, inventory-full failed
pickups do not count, and no bounties are lost when refusing a pickup.

## Admin setup

After deploying the updated datapack and config, use this operator-only
Minecraft command to obtain a Brainmeth decree:

```mcfunction
/give @s bountiful:decree[bountiful:decree_data={ids:["brainmeth_board"],rank:1}] 1
```

Place the decree into any ordinary Bountiful board's decree slot. That board
can now generate Brainmeth contracts. No board-specific tagging or permissions
are required. Boards without the special decree generate ordinary Bountiful
contracts. If the board also has a vanilla decree, both types of contracts
can appear, **without mixing their objectives/rewards** because
`allowDecreeMixing=false`. Remove the ordinary decree if you want only
Brainmeth contracts on that board.

The custom decree JSON is at
`data/bountiful/bounty_decrees/brainmeth/brainmeth_board.json` with
`canSpawn=false`, `canReveal=false`, `canWanderBuy=false`.
Its objective and reward pools are at `data/bountiful/bounty_pools/brainmeth/`.

The `scripts/configure-bountiful.py --data-root <world data root>` script
restores vanilla pool/decree loading if an older Brainmeth-only configuration
had excluded them, restores village board generation, and preserves our
one-objective/one-reward, no-expiry and 15-minute-refresh settings. These
settings are Bountiful-wide, not decree-specific. Restart Bountiful/server
after config changes; already generated bounty papers are not retroactively
changed. The admin `/give` syntax is based on Bountiful's decree component
definition and still needs an in-game check.

## Objectives — exactly three categories

**Common (26):** The former 13 Common and 13 Uncommon objectives have been
one pool since the earlier merger. They are now **rebalanced** to require
substantial interaction with crafting, farming, wildlife, advanced brewing,
different dimensions, archaeology, difficult structures or boss-adjacent
progression. The old 6000/13000 objective-and-reward worth split is gone:
all Common entries now have Bountiful worth **16000**, regardless of source.
This affects reward matching, not a promise of identical real-world playtime.

### Current Common deliveries

| Mod/content | Delivery amounts |
|---|---|
| Naturalist | 12 Chrysalises; 12 Snail Shells; 16 Lizard Tails; 192 Shellstone Bricks |
| Supplementaries | 32 Sacks (crafted using 224 Flax + 32 String); 192 Rope; 2 Netherite Doors |
| Vinery | 24 Miss Lilitus Wines; 24 Cherry Wines; 16 Chorus Wines |
| HerbalBrews | 48 Coffees; 24 Oolong Teas; 24 Milk Coffees; 32 Yerba Mate Teas; 40 Rooibos Teas |
| Deeper & Darker | 8 Soul Crystals; 48 Resonarium; 1 Temple Gloomsherd; 256 Echo Logs |
| Vanilla/Backport | 1 Snort Pottery Sherd; 192 Resin Clumps; 1 Sniffer Egg; 1 Recovery Compass; 3 Ominous Trial Keys; 1 Pigstep Disc; 8 Creaking Hearts |

The former easy **64 raw Flax** task is gone, replaced by crafted Sacks.
Brewing tasks use finished drinks, not ingredient turn-ins.
Unfarmable or scarce archaeology/exploration collectibles are deliberately
**one** each rather than demanding multiple copies. Mass-producible materials
require larger batches. Two Netherite Doors require Netherite Scrap and
Gold Doors; their recipe on the Supplementaries 1.21.1 branch is one
scrap + one gold door each. Exact difficulty will depend on existing
farms, structure loot, and world progression, so these are a *first
difficulty pass*, requiring in-game adjustment if one route dominates.

### Common shipment balancing

The original 29 Common shipments (one now removed from the random pool) are retained with internal worth 16000.
The random prize table now offers 38 equally likely outcomes, including
10 new non-block reward types.
Seven exceptionally valuable crates are reduced: Sponges **64→16**,
Deepslate Emerald Ore **32→4**, Spore Blossoms **16→8**,
Blue Ice **64→32**, Gilded Blackstone **64→32**,
Pearlescent Froglights **64→32**, and Tube Coral Blocks **64→32**.
Ordinary construction-resource shipments retain their earlier amounts.


**Legendary (8):** Ancient Anima, Blazing Eye, Obsidian Heart, Void Thorn,
Heart of the Deep, the Four Calamities Seal, 3 Nether Stars, and **one
Dragon Egg**. The Dragon Egg is an ordinary, repeatable Legendary delivery:
it is consumed on redemption like other objectives, awards one random
Legendary prize, and is not returned. There is no once-per-player limit.
The legacy claim tracking file is ignored; existing `mystery_dragon`
bounties now behave like any ordinary Legendary bounty.

**Mythic (2):** A rare SirJain Plushie grants the **King of Brainmeth
Crown**; a Warden Trophy mounted on its large pillar grants the **Kill
Switch**. Each is guaranteed and unavailable from ordinary Legendary
reward rolls. They are the sole non-operator sources. The intended label
is **Mythic**; Bountiful's built-in `EPIC` rarity (purple) is used to
make these rarer than regular `RARE` (yellow) Legendary contracts.

## Rewards — exactly three Bountiful reward pools

The decree references `common_objs`, `legendary_objs`, `mythic_objs`
and `common_rews`, `legendary_rews`, `mythic_rews`.
Only three labels appear: **??? Common Reward**,
**??? Legendary Reward** and **??? Mythic Reward**.

- Common: 26 objectives, 38 equally likely mystery outcomes: 28 building
  shipments and 10 specialist tools, collectibles and rare-food prizes.
- Legendary: 8 objectives and 35 random custom prizes.
- Mythic: 2 special objectives, each with one exclusive guaranteed prize.

Random prize selection occurs server-side on redemption. The Mythic
Bountiful pool uses the two protected fixed grant commands, not an extra
random aggregate loot table. Legacy Uncommon deliveries still map to
Common. Legacy Dragon Egg grants map to regular Legendary.

**Starter reputation appearance:** about **49.5% Common, 49.5% Legendary,
1% Mythic**. Based on Bountiful's actual initial reward-first selection,
pool multipliers are respectively 1, 4 and 0.16, with built-in
COMMON/RARE/EPIC rarities. Those probabilities **vary with reputation**:
at higher reputation, Common becomes less likely under Bountiful's
rarity-weighting scheme. This is a starting-board calibration, not a
guaranteed per-board quota. Verify on an actual board before deployment.

The 15-minute board refresh and the 3-bounties-taken-per-Minecraft-day
quota are unchanged.

## Rewards

**Common — 38 equally possible outcomes:** cherry logs + saplings (64+4),
mangrove logs + roots (64+16), 64 warped stems, 64 crimson stems,
pale oak logs + saplings (64+4), 64 calcite,
32 cyan and 32 light-blue terracotta, 64 copper grates,
32 lanterns and 32 chains, 64 mushroom stems,
64 moss blocks and 64 moss carpets, 64 mud bricks and
64 packed mud, 32 decorated pots, 64 sponges, 64 powered rails,
64 blue ice, 64 sea lanterns, 64 pearlescent froglights,
64 end rods, 64 shroomlights, 64 gilded blackstone,
64 crying obsidian, 64 dark prismarine, 128 quartz blocks,
64 tube coral blocks, 64 Naturalist shellstone bricks,
4 deepslate emerald ore and 4 deepslate coal ore, 64 waxed oxidised copper,
and 8 spore blossoms.

**Ten newly added non-block outcomes** (each 1-in-38 among Common prizes):

- **Builder's Toolbelt:** 1 Supplementaries Wrench, 1 Slingshot and
  12 Rope Arrows (rope charges included by the mod's item defaults).
- **Copper Restoration Kit:** 32 Supplementaries Soap and 64 Honeycomb.
- **Mob Head:** 1 random Creeper, Zombie, Skeleton, Piglin,
  Wither Skeleton or Dragon head (uniform selection).
- **Firework Display Kit:** 48 coloured explosive firework rockets:
  16 each of star, Creeper and burst designs, with trails/twinkles.
  These are for displays and may hurt users boosted with Elytra.
- **Goat Horn:** 1 horn, selected uniformly from all eight vanilla
  melodies, including four screaming-goat variants.
- **Enchanted Golden Apple:** 1 rare uncraftable food.
- **Rabbit Banquet:** 4 Rabbit Stews, generated as separate items.
- **Saturation Stew:** 3 Suspicious Stews with the Saturation effect.
- **Chorus Harvest:** 32 edible Chorus Fruits.
- **Invisible Frame Collection:** 16 invisible standard Item Frames
  and 8 invisible Glow Item Frames, each visibly named in inventory.
  Custom `minecraft:entity_data` should make each frame invisible
  when placed; test placement and drops on the live NeoForge 1.21.1 build.

Each new outcome has **one** entry in the 38-way random aggregate table,
regardless of the number of items or variants inside its contents.
No extra mods are required. The original 29 Bountiful `common_rews`
command entries remain unchanged to preserve Common/Legendary/Mythic
board appearance odds; those commands all resolve the same aggregate
Common prize table at redemption.


**Legendary — 35 equally possible ordinary prizes:** existing grimoires,
potions, gadgets, collectibles and custom music disc rewards, excluding the
exclusive King of Brainmeth Crown and Kill Switch. The two Mythic challenges grant their unique prizes outside the random lottery.

The 16 formerly Uncommon shipment definitions remain under the legacy
`bounties/rewards/uncommon/` loot table directory solely as item assets;
there is NO active `uncommon_pool.json` or Uncommon Bountiful pool.
The 35 previous Rare prize definitions similarly remain in their existing
private paths. The only two random aggregate tables are
`bounties/rewards/common_pool.json` and
`bounties/rewards/legendary_pool.json`.

## Gameplay verification required

1. Confirm vanilla boards can be crafted, placed, broken and used by non-OP
   players, and village boards still appear in newly generated villages.
2. Confirm new boards produce normal vanilla decrees and never Brainmeth
   decrees; blank crafted decrees must never reveal Brainmeth.
3. As an OP, run the `/give` command above, inspect the named Brainmeth
   decree, insert it into a normal board and wait for fresh custom contracts.
4. Confirm a board with both a vanilla and Brainmeth decree never mixes
   their objective/reward pools.
5. Complete Common, Legendary (including Dragon Egg) and Mythic hand-ins; check
   quantities, reward isolation, collector exclusivity and egg consumption.
6. **Do not activate the Kill Switch outside an isolated test container.**

IMPORTANT: Bountiful 8.0.0-beta.2 has publicly reported
NeoForge villager/board NPE and server hangs when bounties are redeemed
near villagers. Test redemptions on the isolated test world before
moving board anywhere near villager pathfinding. Keep this change on the 1.21.1 branch isolated until live validation.
