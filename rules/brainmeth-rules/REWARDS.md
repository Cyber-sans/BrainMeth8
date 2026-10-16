# Brainmeth bounty rewards — batches 1, 2, 3, 4, 5 and 6 (test branch only)

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
- /loot give @p loot brainmeth:rewards/uncommon/levitation_grimoire
- /loot give @p loot brainmeth:rewards/uncommon/healing_grimoire
- /loot give @p loot brainmeth:rewards/uncommon/lightning_grimoire
- /loot give @p loot brainmeth:rewards/uncommon/knockback_stick
- /loot give @p loot brainmeth:rewards/uncommon/potion_everything
- /loot give @p loot brainmeth:rewards/uncommon/potion_shrink
- /loot give @p loot brainmeth:rewards/uncommon/potion_grow
- /loot give @p loot brainmeth:rewards/uncommon/potion_creative
- /loot give @p loot brainmeth:rewards/uncommon/super_tnt
- /loot give @p loot brainmeth:rewards/uncommon/ultimate_chorus_fruit
- /loot give @p loot brainmeth:rewards/uncommon/splash_binding
- /loot give @p loot brainmeth:rewards/uncommon/splash_vanishing
- /loot give @p loot brainmeth:rewards/uncommon/splash_coronavirus
- /loot give @p loot brainmeth:rewards/uncommon/fake_tnt
- /loot give @p loot brainmeth:rewards/uncommon/naughty_shovel
- /loot give @p loot brainmeth:rewards/uncommon/time_traveller_watch
- /loot give @p loot brainmeth:rewards/uncommon/mild_inconvenience_staff
- /loot give @p loot brainmeth:rewards/uncommon/summoning_bow
- /loot give @p loot brainmeth:rewards/uncommon/tree_of_life
- /loot give @p loot brainmeth:rewards/uncommon/orbital_strike_gun
- /loot give @p loot brainmeth:rewards/uncommon/crystal_ball
- /loot give @p loot brainmeth:rewards/uncommon/kill_switch
- /loot give @p loot brainmeth:rewards/uncommon/cognitohazard_book
- /loot give @p loot brainmeth:rewards/uncommon/crown_of_nothing
- /loot give @p loot brainmeth:rewards/uncommon/fake_death_certificate
- /loot give @p loot brainmeth:rewards/uncommon/butlers_bell
- /loot give @p loot brainmeth:rewards/uncommon/book_of_wisdom
- /loot give @p loot brainmeth:rewards/uncommon/replicating_cake
- /loot give @p loot brainmeth:rewards/uncommon/manifesto

## Magic flow

A player holding any grimoire **right-clicks in the air with an ordinary
stick somewhere in their inventory**. One ordinary stick and one grimoire
are consumed, and a named enchanted stick is produced. Keep the wands: charges
replenish while the player is logged out, based on wall-clock time, not ticks.

- Firework Wand: left-click a block -> launches 10 fireworks. Up to 10 charges,
  one charge every 600 real seconds.
- Levitation Wand: right-click in air -> hovers one block above terrain for 10 real minutes. Charges: 3, +1 per real hour. Uses collision-aware movement and never enables unrestricted flying. The effect timer continues while offline.
- Healing Wand: right-click in air -> restores full health to living, non-spectator players within 128 blocks (8 chunks), same dimension. Charges: 1, +1 per real hour.
- Lightning Wand: look at a block within 64 blocks and right-click in air -> 6 lightning bolts strike its surface at 8-tick intervals. Charges: 3, +1 per 3 real hours.
- Knockback Stick: direct reward, enchanted with Knockback V; no grimoire or rechargeable charges.
- Rain Wand: right-click in air -> starts 10 minutes of Overworld rain.
  One charge, replenished every 86400 real seconds. Does not work outside
  the Overworld. It changes the world weather rather than a single player's weather.

Cooldowns are stored per individual wand in vanilla custom-data components.
None of the magic wands is craftable or obtainable outside grimoire conversion.
The renamed Poo mud is a gag item: it becomes ordinary mud after placement;
it is not currently a persistent special block.

## Test limits

Validation checks source file content and the GitHub Action must compile the
custom Java mod. These do not prove in-game behaviour: test grimoire conversion, all wand powers, hover terrain-following,
block hitting, rain duration, lightning effects, Knockback V, offline recharge and admin /loot before making
rewards available through Bountiful.

Do not deploy to production. The 1.21.1 branch is isolated from 26.2.

The Extinguishing Grimoire has been removed from the design. The old Repulsion Grimoire has been replaced by the directly awarded Knockback Stick V. Do not add normal loot/drop/crafting recipes for these items before Bountiful integration.

