# Random gear stat rolls

Implemented in `custom-mods/brainmeth-core` (`BrainmethGearRolls.java`, plus the
`ItemCraftedByMixin` and `ItemCombinerQuickMoveMixin` mixins). Server-only: the roll is stored in the item's
custom data and shown as a lore line, so players need no extra client mod.

## When a roll happens
- **Crafted** tools and armour roll once, when taken from a crafting grid
  (normal click or shift-click).
- **Not rolled when obtained**: chest loot, mob drops, fishing, villager trades,
  and items from creative or commands.
- **Repairing** two tools in the crafting grid gives an unrolled result, so
  repair crafting can't be used to re-roll.
- **Upgrading** in a smithing table (diamond to netherite, or any other smithing
  upgrade that changes the item):
  - unrolled gear, such as looted diamond armour, gets its first roll;
  - rolled gear rolls again and **keeps the better tier**.
  Armour trims never roll. Shift-clicking an upgrade with a full inventory does
  nothing until there is room, so a roll can't be previewed and swapped out.
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
| Sword, axe | Sharpness: attack damage | +2% | +3% | +5% | +8% |
| Shovel, hoe | Efficiency: mining speed | +3% | +5% | +7% | +10% |
| Bow, crossbow | Power: projectile damage | +2% | +3% | +5% | +8% |
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
- Sharpness and Efficiency bonuses use vanilla attributes, so they also appear in
  the normal "When in Main Hand" tooltip.
- Power boosts every arrow fired by the rolled bow or crossbow (including each
  Multishot arrow), and firework rockets fired from a rolled crossbow held in
  either hand. It stacks with the Power enchantment. Thrown items, tridents and
  dispensers are unaffected.

## Tests before production
1. Craft each tool type and an armour piece, by clicking and by shift-clicking;
   every one should get a roll (most with a lore line).
2. Take tools from chests, villagers and `/give`; none should roll until upgraded.
3. Combine two damaged tools in the crafting grid; the result has no roll.
4. Upgrade a looted (unrolled) diamond piece to netherite by clicking and by
   shift-clicking; both should roll. Trim a looted piece; it should not roll.
5. Upgrade a rolled diamond pickaxe and a rolled diamond sword or axe to netherite;
   check the action-bar message, that the better tier is kept, and that the netherite
   weapon shows netherite damage (not diamond).
6. Shoot the same target with a Legendary and a Plain bow, and with crossbow
   arrows and fireworks; the rolled weapon should deal more. Reload the area and
   check stuck arrows aren't boosted twice.
7. Mine ores with a Legendary pickaxe and compare drop counts with a Plain one.
8. Take fire, explosion, arrow and melee damage in rolled armour; check reductions
   and that the 25% cap holds.
