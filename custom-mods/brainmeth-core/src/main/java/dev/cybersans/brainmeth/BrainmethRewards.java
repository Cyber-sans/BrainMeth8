package dev.cybersans.brainmeth;

import it.unimi.dsi.fastutil.ints.IntList;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.FireworkExplosion;
import net.minecraft.world.item.component.Fireworks;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

import java.time.Instant;
import java.util.List;

/**
 * Bounty-only magic using tagged vanilla items. No client mod or recipes required.
 * Only the server changes charge counts, and every clock is a wall-clock epoch.
 * The existing launch scheduler is intentionally independent of this class.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethRewards {
    private static final String MARKER = "brainmeth_reward";
    private static final long FIREWORK_REGEN_SECONDS = 10 * 60;
    private static final long RAIN_REGEN_SECONDS = 24 * 60 * 60;

    private BrainmethRewards() {}

    @SubscribeEvent
    public static void onRightClickItem(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;

        ItemStack held = event.getItemStack();
        String kind = kind(held);
        switch (kind) {
            case "firework_grimoire", "rain_grimoire" -> {
                if (held.is(Items.BOOK)) enchantStick(player, held, kind);
            }
            case "rain_wand" -> {
                if (held.is(Items.STICK)) {
                    if (!level.dimension().equals(Level.OVERWORLD)) {
                        player.displayClientMessage(Component.literal("The Rain Wand only works in the Overworld."), true);
                    } else if (spendCharge(player, held, 1, RAIN_REGEN_SECONDS, "Rain Wand")) {
                        level.setWeatherParameters(0, 12000, true, false);
                        player.displayClientMessage(Component.literal("The heavens have opened."), true);
                    }
                }
            }
            default -> { return; }
        }
        event.setCancellationResult(InteractionResult.SUCCESS);
        event.setCanceled(true);
    }

    @SubscribeEvent
    public static void onLeftClickBlock(PlayerInteractEvent.LeftClickBlock event) {
        if (event.getAction() != PlayerInteractEvent.LeftClickBlock.Action.START
            || event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;

        ItemStack held = event.getItemStack();
        if (!held.is(Items.STICK) || !kind(held).equals("firework_wand")) return;
        // Cancel ordinary mining while the enchanted stick is used as a wand.
        event.setCanceled(true);
        if (!spendCharge(player, held, 10, FIREWORK_REGEN_SECONDS, "Firework Wand")) return;
        launchFireworks(level, event.getPos());
    }

    private static void enchantStick(ServerPlayer player, ItemStack grimoire, String kind) {
        int slot = -1;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            ItemStack candidate = player.getInventory().getItem(i);
            if (candidate.is(Items.STICK) && kind(candidate).isEmpty()) {
                slot = i;
                break;
            }
        }
        if (slot < 0) {
            player.displayClientMessage(Component.literal("Carry an ordinary stick to enchant it."), true);
            return;
        }
        boolean fireworks = kind.equals("firework_grimoire");
        String name = fireworks ? "Firework Wand" : "Rain Wand";
        String wandKind = fireworks ? "firework_wand" : "rain_wand";
        int capacity = fireworks ? 10 : 1;
        long interval = fireworks ? FIREWORK_REGEN_SECONDS : RAIN_REGEN_SECONDS;

        ItemStack wand = new ItemStack(Items.STICK);
        wand.set(DataComponents.ITEM_NAME, Component.literal(name).withStyle(ChatFormatting.LIGHT_PURPLE));
        wand.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        wand.set(DataComponents.MAX_STACK_SIZE, 1);
        CompoundTag data = new CompoundTag();
        data.putString(MARKER, wandKind);
        data.putInt("charges", capacity);
        data.putLong("recharge_epoch", Instant.now().getEpochSecond());
        wand.set(DataComponents.CUSTOM_DATA, CustomData.of(data));
        refreshLore(wand, name, capacity, capacity, interval);

        player.getInventory().getItem(slot).shrink(1);
        grimoire.shrink(1);
        if (!player.getInventory().add(wand)) player.drop(wand, false);
        player.containerMenu.broadcastChanges();
        player.displayClientMessage(Component.literal(name + " created!"), true);
    }

    private static String kind(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString(MARKER);
    }

    /**
     * Replenish charge buckets lazily when the item is used, including offline time.
     * When full, a newly spent charge starts a new interval at the current instant.
     */
    private static boolean spendCharge(ServerPlayer player, ItemStack wand,
                                       int capacity, long interval, String display) {
        CustomData custom = wand.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return false;
        CompoundTag tag = custom.copyTag();
        long now = Instant.now().getEpochSecond();
        int charges = Math.max(0, Math.min(capacity, tag.getInt("charges")));
        long anchor = tag.getLong("recharge_epoch");
        if (anchor <= 0 || anchor > now) anchor = now;

        if (charges < capacity) {
            long regained = (now - anchor) / interval;
            if (regained > 0) {
                charges = (int) Math.min(capacity, charges + regained);
                anchor = charges == capacity ? now : anchor + regained * interval;
            }
        }
        if (charges == 0) {
            long remain = Math.max(1, interval - (now - anchor));
            saveCharges(wand, tag, 0, anchor, display, capacity, interval);
            player.displayClientMessage(Component.literal(
                display + " is empty. Next charge in " + remain + " seconds."), true);
            return false;
        }
        if (charges == capacity) anchor = now;
        charges--;
        saveCharges(wand, tag, charges, anchor, display, capacity, interval);
        player.displayClientMessage(Component.literal(
            display + ": " + charges + "/" + capacity + " charges remaining"), true);
        return true;
    }

    private static void saveCharges(ItemStack wand, CompoundTag tag, int charges, long anchor,
                                    String display, int capacity, long interval) {
        tag.putInt("charges", charges);
        tag.putLong("recharge_epoch", anchor);
        wand.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        refreshLore(wand, display, charges, capacity, interval);
    }

    private static void refreshLore(ItemStack wand, String display, int charges, int capacity, long interval) {
        String recharge = interval == RAIN_REGEN_SECONDS ? "24 real hours" : "10 real minutes";
        String use = display.equals("Firework Wand") ? "Left-click a block for 10 fireworks" : "Right-click to summon 10 minutes of rain";
        wand.set(DataComponents.LORE, new ItemLore(List.of(
            Component.literal(use).withStyle(ChatFormatting.GRAY),
            Component.literal("Charges: " + charges + "/" + capacity).withStyle(ChatFormatting.AQUA),
            Component.literal("Regenerates 1 charge every " + recharge).withStyle(ChatFormatting.GRAY)
        )));
    }

    private static void launchFireworks(ServerLevel level, BlockPos target) {
        ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
        FireworkExplosion burst = new FireworkExplosion(
            FireworkExplosion.Shape.STAR, IntList.of(0xFF55CC, 0x55DDFF, 0xFFDD55),
            IntList.of(0xFFFFFF), true, true);
        rocket.set(DataComponents.FIREWORKS, new Fireworks(1, List.of(burst)));
        for (int i = 0; i < 10; i++) {
            double x = target.getX() + 0.5 + (level.random.nextDouble() - 0.5) * 3.0;
            double y = target.getY() + 1.5;
            double z = target.getZ() + 0.5 + (level.random.nextDouble() - 0.5) * 3.0;
            level.addFreshEntity(new FireworkRocketEntity(level, x, y, z, rocket));
        }
    }
}