## Batch 3 — uncommon consumables

- Potion of Everything: a fixed selection of beneficial effects for 3 minutes, plus instant heal/saturation.
- Shrinking Potion: sets player size to 0.2x for **10 real minutes**.
- Growing Potion: sets player size to 2x for **10 real minutes**.
- Creative Potion: **2 real seconds**, granting flight and invulnerability without switching
  gamemode or unlocking Creative inventory. No infinite blocks/items; slow falling for 8 seconds after.
- Compressed TNT: delayed explosion energy equivalent to ten ordinary TNT blocks;
  explosion radius scales as the cube root of energy, rather than multiplying radius by ten.
- Ultimate Chorus Fruit x8: each use samples safe, *currently loaded* destinations
  within a 1000-block radius. An unsuccessful search does not consume a fruit or generate chunks.
- Splash Potion of Binding x2: applies Binding to worn armour on splash.
- Splash Potion of Vanishing x2: applies Vanishing to worn armour on splash.
- Splash Potion of Coronavirus x3: Nausea, Hunger, Oozing and Weakness for 8 minutes on splash.
- Fake TNT x3: placed TNT is tracked in the world file `brainmeth-fake-tnt.json`.
  When primed it fizzles instead of exploding, then becomes a TNT block again.
  Priming via flint, redstone or other explosions should be checked in-game.

### In-game verification

Test all consumables in the isolated 1.21.1 test world with `/loot give`.
Verify potion expiry after logout and restart, item stacks for splash potions,
safe teleport/no chunk generation, anti-duplication Creative restrictions,
TNT response to redstone and flint/steel, and fake TNT recovery.
Never activate these rewards in production until validated. No Bountiful entries yet.


## Batch 4 — weapons, pranks, rewinds and the colossal Tree of Life

All five remain **admin-only** and are not yet available through normal survival
or Bountiful. No additional mod dependency or client download is needed.

- Naughty Shovel: iron shovel branded "Slavery I" (custom lore/behaviour rather
  than a global enchantment registry); hitting another player forces their
  server-side crouch pose for 20 real seconds. Two charges, one regains every
  six real hours. Normal PvP rules apply.
- Time Traveller's Pocket Watch: right-click to return to the position and
  dimension from 15 real seconds before. Requires 15 seconds of online history;
  checks loaded chunks, border and collision. One charge every six real hours;
  an unsafe destination costs no charge. History resets after server restart.
- Staff of Mild Inconvenience: right-click a player to rotate them 180 degrees.
  3 stored uses; one use regenerates every 20 real minutes.
- Summoning Bow: on striking a non-boss entity, teleports it to the archer in
  the same dimension if the destination is collision-safe. Ordinary bow
  durability is finite. Anvil repair is rejected; repair exploits must be
  tested in-game, including Mending/combining.
