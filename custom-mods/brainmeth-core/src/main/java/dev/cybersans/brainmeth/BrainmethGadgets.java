package dev.cybersans.brainmeth;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.boss.EnderDragonPart;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.AnvilUpdateEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.ProjectileImpactEvent;
import net.neoforged.neoforge.event.entity.player.AttackEntityEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

/** Bounty-only gadgets using server-verified vanilla items. No client install. */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethGadgets {
    private static final String MARKER = "brainmeth_reward";
    private static final String CROUCH_UNTIL = "brainmeth_naughty_crouch_until";
    private static final String WAS_FORCED = "brainmeth_naughty_was_forced";
    private static final long SHOVEL_REGEN = 6 * 3600L;
    private static final long STAFF_REGEN = 20 * 60L;
    private static final long WATCH_COOLDOWN = 6 * 3600L;
    private static final int HISTORY_SIZE = 400;
    private static final long HISTORY_LOOKBACK_MS = 15000L;
    private static final Map<UUID, ArrayDeque<Snapshot>> history = new HashMap<>();
    private static MinecraftServer activeServer;

    private record Snapshot(long ms, ServerLevel level, Vec3 pos, float yaw, float pitch) {}
    private BrainmethGadgets() {}

    private static long now() { return Instant.now().getEpochSecond(); }
    private static String kind(ItemStack item) {
        CustomData data = item.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString(MARKER);
    }

    /** Real-time charge restoration per item, including while offline. */
    private static boolean takeCharge(ServerPlayer actor, ItemStack item, int capacity,
                                      long recharge, String label) {
        CustomData custom = item.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return false;
        CompoundTag data = custom.copyTag();
        long instant = now();
        int charges = data.contains("charges") ? data.getInt("charges") : capacity;
        charges = Math.max(0, Math.min(capacity, charges));
        long anchor = data.getLong("charge_anchor");
        if (anchor <= 0 || anchor > instant) anchor = instant;
        if (charges < capacity) {
            long gained = (instant - anchor) / recharge;
            if (gained > 0) {
                charges = (int) Math.min(capacity, charges + gained);
                anchor = charges == capacity ? instant : anchor + gained * recharge;
            }
        }
        if (charges == 0) {
            actor.displayClientMessage(Component.literal(label + " is recharging: "
                + Math.max(1, recharge - (instant - anchor)) + " seconds to next charge."), true);
            return false;
        }
        if (charges == capacity) anchor = instant;
        data.putInt("charges", charges - 1);
        data.putLong("charge_anchor", anchor);
        item.set(DataComponents.CUSTOM_DATA, CustomData.of(data));
        actor.displayClientMessage(Component.literal(label + " | "
            + (charges - 1) + "/" + capacity + " charges"), true);
        return true;
    }

    @SubscribeEvent
    public static void onAttack(AttackEntityEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer actor) ||
            !(event.getTarget() instanceof ServerPlayer victim)) return;
        ItemStack item = actor.getMainHandItem();
        if (!item.is(Items.IRON_SHOVEL) || !kind(item).equals("naughty_shovel")) return;
        if (!actor.serverLevel().getServer().isPvpAllowed()) return;
        if (!takeCharge(actor, item, 2, SHOVEL_REGEN, "Naughty Shovel")) return;
        victim.getPersistentData().putLong(CROUCH_UNTIL, now() + 20);
        victim.getPersistentData().putBoolean(WAS_FORCED, true);
        victim.displayClientMessage(Component.literal("Naughty Shovel: crouch for 20 seconds!"), true);
    }

    @SubscribeEvent
    public static void onEntityInteract(PlayerInteractEvent.EntityInteract event) {
        if (event.getHand() != InteractionHand.MAIN_HAND ||
            !(event.getEntity() instanceof ServerPlayer actor) ||
            !(event.getTarget() instanceof ServerPlayer target)) return;
        ItemStack item = event.getItemStack();
        if (!item.is(Items.STICK) || !kind(item).equals("mild_inconvenience_staff")) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        if (!takeCharge(actor, item, 3, STAFF_REGEN, "Staff of Mild Inconvenience")) return;
        target.teleportTo(target.serverLevel(), target.getX(), target.getY(), target.getZ(),
            target.getYRot() + 180.0F, target.getXRot());
        target.displayClientMessage(Component.literal("You have been mildly inconvenienced."), true);
    }

    @SubscribeEvent
    public static void onWatch(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND ||
            !(event.getEntity() instanceof ServerPlayer actor)) return;
        ItemStack item = event.getItemStack();
        if (!item.is(Items.CLOCK) || !kind(item).equals("time_traveller_watch")) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        ArrayDeque<Snapshot> snapshots = history.get(actor.getUUID());
        if (snapshots == null) {
            actor.displayClientMessage(Component.literal("No history yet. Stay online for 15 seconds."), true);
            return;
        }
        long targetTime = System.currentTimeMillis() - HISTORY_LOOKBACK_MS;
        Snapshot chosen = null;
        for (Snapshot s : snapshots) {
            if (s.ms <= targetTime) chosen = s; else break;
        }
        if (chosen == null) {
            actor.displayClientMessage(Component.literal("The watch needs 15 seconds of history."), true);
            return;
        }
        ServerLevel dest = chosen.level();
        Vec3 pos = chosen.pos();
        BlockPos block = BlockPos.containing(pos);
        if (dest.getServer() != actor.serverLevel().getServer() ||
            !dest.hasChunkAt(block) || !dest.getWorldBorder().isWithinBounds(block) ||
            !dest.getBlockState(block).getFluidState().isEmpty() ||
            !dest.getBlockState(block.above()).getFluidState().isEmpty()) {
            actor.displayClientMessage(Component.literal("Past destination unavailable or unsafe; no charge used."), true);
            return;
        }
        AABB bounds = actor.getBoundingBox().move(pos.subtract(actor.position()));
        if (!dest.noCollision(actor, bounds)) {
            actor.displayClientMessage(Component.literal("Your past position is obstructed; no charge used."), true);
            return;
        }
        if (!takeCharge(actor, item, 1, WATCH_COOLDOWN, "Pocket Watch")) return;
        actor.teleportTo(dest, pos.x, pos.y, pos.z, chosen.yaw(), chosen.pitch());
        actor.fallDistance = 0.0F;
        actor.displayClientMessage(Component.literal("Returned to where you were 15 seconds ago."), true);
    }

    @SubscribeEvent
    public static void onArrowSpawn(EntityJoinLevelEvent event) {
        if (!(event.getLevel() instanceof ServerLevel) ||
            !(event.getEntity() instanceof AbstractArrow arrow) ||
            !(arrow.getOwner() instanceof ServerPlayer archer)) return;
        if (kind(archer.getMainHandItem()).equals("summoning_bow") ||
            kind(archer.getOffhandItem()).equals("summoning_bow")) {
            arrow.getPersistentData().putBoolean("brainmeth_summon_arrow", true);
        }
    }

    @SubscribeEvent
    public static void onArrowHit(ProjectileImpactEvent event) {
        if (!(event.getProjectile() instanceof AbstractArrow arrow) ||
            !arrow.getPersistentData().getBoolean("brainmeth_summon_arrow") ||
            !(event.getRayTraceResult() instanceof EntityHitResult hit) ||
            !(arrow.getOwner() instanceof ServerPlayer archer) ||
            !(arrow.level() instanceof ServerLevel level)) return;
        Entity victim = hit.getEntity();
        if (victim instanceof EnderDragon || victim instanceof EnderDragonPart ||
            victim instanceof WitherBoss || !victim.isAlive() || victim == archer ||
            victim.level() != archer.level() ||
            (victim instanceof ServerPlayer && !level.getServer().isPvpAllowed())) return;
        BlockPos destination = archer.blockPosition();
        if (!level.hasChunkAt(destination) || !level.getWorldBorder().isWithinBounds(destination)) return;
        if (!level.noCollision(victim, victim.getBoundingBox().move(archer.position().subtract(victim.position())))) return;
        event.setCanceled(true);
        victim.teleportTo(archer.getX(), archer.getY(), archer.getZ());
        victim.fallDistance = 0.0F;
        arrow.discard();
    }

    /** Prevent repair and enchanted book upgrades at the anvil. */
    @SubscribeEvent
    public static void onAnvil(AnvilUpdateEvent event) {
        if (kind(event.getLeft()).equals("summoning_bow")) {
            event.setOutput(ItemStack.EMPTY);
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        if (activeServer != server) {
            history.clear();
            activeServer = server;
        }
        long nowMs = System.currentTimeMillis();
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            ArrayDeque<Snapshot> snapshots = history.computeIfAbsent(player.getUUID(), k -> new ArrayDeque<>());
            snapshots.addLast(new Snapshot(nowMs, player.serverLevel(), player.position(),
                player.getYRot(), player.getXRot()));
            while (snapshots.size() > HISTORY_SIZE || (!snapshots.isEmpty()
                    && snapshots.peekFirst().ms < nowMs - 21000L)) snapshots.removeFirst();

            CompoundTag data = player.getPersistentData();
            if (data.getLong(CROUCH_UNTIL) > now()) {
                player.setShiftKeyDown(true);
                player.setPose(Pose.CROUCHING);
            } else if (data.getBoolean(WAS_FORCED)) {
                data.remove(CROUCH_UNTIL);
                data.remove(WAS_FORCED);
                player.setShiftKeyDown(false);
            }

            // Make a custom summoning bow finite durability even when enchanted with Mending.
            for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
                ItemStack held = player.getInventory().getItem(i);
                if (!held.is(Items.BOW) || !kind(held).equals("summoning_bow")) continue;
                int damage = held.getDamageValue();
                CustomData cd = held.get(DataComponents.CUSTOM_DATA);
                CompoundTag tag = cd == null ? new CompoundTag() : cd.copyTag();
                int highest = tag.getInt("max_observed_damage");
                if (damage < highest) held.setDamageValue(highest);
                else if (damage > highest) {
                    tag.putInt("max_observed_damage", damage);
                    held.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
                }
            }
        }
        Iterator<UUID> keys = history.keySet().iterator();
        while (keys.hasNext()) {
            if (server.getPlayerList().getPlayer(keys.next()) == null) keys.remove();
        }
    }
}
