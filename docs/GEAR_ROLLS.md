# Random gear stat rolls

Implemented in `custom-mods/brainmeth-core` (`BrainmethGearRolls.java`, plus
`mixin/ItemCraftedByMixin.java`). Server-only: the roll is stored in the item's
custom data and shown as a lore line, so players need no extra client mod.

## When a roll happens
- **Crafted** tools and armour roll once, when taken from a crafting grid
  (normal click or shift-click).
- **Never rolled**: chest loot, mob drops, fishing, villager trades, and items
  from creative or commands.
- **Repairing** two tools in the crafting grid gives an unrolled result, so
  repair crafting can't be used to re-roll.
- **Upgrading** rolled gear in a smithing table (diamond to netherite, or any
  other smithing upgrade that changes the item) rolls again and **keeps the
  better tier**. Unrolled gear (for example looted diamond armour) stays unrolled
  when upgraded. Armour trims do not re-roll.
- There is no other way to raise or re-roll a bonus.

## Tiers (every rollable item)

| Tier | Chance | Lore colour |
|---|---|---|
| Plain (no bonus) | 20% | none shown |
| Fine | 50% | green |
| Superior | 20% | blue |
| Exquisite | 8% | purple |
| Legendary | 2% | gold |

## Bonus per item type

| Item | Stat | Fine | Superior | Exquisite | Legendary |
|---|---|---|---|---|---|
| Pickaxe | Fortune: chance per ore drop of +1 extra item | 3% | 5% | 7% | 10% |
| Sword | Sharpness: attack damage | +2% | +3% | +5% | +8% |
| Axe, shovel, hoe | Efficiency: mining speed | +3% | +5% | +7% | +10% |
| Armour | Protection: all damage | 1% | 2% | 3% | 4% |
| Armour | Fire Protection: fire damage | 2% | 4% | 6% | 8% |
| Armour | Blast Protection: explosion damage | 2% | 4% | 6% | 8% |
| Armour | Projectile Protection: projectile damage | 2% | 4% | 6% | 8% |

- Each armour piece gets one of its four stats at random.
- Armour bonuses from all worn pieces add up, capped at **25%** reduction per hit.
  They stack on top of normal enchantments.
- Fortune bonus applies only to blocks in the `c:ores` tag and only to their
  products (raw iron, diamonds...), never to the ore block itself, and not with
  Silk Touch. It stacks with real Fortune.
- Sword and mining-speed bonuses use vanilla attributes, so they also appear in
  the normal "When in Main Hand" tooltip.

## Tests before production
1. Craft each tool type and an armour piece, by clicking and by shift-clicking;
   every one should get a roll (most with a lore line).
2. Take tools from chests, villagers and `/give`; none should roll.
3. Combine two damaged tools in the crafting grid; the result has no roll.
4. Upgrade a rolled diamond pickaxe and a rolled diamond sword to netherite; check
   the action-bar message, that the better tier is kept, and that the netherite
   sword shows netherite damage (not diamond).
5. Mine ores with a Legendary pickaxe and compare drop counts with a Plain one.
6. Take fire, explosion, arrow and melee damage in rolled armour; check reductions
   and that the 25% cap holds.
