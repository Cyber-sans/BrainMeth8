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

**Common (26):** Former Common + Uncommon deliveries, unchanged quantities.
The old Uncommon rarity is no longer an active Brainmeth category.

**Legendary (8):** Ancient Anima, Blazing Eye, Obsidian Heart, Void Thorn,
Heart of the Deep, the Four Calamities Seal, 3 Nether Stars, and **one
Dragon Egg**. The Dragon Egg is an ordinary, repeatable Legendary delivery:
it is consumed on redemption like other objectives, awards one random
Legendary prize, and is not returned. There is no once-per-player limit.
The legacy claim tracking file is ignored; existing `mystery_dragon`
bounties now behave like any ordinary Legendary bounty.

**Mything (2):** A rare SirJain Plushie grants the **King of Brainmeth
Crown**; a Warden Trophy mounted on its large pillar grants the **Kill
Switch**. Each is guaranteed and unavailable from ordinary Legendary
reward rolls. They are the sole non-operator sources. The intended label
is **Mything**; Bountiful's built-in `EPIC` rarity (purple) is used to
make these rarer than regular `RARE` (yellow) Legendary contracts.

## Rewards — exactly three Bountiful reward pools

The decree references `common_objs`, `legendary_objs`, `mything_objs`
and `common_rews`, `legendary_rews`, `mything_rews`.
Only three labels appear: **??? Common Reward**,
**??? Legendary Reward** and **??? Mything Reward**.

- Common: 26 delivery objectives and 29 random building shipments.
- Legendary: 8 objectives and 35 random custom prizes.
- Mything: 2 special objectives, each with one exclusive guaranteed prize.

Random prize selection occurs server-side on redemption. The Mything
Bountiful pool uses the two protected fixed grant commands, not an extra
random aggregate loot table. Legacy Uncommon deliveries still map to
Common. Legacy Dragon Egg grants map to regular Legendary.

**Starter reputation appearance:** about **49.5% Common, 49.5% Legendary,
1% Mything**. Based on Bountiful's actual initial reward-first selection,
pool multipliers are respectively 1, 4 and 0.16, with built-in
COMMON/RARE/EPIC rarities. Those probabilities **vary with reputation**:
at higher reputation, Common becomes less likely under Bountiful's
rarity-weighting scheme. This is a starting-board calibration, not a
guaranteed per-board quota. Verify on an actual board before deployment.

The 15-minute board refresh and the 3-bounties-taken-per-Minecraft-day
quota are unchanged.

## Rewards

**Common — 29 equally possible shipments:** cherry logs + saplings (64+4),
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
32 deepslate emerald ore, 64 waxed oxidised copper,
and 16 spore blossoms.

**Legendary — 35 equally possible ordinary prizes:** existing grimoires,
potions, gadgets, collectibles and custom music disc rewards, excluding the
exclusive King of Brainmeth Crown and Kill Switch. The two Mything challenges grant their unique prizes outside the random lottery.

The 16 previously Uncommon shipment definitions remain under the legacy
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
5. Complete Common, Legendary (including Dragon Egg) and Mything hand-ins; check
   quantities, reward isolation, collector exclusivity and egg consumption.
6. **Do not activate the Kill Switch outside an isolated test container.**

IMPORTANT: Bountiful 8.0.0-beta.2 has publicly reported
NeoForge villager/board NPE and server hangs when bounties are redeemed
near villagers. Test redemptions on the isolated test world before
moving board anywhere near villager pathfinding. Keep this change on the 1.21.1 branch isolated until live validation.
