# Brainmeth Community Bounty Board — 1.21.1 TEST ONLY

The custom Bountiful 8.0.0-beta.2 decree is `brainmeth_board` and is the sole
naturally available decree on a freshly configured TEST world. Decree and
pool JSON are in `data/bountiful/bounty_decrees/brainmeth/` and
`data/bountiful/bounty_pools/brainmeth/`. In-game board
item is `bountiful:bountyboard`.

## Setup

After `./scripts/deploy.sh test`, **only OP players can place or break a board**
(`/give @p bountiful:bountyboard`). Ordinary players can accept and redeem
contracts at boards placed by an OP, but cannot place/break boards themselves.
Board crafting is disabled in survival, and new village boards do not spawn.
Previously generated village boards are inaccessible to non-OP players.
The allowed locations are saved in `world/brainmeth-bounty-boards.json`;
existing admin boards must be broken and placed once after the new guard
is installed to become available to ordinary players.
A pristine board generates the sole eligible `brainmeth_board` decree.
If starting with an existing board, replace it or replace its old decree;
old bounty papers do not auto-transform. Use `/bountiful reload` if
necessary, then inspect server logs for pool/command parse warnings.

The installation edits only
`/srv/minecraft/brainmeth/test-1211/config/bountiful/bountiful.json`:
hides Bountiful's default decrees/pools (not our `brainmeth/` paths),
sets one initial reward and one objective per paper, preserves local boards,
disables timer expiry, disables village board generation, and slows refreshes
to 15 minutes. Existing vanilla decree-bearing board items retain their NBT;
use a fresh board after updating the config and restarting. Bountiful
data matches tiers using marker/forbidMarkers in both directions; repRequired
0 for all. The source mod's reputation **still changes weighting** on
future papers, but nothing is gated behind a reputation threshold.

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

This is not yet live tested. On the test server:
1. Verify `bountiful-neoforge-8.0.0-beta.2.jar` is loaded and a fresh
   operator-placed board produces only the Brainmeth decree. Verify a non-OP
   cannot place/break a board, cannot use a pre-existing village board,
   and can use an OP-placed board across server restarts.
2. Inspect Bountiful logs for invalid item IDs or invalid command
   entries; test all modded objectives before opening to players.
3. Complete one Common and one Uncommon bounty; check quantities and
   absence of items from other tiers.
4. Generate/test a Rare objective and claim custom loot.
5. Check the four-drop seal recipe, dragon egg return and persistent
   one-time grant across server restarts.
6. Test a Rare SirJain plushie hand-in => crown, and a Warden trophy
   stand hand-in => Kill Switch; ensure no alternative rewards for
   those two hand-ins.
7. **Do not activate the Kill Switch outside the isolated test
   container**. The test compose flag alone enables controlled restart.

IMPORTANT: Bountiful 8.0.0-beta.2 has publicly reported
NeoForge villager/board NPE and server hangs when bounties are redeemed
near villagers. Test redemptions on the isolated test world before
moving board anywhere near villager pathfinding. No 26.2 production
environment has been changed.
