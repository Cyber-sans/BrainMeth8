package dev.cybersans.brainmeth;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.inventory.ItemCombinerMenu;
import net.minecraft.world.inventory.MerchantMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.AnimalArmorItem;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.AxeItem;
import net.minecraft.world.item.HoeItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.PickaxeItem;
import net.minecraft.world.item.ShovelItem;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.level.BlockDropsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.util.ArrayList;
import java.util.List;

/** Random bonus stat rolled once when a tool or armour piece is crafted.
 * Chest loot, mob drops and trades never roll. Upgrading rolled gear in a smithing
 * table (e.g. to netherite) rolls again and keeps the better of the two.
 * The roll is stored in custom data and shown as a lore line, so no client mod is needed.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethGearRolls {
    private static final String ROLL = "brainmeth_roll";
    private static final ResourceLocation BONUS_ID = ResourceLocation.fromNamespaceAndPath(BrainmethCore.MOD_ID, "gear_roll");
    /** Combined cap for all armour bonuses against a single hit, in percent. */
    static final int MAX_ARMOUR_REDUCTION = 25;
    private static int elapsed;

    /** Weights add up to 100, so each weight is the percentage chance of that tier. */
    enum Tier {
        PLAIN(20, ChatFormatting.GRAY),
        FINE(50, ChatFormatting.GREEN),
        SUPERIOR(20, ChatFormatting.BLUE),
        EXQUISITE(8, ChatFormatting.DARK_PURPLE),
        LEGENDARY(2, ChatFormatting.GOLD);

        final int weight;
        final ChatFormatting color;
        Tier(int weight, ChatFormatting color) { this.weight = weight; this.color = color; }

        String label() { return name().charAt(0) + name().substring(1).toLowerCase(); }
    }

    /** Bonus percent for FINE, SUPERIOR, EXQUISITE and LEGENDARY respectively. */
    enum Stat {
        FORTUNE("Fortune", 3, 5, 7, 10),
        SHARPNESS("Sharpness", 2, 3, 5, 8),
        EFFICIENCY("Efficiency", 3, 5, 7, 10),
        PROTECTION("Protection", 1, 2, 3, 4),
        FIRE_PROTECTION("Fire Protection", 2, 4, 6, 8),
        BLAST_PROTECTION("Blast Protection", 2, 4, 6, 8),
        PROJECTILE_PROTECTION("Projectile Protection", 2, 4, 6, 8);

        final String label;
        final int[] percent;
        Stat(String label, int... percent) { this.label = label; this.percent = percent; }

        int percentFor(Tier tier) { return tier == Tier.PLAIN ? 0 : percent[tier.ordinal() - 1]; }
    }

    private static final List<Stat> ARMOUR_STATS = List.of(Stat.PROTECTION, Stat.FIRE_PROTECTION,
        Stat.BLAST_PROTECTION, Stat.PROJECTILE_PROTECTION);

    private record Roll(Tier tier, Stat stat) {
        int percent() { return stat.percentFor(tier); }
        String lore() { return tier.label() + ": +" + percent() + "% " + stat.label; }
    }

    private BrainmethGearRolls() {}

    /** The stat family an item can roll, or null when the item never rolls. */
    private static List<Stat> statsFor(ItemStack stack) {
        Item item = stack.getItem();
        if (item instanceof PickaxeItem) return List.of(Stat.FORTUNE);
        if (item instanceof SwordItem) return List.of(Stat.SHARPNESS);
        if (item instanceof AxeItem || item instanceof ShovelItem || item instanceof HoeItem)
            return List.of(Stat.EFFICIENCY);
        if (item instanceof ArmorItem && !(item instanceof AnimalArmorItem)) return ARMOUR_STATS;
        return null;
    }

    private static Roll roll(List<Stat> stats, RandomSource random) {
        int pick = random.nextInt(100);
        Tier tier = Tier.PLAIN;
        for (Tier candidate : Tier.values()) {
            if (pick < candidate.weight) { tier = candidate; break; }
            pick -= candidate.weight;
        }
        return new Roll(tier, stats.get(random.nextInt(stats.size())));
    }

    private static Roll read(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null || !data.contains(ROLL)) return null;
        CompoundTag tag = data.copyTag().getCompound(ROLL);
        try {
            return new Roll(Tier.valueOf(tag.getString("tier")), Stat.valueOf(tag.getString("stat")));
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    private static String rolledItem(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getCompound(ROLL).getString("item");
    }

    /** Store the roll, refresh its lore line and rebuild attribute bonuses for the current item. */
    private static void apply(ItemStack stack, Roll roll, Roll previous) {
        String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        CustomData.update(DataComponents.CUSTOM_DATA, stack, tag -> {
            CompoundTag rollTag = new CompoundTag();
            rollTag.putString("tier", roll.tier().name());
            rollTag.putString("stat", roll.stat().name());
            rollTag.putString("item", itemId);
            tag.put(ROLL, rollTag);
        });

        List<Component> lines = new ArrayList<>(stack.getOrDefault(DataComponents.LORE, ItemLore.EMPTY).lines());
        if (previous != null) lines.removeIf(line -> line.getString().equals(previous.lore()));
        if (roll.tier() != Tier.PLAIN) {
            lines.add(Component.literal(roll.lore())
                .withStyle(style -> style.withItalic(false).withColor(roll.tier().color)));
        }
        stack.set(DataComponents.LORE, new ItemLore(lines));

        // Start from the item's own defaults so a smithing upgrade does not keep the old tier's damage.
        Holder<Attribute> attribute = switch (roll.stat()) {
            case SHARPNESS -> Attributes.ATTACK_DAMAGE;
            case EFFICIENCY -> Attributes.BLOCK_BREAK_SPEED;
            default -> null;
        };
        if (attribute != null) {
            ItemAttributeModifiers modifiers = stack.getPrototype()
                .getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
            if (roll.tier() != Tier.PLAIN) {
                AttributeModifier.Operation operation = attribute == Attributes.ATTACK_DAMAGE ?
                    AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL : AttributeModifier.Operation.ADD_MULTIPLIED_BASE;
                modifiers = modifiers.withModifierAdded(attribute,
                    new AttributeModifier(BONUS_ID, roll.percent() / 100.0D, operation), EquipmentSlotGroup.MAINHAND);
            }
            stack.set(DataComponents.ATTRIBUTE_MODIFIERS, modifiers);
        }
    }

    /** Called from ItemCraftedByMixin whenever a player takes a crafted item. */
    public static void onCrafted(ItemStack stack, Level level, Player player) {
        if (level.isClientSide() || player == null || stack.isEmpty() || read(stack) != null) return;
        List<Stat> stats = statsFor(stack);
        if (stats == null) return;
        // Trades and smithing/anvil results also report as "crafted"; only crafting grids roll.
        if (player.containerMenu instanceof MerchantMenu || player.containerMenu instanceof ItemCombinerMenu) return;
        boolean craftingGrid = false;
        for (Slot slot : player.containerMenu.slots) {
            if (!(slot.container instanceof CraftingContainer)) continue;
            craftingGrid = true;
            // Combining two worn tools in the grid (repair) must not hand out a fresh roll.
            if (statsFor(slot.getItem()) != null) return;
        }
        if (!craftingGrid) return;
        apply(stack, roll(stats, player.getRandom()), null);
    }

    /** Smithing copies custom data, so an item id change means rolled gear was upgraded. */
    private static void checkUpgrade(ServerPlayer player, ItemStack stack) {
        Roll old = read(stack);
        if (old == null) return;
        String itemId = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        if (itemId.equals(rolledItem(stack))) return;
        List<Stat> stats = statsFor(stack);
        if (stats == null) return;
        Roll fresh = roll(stats, player.getRandom());
        Roll kept = fresh.tier().ordinal() > old.tier().ordinal() ? fresh : old;
        apply(stack, kept, old);
        player.displayClientMessage(Component.literal("Upgrade re-roll: " +
            (kept == fresh ? "new roll kept! " : "original roll kept. ") +
            (kept.tier() == Tier.PLAIN ? "No bonus." : kept.lore())), true);
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        if (++elapsed % 20 != 0) return;
        for (ServerPlayer player : event.getServer().getPlayerList().getPlayers()) {
            var inventory = player.getInventory();
            for (int i = 0; i < inventory.getContainerSize(); i++) checkUpgrade(player, inventory.getItem(i));
        }
    }

    @SubscribeEvent
    public static void onBlockDrops(BlockDropsEvent event) {
        ItemStack tool = event.getTool();
        Roll roll = read(tool);
        if (roll == null || roll.stat() != Stat.FORTUNE || roll.tier() == Tier.PLAIN) return;
        if (!event.getState().is(Tags.Blocks.ORES)) return;
        ServerLevel level = event.getLevel();
        var silkTouch = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(Enchantments.SILK_TOUCH);
        if (EnchantmentHelper.getItemEnchantmentLevel(silkTouch, tool) > 0) return;
        Item blockItem = event.getState().getBlock().asItem();
        for (ItemEntity drop : event.getDrops()) {
            ItemStack item = drop.getItem();
            // Only the ore's products (raw iron, diamonds...), never the ore block itself.
            if (item.is(blockItem) || level.random.nextInt(100) >= roll.percent()) continue;
            ItemStack bigger = item.copy();
            bigger.grow(1);
            drop.setItem(bigger);
        }
    }

    @SubscribeEvent
    public static void onIncomingDamage(LivingIncomingDamageEvent event) {
        LivingEntity entity = event.getEntity();
        DamageSource source = event.getSource();
        if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) return;
        int total = 0;
        for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
            Roll roll = read(entity.getItemBySlot(slot));
            if (roll == null) continue;
            boolean applies = switch (roll.stat()) {
                case PROTECTION -> true;
                case FIRE_PROTECTION -> source.is(DamageTypeTags.IS_FIRE);
                case BLAST_PROTECTION -> source.is(DamageTypeTags.IS_EXPLOSION);
                case PROJECTILE_PROTECTION -> source.is(DamageTypeTags.IS_PROJECTILE);
                default -> false;
            };
            if (applies) total += roll.percent();
        }
        if (total <= 0) return;
        event.setAmount(event.getAmount() * (1.0F - Math.min(total, MAX_ARMOUR_REDUCTION) / 100.0F));
    }
}
