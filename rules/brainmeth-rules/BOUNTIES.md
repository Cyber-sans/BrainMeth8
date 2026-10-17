# Brainmeth Community Bounties — NeoForge 1.21.1

Bountiful boards remain completely normal: players can craft, place, break,
move and use them, and boards generate naturally in villages. Vanilla Bountiful
decrees and contracts remain available. The **Brainmeth Community Bounties**
decree is special: it never generates, reveals from blank decrees, or appears
in wandering-trader offers. Only an operator can issue it.

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

## Objectives

**Common (11):** 3 Naturalist Chrysalises; 3 Snail Shells; 10 Lizard
Tails; 32 Vinery Red Savanna Grapes; 32 Dark Cherries; 32 HerbalBrews
Coffee Beans; 16 Dried Oolong Tea; 64 Supplementaries Flax; 32 Rope;
3 Snort Sherds; 64 Vanilla Backport Resin Clumps.

**Uncommon (13):** 3 Deeper & Darker Soul Crystals; 16 Resonarium;
3 Temple Gloomsherds; 64 Echo Logs; 64 Naturalist Shellstone Bricks;
10 Vinery Chorus Wines; 10 Rooibos Teas; 3 Supplementaries Netherite
Doors; 3 Sniffer Eggs; 3 Recovery Compasses; 3 Ominous Trial Keys;
3 Pigstep discs; 3 Creaking Hearts.

**Rare (8):** 1 Ancient Anima; 1 Blazing Eye; 1 Obsidian Heart;
1 Void Thorn; 1 Heart of the Deep; 1 Four Calamities Seal (crafted
shapeless from all four BOMD materials, consuming them); 3 Nether Stars;
1 Dragon Egg. The Dragon Egg is returned when redeemed. Its custom
reward is **one-time per player**; later redemptions return the egg with
no additional prize, enforced in
`world/brainmeth-dragon-egg-claims.json`.

**Exclusive collectors (2):**
- Deliver the *SirJain Rare Plushie* (`perfectplushies:sirjain_plushie_rare`)
  => **King of Brainmeth Crown**, the ONLY non-operator source.
- Deliver a *Warden Trophy mounted on its large pillar* (component
  `trofers:trophy=trofers:warden`) => **Kill Switch**, the ONLY
  non-operator source.

The matching system forbids mixing any Common/Uncommon/Rare/special
markers, even though all are under a single Brainmeth decree.
Both collector items are obtainable only as rare random plushie/trophy
rewards; prior natural acquisition locks remain in place. The named
specials do not appear in the 36-option ordinary Rare reward pool.
The original Crown of Nothing remains in that ordinary Rare pool.

## Rewards

**Common (13 shipments):** cherry logs + saplings (64+4),
mangrove logs + roots (64+16), 64 warped stems, 64 crimson stems,
pale oak logs + saplings (64+4), 64 calcite, matched cyan and light-blue
terracotta (32+32, not the earlier rejected 64+64), 64 copper grates,
lanterns + chains (32+32), 64 mushroom stems,
moss blocks + carpet (64+64), mud bricks + packed mud (64+64), and
32 decorated pots.

**Uncommon (16 shipments):** 64 sponges, powered rails, blue ice,
sea lanterns, pearlescent froglights, end rods, shroomlights,
gilded blackstone, crying obsidian or dark prismarine;
128 quartz blocks; 64 tube coral blocks; 64 Naturalist Shellstone
Bricks; 32 deepslate emerald ore; 64 waxed oxidised copper; 16
Spore Blossoms.

**Rare (36 custom reward choices):** every previously created custom
reward (grimoires, potions, gadgets, unique collectibles, discs with
placeholder audio, etc.) except the reserved Kill Switch and new
King of Brainmeth Crown; ordinary building supplies are not here.
Named individual reward entries run as server-authorised
`brainmethbounty grant "%PLAYER_NAME%" rare_<reward_id>` commands;
they invoke existing private admin-only loot tables. Non-op players
cannot invoke that command.

## Gameplay verification required

1. Confirm vanilla boards can be crafted, placed, broken and used by non-OP
   players, and village boards still appear in newly generated villages.
2. Confirm new boards produce normal vanilla decrees and never Brainmeth
   decrees; blank crafted decrees must never reveal Brainmeth.
3. As an OP, run the `/give` command above, inspect the named Brainmeth
   decree, insert it into a normal board and wait for fresh custom contracts.
4. Confirm a board with both a vanilla and Brainmeth decree never mixes
   their objective/reward pools.
5. Complete Common, Uncommon, Rare and special hand-ins; check item quantities,
   reward isolation and persistent one-time Dragon Egg claim.
6. **Do not activate the Kill Switch outside an isolated test container.**

IMPORTANT: Bountiful 8.0.0-beta.2 has publicly reported
NeoForge villager/board NPE and server hangs when bounties are redeemed
near villagers. Test redemptions on the isolated test world before
moving board anywhere near villager pathfinding. No 26.2 production
environment has been changed.
