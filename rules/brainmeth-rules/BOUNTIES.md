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

## Objectives — exactly two tiers

**Common (26):** Original 13 Common and 13 former Uncommon objectives are
now one Common category, with the existing quantities kept pending a separate
fairness review. Includes Naturalist drops, Supplementaries supplies,
Vinery/HerbalBrews finished drinks, Deeper & Darker materials, and several
challenging vanilla exploration items. There is no active Uncommon tier.

**Legendary (10):** Seven regular high-difficulty challenges — Ancient Anima,
Blazing Eye, Obsidian Heart, Void Thorn, Heart of the Deep, the crafted Four
Calamities Seal, and 3 Nether Stars — plus three exclusive collectors:
1 Dragon Egg, the SirJain Rare Plushie, and the Warden Trophy on its large
pillar. Internally special collector entries have distinct matching markers
so that the Crown, Kill Switch and one-time Dragon Egg exception cannot
randomly be awarded to other Legendary objectives.

The Dragon Egg is returned on redemption, and the bonus prize is awarded
only once per player (recorded in world/brainmeth-dragon-egg-claims.json).
Only the rare SirJain plushie unlocks the King of Brainmeth Crown; only
the correctly mounted Warden trophy unlocks the Kill Switch. The prizes
themselves are not randomly included in the ordinary Legendary prize pool.

## Mystery rewards — exactly two pools

The decree references exactly two objective pools (`common_objs`,
`legendary_objs`) and two reward pools (`common_rews`, `legendary_rews`).
Contracts visibly offer only **??? Common Reward** or
**??? Legendary Reward**. One reward is granted per completed contract.
The concrete reward is drawn server-side **at redemption time**, not
stored in the bounty preview.

- **Common:** all 26 objectives can match 29 building-resource shipment
  entries, now drawing from one combined 29-outcome random loot table.
  The existing relative work values (6000 and 13000) remain so that
  more demanding Common objectives still have matching reward entries.
- **Legendary:** seven regular challenges select one of 35 original
  custom prizes. The three protected collector objectives use the same
  Legendary reward POOL JSON with different matching markers; their
  redemption commands retain their exclusive behaviour.
- Previously-issued `mystery_uncommon` papers are redirected to the new
  Common random loot table. Existing `mystery_legendary` and Dragon Egg
  redemptions now target the renamed Legendary loot table.

**Appearance target:** about half of new Brainmeth board contracts should
be Legendary at initial (zero) reputation. Bountiful normalises entry
weights by pool length, then applies rarity- and reputation-dependent
weights. The Legendary reward pool multiplier is tuned to **21.54**
against Common 1.0; protected specials stay relatively rare.
This is a *generation weight target*, not a hard per-board quota.
As board reputation increases the RARE rarity is less penalised, so the
Legendary share may rise substantially. Calibrate in-game with realistic
board reputation if a roughly even ratio must be maintained over time.

Ordinary village Bountiful decrees remain unaffected. The board refresh
interval remains 15 minutes; contracts do not expire, and players
can take at most three Brainmeth contracts per Minecraft day
(pickup-mixin behaviour still requires live validation).

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
exclusive King of Brainmeth Crown and Kill Switch. The 3 protected
collector challenges use fixed exceptional redemption behaviour, not
the 35-prize lottery.

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
5. Complete Common, Legendary and protected collector hand-ins; check item quantities,
   reward isolation and persistent one-time Dragon Egg claim.
6. **Do not activate the Kill Switch outside an isolated test container.**

IMPORTANT: Bountiful 8.0.0-beta.2 has publicly reported
NeoForge villager/board NPE and server hangs when bounties are redeemed
near villagers. Test redemptions on the isolated test world before
moving board anywhere near villager pathfinding. Keep this change on the 1.21.1 branch isolated until live validation.
