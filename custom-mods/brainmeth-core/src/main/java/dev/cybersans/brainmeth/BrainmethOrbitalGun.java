package dev.cybersans.brainmeth;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;

/**
 * The Orbital Strike Gun is deliberately an elaborate animation that destroys
 * precisely one ordinary block. Uses existing vanilla particles and sounds,
 * so no client assets or orbital-strike mod is required.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethOrbitalGun {
    private static final String KIND = "orbital_strike_gun";
    private static final long RECHARGE_SECONDS = 10 * 60;
    private static final int RANGE = 128;
    private static final int WINDUP_TICKS = 45;
    private static final int MAX_ACTIVE_STRIKES = 8;
    private static final List<Strike> active = new ArrayList<>();
    private static MinecraftServer currentServer;

    private static final class Strike {
        final ServerLevel level;
        final BlockPos target;
        final BlockState originalState;
        final UUID shooter;
        final long impactTick;

        Strike(ServerLevel level, BlockPos target, BlockState state, UUID shooter) {
            this.level = level;
            this.target = target.immutable();
            this.originalState = state;
            this.shooter = shooter;
            this.impactTick = level.getGameTime() + WINDUP_TICKS;
        }
    }

    private BrainmethOrbitalGun() {}

    private static boolean isGun(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return stack.is(Items.CROSSBOW) && data != null
            && KIND.equals(data.copyTag().getString("brainmeth_reward"));
    }

    @SubscribeEvent
    public static void onRightClickItem(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)
            || !isGun(event.getItemStack())) return;
        fire(player, level, event.getItemStack());
        event.setCancellationResult(InteractionResult.SUCCESS);
        event.setCanceled(true);
    }

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)
            || !isGun(event.getItemStack())) return;
        fire(player, level, event.getItemStack());
        event.setCancellationResult(InteractionResult.SUCCESS);
        event.setCanceled(true);
    }

    private static void fire(ServerPlayer shooter, ServerLevel level, ItemStack gun) {
        if (currentServer != level.getServer()) {
            active.clear();
            currentServer = level.getServer();
        }
        if (active.size() >= MAX_ACTIVE_STRIKES) {
            message(shooter, "Orbital network busy; try again.");
            return;
        }
        for (Strike strike : active) {
            if (strike.shooter.equals(shooter.getUUID())) {
                message(shooter, "Your orbital strike is still locking on.");
                return;
            }
        }

        HitResult trace = shooter.pick(RANGE, 0.0F, false);
        if (!(trace instanceof BlockHitResult target) || trace.getType() != HitResult.Type.BLOCK) {
            message(shooter, "Aim at a block no farther than 128 blocks.");
            return;
        }
        BlockPos pos = target.getBlockPos();
        if (!allowed(level, shooter, pos)) {
            message(shooter, "No lock: protected, indestructible, or container block.");
            return;
        }

        CustomData existing = gun.get(DataComponents.CUSTOM_DATA);
        if (existing == null) return;
        CompoundTag tag = existing.copyTag();
        long now = Instant.now().getEpochSecond();
        long ready = tag.getLong("orbital_ready_epoch");
        if (ready > now) {
            message(shooter, "Orbit recharging: " + (ready - now) + " seconds remaining.");
            return;
        }
        tag.putLong("orbital_ready_epoch", now + RECHARGE_SECONDS);
        gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        active.add(new Strike(level, pos, level.getBlockState(pos), shooter.getUUID()));
        level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.2F, 0.55F);
        level.sendParticles(ParticleTypes.FLASH, pos.getX()+0.5, pos.getY()+1.3, pos.getZ()+0.5,
            4, 0.1, 0.2, 0.1, 0);
        message(shooter, "ORBITAL STRIKE LOCKED. Calculating one (1) block...");
    }

    private static void message(ServerPlayer player, String message) {
        player.displayClientMessage(Component.literal(message), true);
    }

    private static boolean allowed(ServerLevel level, ServerPlayer shooter, BlockPos pos) {
        if (!level.hasChunkAt(pos) || !level.getWorldBorder().isWithinBounds(pos)) return false;
        if (!level.mayInteract(shooter, pos)
            || !shooter.mayUseItemAt(pos, Direction.UP, shooter.getMainHandItem())) return false;
        BlockState state = level.getBlockState(pos);
        if (state.isAir() || !state.getFluidState().isEmpty()
            || state.hasBlockEntity() || state.getDestroySpeed(level, pos) < 0) return false;
        // Prevent destroying blocks involved in inventories or machines.
        BlockEntity entity = level.getBlockEntity(pos);
        return entity == null;
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        if (currentServer != server) {
            active.clear();
            currentServer = server;
        }
        Iterator<Strike> iterator = active.iterator();
        while (iterator.hasNext()) {
            Strike strike = iterator.next();
            ServerLevel level = strike.level;
            if (level.getGameTime() < strike.impactTick) {
                if (!level.hasChunkAt(strike.target)) {
                    iterator.remove(); // Never force-load chunks.
                    continue;
                }
                // Visible pillar descending from the sky while the satellite targets.
                double x = strike.target.getX() + 0.5;
                double z = strike.target.getZ() + 0.5;
                double foot = strike.target.getY() + 0.75;
                double top = Math.min(level.getMaxBuildHeight() - 4, foot + 96);
                for (int i = 0; i <= 16; i++) {
                    double y = foot + (top - foot) * i / 16.0;
                    level.sendParticles(ParticleTypes.END_ROD, x, y, z,
                        1, 0.09, 0.30, 0.09, 0.01);
                }
                if (level.getGameTime() % 10 == 0)
                    level.playSound(null, strike.target, SoundEvents.BEACON_AMBIENT,
                        SoundSource.BLOCKS, 0.45F, 0.55F);
                continue;
            }
            iterator.remove();
            ServerPlayer shooter = server.getPlayerList().getPlayer(strike.shooter);
            if (shooter == null || shooter.level() != level ||
                !allowed(level, shooter, strike.target) ||
                !level.getBlockState(strike.target).equals(strike.originalState)) {
                if (shooter != null) message(shooter, "Satellite aborted: the target changed or is now unsafe.");
                continue;
            }

            // No explosion, fire, entity damage or loot. Just one block is removed.
            boolean destroyed = level.destroyBlock(strike.target, false, shooter);
            if (destroyed) {
                level.sendParticles(ParticleTypes.FLASH, strike.target.getX()+0.5,
                    strike.target.getY()+0.5, strike.target.getZ()+0.5,
                    3, 0.1, 0.1, 0.1, 0);
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, strike.target.getX()+0.5,
                    strike.target.getY()+0.5, strike.target.getZ()+0.5,
                    120, 0.7, 1.0, 0.7, 0.08);
                level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, strike.target.getX()+0.5,
                    strike.target.getY()+0.6, strike.target.getZ()+0.5,
                    15, 0.4, 0.4, 0.4, 0.03);
                level.playSound(null, strike.target, SoundEvents.LIGHTNING_BOLT_THUNDER,
                    SoundSource.BLOCKS, 1.0F, 1.35F);
                message(shooter, "Direct orbital hit. Exactly one block has been eliminated.");
            } else {
                message(shooter, "The orbital strike fizzled. No block was removed.");
            }
        }
    }
}
