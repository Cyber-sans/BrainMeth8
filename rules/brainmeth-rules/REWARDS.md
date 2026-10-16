# Brainmeth bounty rewards — batch 1 (test branch only)

All entries are deliberately **admin-only** loot tables; no recipes, mob drops,
advancements or naturally generated chest references are added. Bountiful will
refer to these later. Rewards use vanilla items so brainmeth-core stays server-only
and AutoModpack does not need new assets for this batch.

Run on the Minecraft test server (as an operator):
- /loot give @p loot brainmeth:rewards/common/sponges
- /loot give @p loot brainmeth:rewards/common/trapped_chests
- /loot give @p loot brainmeth:rewards/common/deepslate_emerald_ore
- /loot give @p loot brainmeth:rewards/uncommon/poo
- /loot give @p loot brainmeth:rewards/uncommon/firework_grimoire
- /loot give @p loot brainmeth:rewards/uncommon/rain_grimoire

## Magic flow

A player holding either grimoire **right-clicks in the air with an ordinary
stick somewhere in their inventory**. One ordinary stick and one grimoire
are consumed, and a named enchanted stick is produced. Keep the wands: charges
replenish while the player is logged out, based on wall-clock time, not ticks.

- Firework Wand: left-click a block -> launches 10 fireworks. Up to 10 charges,
  one charge every 600 real seconds.
- Rain Wand: right-click in air -> starts 10 minutes of Overworld rain.
  One charge, replenished every 86400 real seconds. Does not work outside
  the Overworld. It changes the world weather rather than a single player's weather.

Cooldowns are stored per individual wand in vanilla custom-data components.
Neither magic wand is craftable or obtainable outside grimoire conversion.
The renamed Poo mud is a gag item: it becomes ordinary mud after placement;
it is not currently a persistent special block.

## Test limits

Validation checks source file content and the GitHub Action must compile the
custom Java mod. These do not prove in-game behaviour: test grimoire conversion,
block hitting, rain duration, offline recharge and admin /loot before making
rewards available through Bountiful.

Do not deploy to production. The 1.21.1 branch is isolated from 26.2.
