package dev.cybersans.brainmeth;

import it.unimi.dsi.fastutil.ints.IntList;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
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
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.time.Instant;
import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;

/**
 * Bounty-only magic using tagged vanilla items. No client mod or recipes required.
 * Only the server changes charge counts, and every clock is a wall-clock epoch.
 * The existing launch scheduler is intentionally independent of this class.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethRewards {
    private static final String MARKER = "brainmeth_reward";
    private static final long FIREWORK_REGEN_SECONDS = 10 * 60;
    private static final int FIREWORK_CAPACITY = 6;
    private static final int FIREWORKS_PER_USE = 20;
    private static final int FIREWORKS_PER_WAVE = 5;
    private static final int MAX_ACTIVE_FIREWORK_VOLLEYS = 12;
    private static final long RAIN_REGEN_SECONDS = 24 * 60 * 60;
    private static final long LEVITATION_REGEN_SECONDS = 60 * 60;
    private static final long HEALING_REGEN_SECONDS = 60 * 60;
    private static final long LIGHTNING_REGEN_SECONDS = 3 * 60 * 60;
    private static final long LEVITATION_DURATION_SECONDS = 10 * 60;
    private static final double HOVER_HEIGHT_BLOCKS = 5.0;
    private static final double HOVER_HORIZONTAL_BOOST = 1.6;
    private static final double HOVER_MAX_HORIZONTAL_SPEED = 0.38;
    private static final String HOVER_END_KEY = "brainmeth_hover_end_epoch";
    private static final int HEAL_RADIUS_BLOCKS = 8 * 16;
    private static MinecraftServer queuedServer;
    private static final List<PendingLightning> lightningQueue = new ArrayList<>();
    private static final List<PendingFireworks> fireworkQueue = new ArrayList<>();

    private static final class PendingLightning {
        final ServerLevel level;
        final BlockPos pos;
        int remaining = 6;
        long nextTick;

        PendingLightning(ServerLevel level, BlockPos pos) {
            this.level = level;
            this.pos = pos;
            this.nextTick = level.getGameTime();
        }
    }

    private static final class PendingFireworks {
        final ServerLevel level;
        final BlockPos pos;
        int remaining = FIREWORKS_PER_USE;
        long nextTick;

        PendingFireworks(ServerLevel level, BlockPos pos) {
            this.level = level;
            this.pos = pos;
            this.nextTick = level.getGameTime();
        }
    }

    private BrainmethRewards() {}

    @SubscribeEvent
    public static void onRightClickItem(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;

        ItemStack held = event.getItemStack();
        String kind = kind(held);
        switch (kind) {
            case "firework_grimoire", "rain_grimoire", "levitation_grimoire", "healing_grimoire", "lightning_grimoire" -> {
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
            case "levitation_wand" -> {
                if (held.is(Items.STICK)) {
                    long now = Instant.now().getEpochSecond();
                    long previousEnd = player.getPersistentData().getLong(HOVER_END_KEY);
                    if (previousEnd > now) {
                        player.displayClientMessage(Component.literal("Already floating."), true);
                    } else if (spendCharge(player, held, 3, LEVITATION_REGEN_SECONDS, "Levitation Wand")) {
                        player.getPersistentData().putLong(HOVER_END_KEY, now + LEVITATION_DURATION_SECONDS);
                        player.displayClientMessage(Component.literal("You hover five blocks above the ground for 10 minutes."), true);
                    }
                }
            }
            case "healing_wand" -> {
                if (held.is(Items.STICK) && spendCharge(player, held, 1, HEALING_REGEN_SECONDS, "Healing Wand")) {
                    int healed = healNearby(level, player);
                    player.displayClientMessage(Component.literal("Fully healed " + healed + " nearby player(s)."), true);
                }
            }
            case "lightning_wand" -> {
                if (held.is(Items.STICK)) {
                    HitResult hit = player.pick(64.0, 0.0F, false);
                    if (!(hit instanceof BlockHitResult target) || hit.getType() != HitResult.Type.BLOCK) {
                        player.displayClientMessage(Component.literal("Look at a block within 64 blocks."), true);
                    } else if (lightningQueue.size() >= 8) {
                        player.displayClientMessage(Component.literal("Too many lightning volleys active; try again."), true);
                    } else if (spendCharge(player, held, 3, LIGHTNING_REGEN_SECONDS, "Lightning Wand")) {
                        lightningQueue.add(new PendingLightning(level, target.getBlockPos().above()));
                        player.displayClientMessage(Component.literal("Six lightning strikes incoming!"), true);
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
        if (fireworkQueue.size() >= MAX_ACTIVE_FIREWORK_VOLLEYS) {
            player.displayClientMessage(Component.literal("Too many firework volleys active; try again."), true);
            return;
        }
        if (!spendCharge(player, held, FIREWORK_CAPACITY, FIREWORK_REGEN_SECONDS, "Firework Wand")) return;
        fireworkQueue.add(new PendingFireworks(level, event.getPos()));
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
        final String name, wandKind;
        final int capacity;
        final long interval;
        switch (kind) {
            case "firework_grimoire" -> {
                name = "Firework Wand"; wandKind = "firework_wand";
                capacity = FIREWORK_CAPACITY; interval = FIREWORK_REGEN_SECONDS;
            }
            case "rain_grimoire" -> {
                name = "Rain Wand"; wandKind = "rain_wand";
                capacity = 1; interval = RAIN_REGEN_SECONDS;
            }
            case "levitation_grimoire" -> {
                name = "Levitation Wand"; wandKind = "levitation_wand";
                capacity = 3; interval = LEVITATION_REGEN_SECONDS;
            }
            case "healing_grimoire" -> {
                name = "Healing Wand"; wandKind = "healing_wand";
                capacity = 1; interval = HEALING_REGEN_SECONDS;
            }
            case "lightning_grimoire" -> {
                name = "Lightning Wand"; wandKind = "lightning_wand";
                capacity = 3; interval = LIGHTNING_REGEN_SECONDS;
            }
            default -> { return; }
        }

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
            saveCharges(wand, tag, 0, anchor, display, capacity, interval);
            player.displayClientMessage(Component.literal(
                display + ": No uses left."), true);
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
        String recharge = switch (display) {
            case "Firework Wand" -> "10 real minutes";
            case "Rain Wand" -> "24 real hours";
            case "Levitation Wand", "Healing Wand" -> "1 real hour";
            case "Lightning Wand" -> "3 real hours";
            default -> "unknown";
        };
        String use = switch (display) {
            case "Firework Wand" -> "Left-click a block for 20 fireworks";
            case "Rain Wand" -> "Right-click to summon 10 minutes of rain";
            case "Levitation Wand" -> "Right-click to hover 5 blocks above terrain for 10 minutes";
            case "Healing Wand" -> "Right-click to heal players within 8 chunks";
            case "Lightning Wand" -> "Right-click a targeted block for 6 lightning strikes";
            default -> "Unknown wand";
        };
        wand.set(DataComponents.LORE, new ItemLore(List.of(
            Component.literal(use).withStyle(ChatFormatting.GRAY),
            Component.literal("Charges: " + charges + "/" + capacity).withStyle(ChatFormatting.AQUA),
            Component.literal("Regenerates 1 charge every " + recharge).withStyle(ChatFormatting.GRAY)
        )));
    }

    private static void launchFireworks(ServerLevel level, BlockPos target, int count) {
        ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
        FireworkExplosion burst = new FireworkExplosion(
            FireworkExplosion.Shape.STAR, IntList.of(0xFF55CC, 0x55DDFF, 0xFFDD55),
            IntList.of(0xFFFFFF), true, true);
        rocket.set(DataComponents.FIREWORKS, new Fireworks(1, List.of(burst)));
        for (int i = 0; i < count; i++) {
            // Scatter each wave over an 8-block-wide area, rather than a 3-block clump.
            double x = target.getX() + 0.5 + (level.random.nextDouble() - 0.5) * 8.0;
            double y = target.getY() + 1.5 + level.random.nextDouble() * 1.5;
            double z = target.getZ() + 0.5 + (level.random.nextDouble() - 0.5) * 8.0;
            level.addFreshEntity(new FireworkRocketEntity(level, x, y, z, rocket));
        }
    }

    /** Eight chunks = 128 blocks, spherical range, same dimension only. */
    private static int healNearby(ServerLevel level, ServerPlayer caster) {
        int healed = 0;
        for (ServerPlayer target : level.getServer().getPlayerList().getPlayers()) {
            if (target.level() != level || !target.isAlive() || target.isSpectator()) continue;
            if (target.distanceToSqr(caster) <= HEAL_RADIUS_BLOCKS * HEAL_RADIUS_BLOCKS) {
                target.setHealth(target.getMaxHealth());
                healed++;
            }
        }
        return healed;
    }

    /** One durability point per successful hit with the tagged Knockback Stick. */
    @SubscribeEvent
    public static void onKnockbackHit(LivingDamageEvent.Post event) {
        if (!(event.getSource().getEntity() instanceof ServerPlayer attacker)) return;
        ItemStack weapon = attacker.getMainHandItem();
        if (weapon.is(Items.STICK) && kind(weapon).equals("knockback_stick")) {
            weapon.hurtAndBreak(1, attacker, EquipmentSlot.MAINHAND);
        }
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        if (queuedServer != server) {
            lightningQueue.clear();
            fireworkQueue.clear();
            queuedServer = server;
        }
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            long end = player.getPersistentData().getLong(HOVER_END_KEY);
            if (end == 0) continue;
            if (end <= Instant.now().getEpochSecond() || !player.isAlive()) {
                player.getPersistentData().remove(HOVER_END_KEY);
                continue;
            }
            hoverAboveTerrain(player);
        }
        Iterator<PendingLightning> it = lightningQueue.iterator();
        while (it.hasNext()) {
            PendingLightning pending = it.next();
            if (pending.level.getGameTime() < pending.nextTick) continue;
            LightningBolt bolt = EntityType.LIGHTNING_BOLT.create(pending.level);
            if (bolt != null) {
                bolt.moveTo(pending.pos.getX() + 0.5, pending.pos.getY(),
                            pending.pos.getZ() + 0.5);
                pending.level.addFreshEntity(bolt);
            }
            pending.remaining--;
            pending.nextTick = pending.level.getGameTime() + 8; // visibly separated strikes
            if (pending.remaining == 0) it.remove();
        }
        // Four waves of five fireworks, separated by 4 ticks (~0.2 seconds).
        Iterator<PendingFireworks> fireworks = fireworkQueue.iterator();
        while (fireworks.hasNext()) {
            PendingFireworks pending = fireworks.next();
            if (pending.level.getGameTime() < pending.nextTick) continue;
            int count = Math.min(FIREWORKS_PER_WAVE, pending.remaining);
            launchFireworks(pending.level, pending.pos, count);
            pending.remaining -= count;
            pending.nextTick = pending.level.getGameTime() + 4;
            if (pending.remaining == 0) fireworks.remove();
        }
    }

    /** Avoid allowing free flight: follow the collision surface five blocks below the feet.
     *  Keep the player's horizontal velocity and respect normal collision checks.
     *  No persistent no-gravity flag is set, so logout or expiry cannot strand a player.
     */
    private static void hoverAboveTerrain(ServerPlayer player) {
        if (player.isPassenger() || player.isFallFlying() || player.isSpectator()
            || player.getAbilities().flying) return;
        ServerLevel level = player.serverLevel();
        Vec3 from = player.position().add(0.0, 0.25, 0.0);
        Vec3 to = from.add(0.0, -12.0, 0.0);
        BlockHitResult ground = level.clip(new ClipContext(
            from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY, player));
        Vec3 motion = player.getDeltaMovement();
        double vertical;
        if (ground.getType() == HitResult.Type.BLOCK) {
            double desiredY = ground.getLocation().y + HOVER_HEIGHT_BLOCKS;
            double error = desiredY - player.getY();
            vertical = Math.max(-0.26, Math.min(0.26, error * 0.26 + 0.0784));
        } else {
            // Over deep drops, descend slowly until solid ground is located.
            vertical = -0.10;
        }
        // Air movement is naturally sluggish; amplify horizontal input but cap speed.
        double horizontalX = motion.x * HOVER_HORIZONTAL_BOOST;
        double horizontalZ = motion.z * HOVER_HORIZONTAL_BOOST;
        double horizontalSpeed = Math.hypot(horizontalX, horizontalZ);
        if (horizontalSpeed > HOVER_MAX_HORIZONTAL_SPEED) {
            double scale = HOVER_MAX_HORIZONTAL_SPEED / horizontalSpeed;
            horizontalX *= scale;
            horizontalZ *= scale;
        }
        player.setDeltaMovement(horizontalX, vertical, horizontalZ);
        player.fallDistance = 0.0F;
        player.hurtMarked = true;
    }
}
