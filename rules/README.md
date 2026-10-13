# Brainmeth 1.21.1 gameplay rules

The migration deploy script installs `rules/brainmeth-rules` into the
**isolated test world's** `world/datapacks/brainmeth-rules` before server start.

- Mending can only be newly applied to **netherite armour and tools**:
  helmet, chestplate, leggings, boots, sword, pickaxe, axe, shovel, hoe.
  This is a vanilla enchantment registry override using `supported_items`,
  not an extra mod. Mending books may still be found/traded, but cannot be
  applied to other items (including Elytra). Existing illegitimate gear
  enchantments are **not automatically stripped**.
- Vanilla insomnia phantom spawning is disabled by `gamerule doInsomnia false`
  on world load/reload. Phantoms can still be summoned or spawned by modded
  mechanics; this does not delete phantom membranes from the game.

Test in-game: anvil Mending on Elytra must fail; netherite pickaxe and
netherite chestplate must accept Mending. Confirm
`/gamerule doInsomnia` returns `false`, and check vanilla phantom spawn.
If another mod/datapack replaces `minecraft:mending`, inspect datapack order.