- Tree of Life: enchanted oak sapling; place it on a valid surface, then
  right-click it with **64 bone meal in one stack** to grow the huge tree.
  Approximate world footprint: ~78-block-wide leafy crown (radius 39) at
  88 blocks above the ground with 24-block crown height in each direction,
  reaching **~112 blocks** above the sapling, plus an enormous tapering
  trunk about 10 blocks across at its base and thick branches.
  The growth consumes all 64 bone meal once and then builds over many ticks,
  at most 650 blocks per tick, without forcing unloaded chunks. Existing
  solid structures are preserved and a clear core is required. Only one
  growth can run at once. Progress and special saplings are stored in
  \`world/brainmeth-life-trees.json\`, so an interrupted growth resumes
  after server restart when the chunks are reloaded.
  Natural sapling growth is suppressed until you give the full bone meal.
  Height/space requirement: build up to 118 blocks above sapling.

### Batch 4 in-game validation
Test the shovels on another player, actual crouch visuals and expiration,
offline charge recovery, watch cross-dimension/blocked rewind, staff direction,
arrows and boss immunity, finite bow durability, and Tree of Life from
planting through restart/resume and full giant generation. These Java builds
are NOT substitutes for in-world testing. Do not deploy to production.


## Batch 5 — one-block orbital strike

Super TNT and Fake TNT were implemented in Batch 3, and the giant Tree of
Life was implemented in Batch 4. The only outstanding Batch-5 feature was
the Orbital Strike Gun.

- Orbital Strike Gun: a uniquely named/enchantment-glowing vanilla crossbow,
  functioning as a remote-designation weapon using server-side particles and
  sounds. Aim and right-click to mark one block within 128 blocks.
- After a 45-tick windup a dramatic END_ROD pillar, FLASH, ELECTRIC_SPARK,
  smoke and thunder occur at the target. The strike removes **one block**,
  with **no explosion or drops**. It never intentionally damages entities.
- One use every **10 real minutes**, per-item cooldown stored in its
  custom-data component. Invalid targets do not use the charge.
- Unloaded chunks are never force-loaded. The gun refuses unbreakable blocks,
  liquids, block entities/inventories, and interactions forbidden by basic
  world permissions; the target is revalidated at impact. It prevents multiple
  simultaneous strikes from a player and caps world-wide active strikes at 8.
- Client-side appearance is the vanilla crossbow; the sky beam and impact
  effects are custom server visuals. A bespoke sci-fi model would require an
  additional client resource pack and is not part of this batch.

### Live-test checklist
Check right-clicking a block and aiming in air, 128-block range, one-block
destruction, protected blocks and containers, cooldown across relog/restart,
no drops or extra entity damage, and the 45-tick warning effects.

## Remaining planned unusual rewards

The generic **rare music disc has been removed from the roadmap**, per
request. The two specifically requested custom music discs remain on the
wish list, subject to obtaining the required audio rights.

- Herobrine Head; Kanye West "Flashing Lights" disc; Drake "Passionfruit" disc.
- Random Perfect Plushies collectible; random Trofers trophy plus its stand.
- Cognitohazard Book (signed by 文); Crown of Nothing; Communist Manifesto.
- Fake Death Certificate; Butler's Bell (Mr. Deeds); Book of Wisdom (Wanda);
  Replicating Cake; Crystal Ball; single-use server restart Kill Switch.

No new mod, resource pack, recipes or Bountiful reward tables are installed
by Batch 5. These remain separate future work.

## Batch 6 — special rewards and collectibles

- **Crystal Ball**: Hold it and run `/crystalball send PlayerName your message`.
  Works for online players immediately, offline players on their next login.
  The receiver sees a large on-screen title/subtitle and a copy in chat.
  Up to 120 characters; 3 real hours between uses. Pending messages persist
  in `world/brainmeth-crystal-messages.json` (8/player, 256 overall).
- **Kill Switch**: Single-use stone button; on test only, gives players 10
  seconds warning then executes the vanilla `stop` command. Docker's
  `restart: unless-stopped` brings the Minecraft container back. The test
  container alone sets `BRAINMETH_ALLOW_KILLSWITCH=true`. This mechanism
  MUST be tested only on the isolated test server.
- **Cognitohazard**: Written book, signed by 文. Opening it kills the reader.
- **Crown of Nothing**: Wearable golden helmet with empty attribute modifiers
  (zero bonus armour), plus a server-side text display bearing the title
  "King of Absolutely Nothing" below the wearer's name.
- **Fake Death Certificate**: Paper, reusable; right-click broadcasts one
  of eight fake death messages globally, without changing life or inventory.
  Five-second anti-spam cooldown.
- **Butler's Bell**: Summons an invulnerable, non-trading nitwit villager
  named Mr. Deeds who follows its owner for five minutes. 24 real-hour
  cooldown per bell. The NPC is removed when its owner logs out.
- **Book of Wisdom**: Paper. Each use broadcasts one of the **94 exact**
  user-provided fortune messages as a message from Wanda, with Reddit
  username credits removed. One use per real hour.
- **Replicating Cake**: Place the named cake; it regenerates after all
  seven slices are eaten. If left untouched for a real 24-hour period it
  creates a second cake on a valid adjacent block. Clones also replicate,
  and there is no total lifetime cap. It refuses to load chunks or replace
  other blocks. Persistent state is in `world/brainmeth-replicating-cakes.json`.
  Processing is rate limited so it cannot scan every cake on every tick.
- **The Communist Manifesto**: One bounty reward yields **four signed written
  books**, attributed to Marx & Engels, preserving the entire Samuel Moore
  1888 English translation, sourced from the public-domain GITenberg
  copy of Project Gutenberg #61. The 295 readable pages require four
  volumes because Minecraft limits individual written books to 100 pages.

### Batch 6 gameplay checks

Test /loot administration, Crystal Ball cross-login delivery and restart
persistence, the Kill Switch stop/restart sequence on **test only**, immediate
book death, crown hologram (including removal/disconnect/relogin), Mr. Deeds
following and expiry, Wanda's cooldown, the cake's final-slice restoration
and one-day cloning, and the order/readability of all four Manifesto volumes.
Only Java compilation and offline catalogue validation are automated;
**in-game behaviour is not yet verified**.

The generic rare music disc was already removed from the roadmap in Batch 5;
only the two specifically requested custom-song discs remain planned.
