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
    private static final int WINDUP_TICKS = 200; // Ten-second cinematic lock, charge, and descent.
    private static final int MAX_ACTIVE_STRIKES = 8;
    private static final List<Strike> active = new ArrayList<>();
    private static MinecraftServer currentServer;

    private static final class Strike {
        final ServerLevel level;
        final BlockPos target;
        final BlockState originalState;
        final UUID shooter;
        final long impactTick;
        final long startTick;

        Strike(ServerLevel level, BlockPos target, BlockState state, UUID shooter) {
            this.level = level;
            this.target = target.immutable();
            this.originalState = state;
            this.shooter = shooter;
            this.startTick = level.getGameTime();
            this.impactTick = startTick + WINDUP_TICKS;
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
            return;
        }
        for (Strike strike : active) {
            if (strike.shooter.equals(shooter.getUUID())) {
                return;
            }
        }

        HitResult trace = shooter.pick(RANGE, 0.0F, false);
        if (!(trace instanceof BlockHitResult target) || trace.getType() != HitResult.Type.BLOCK) {
            return;
        }
        BlockPos pos = target.getBlockPos();
        if (!allowed(level, shooter, pos)) {
            return;
        }

        CustomData existing = gun.get(DataComponents.CUSTOM_DATA);
        if (existing == null) return;
        CompoundTag tag = existing.copyTag();
        long now = Instant.now().getEpochSecond();
        long ready = tag.getLong("orbital_ready_epoch");
        if (ready > now) {
            return;
        }
        tag.putLong("orbital_ready_epoch", now + RECHARGE_SECONDS);
        gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        active.add(new Strike(level, pos, level.getBlockState(pos), shooter.getUUID()));
        level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1.2F, 0.55F);
        level.sendParticles(ParticleTypes.FLASH, pos.getX()+0.5, pos.getY()+1.3, pos.getZ()+0.5,
            4, 0.1, 0.2, 0.1, 0);
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
                renderCharge(strike);
                continue;
            }
            iterator.remove();
            ServerPlayer shooter = server.getPlayerList().getPlayer(strike.shooter);
            if (shooter == null || shooter.level() != level ||
                !allowed(level, shooter, strike.target) ||
                !level.getBlockState(strike.target).equals(strike.originalState)) {
                continue;
            }

            // No explosion, fire, entity damage or loot. Just one block is removed.
            boolean destroyed = level.destroyBlock(strike.target, false, shooter);
            if (destroyed) {
                renderImpact(strike);
            }
        }
    }
    /**
     * Purely cosmetic orbital strike: no explosions, projectile damage, fire, block
     * updates, forced chunk loads or client-side mod requirements. A ten-second
     * sequence with a rotating targeting reticle, growing electrical charge,
     * vertical sky beam and descending projectile. The impact destroys one block.
     */
    private static void renderCharge(Strike strike) {
        ServerLevel level = strike.level;
        int age = (int) (level.getGameTime() - strike.startTick);
        double x = strike.target.getX() + 0.5;
        double y = strike.target.getY() + 0.55;
        double z = strike.target.getZ() + 0.5;
        double sky = Math.min(level.getMaxBuildHeight() - 3, y + 80);
        double phase = age * 0.075;

        // Rotating double-ring reticle: visible for the entire lock-on.
        for (int i = 0; i < 16; i++) {
            double angle = Math.PI * 2 * i / 16 + phase;
            double outer = 2.6 + 0.28 * Math.sin(age * 0.09);
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK,
                x + Math.cos(angle) * outer, y + 0.12,
                z + Math.sin(angle) * outer, 1, 0, 0, 0, 0);
            if (i % 2 == 0) {
                double innerAngle = -angle;
                level.sendParticles(ParticleTypes.END_ROD,
                    x + Math.cos(innerAngle) * 1.25, y + 0.35,
                    z + Math.sin(innerAngle) * 1.25, 1, 0, 0, 0, 0);
            }
        }

        // Acquisition (0-3s): pulses and distant beacon hum.
        if (age < 60) {
            if (age % 12 == 0) {
                level.sendParticles(ParticleTypes.FLASH, x, y + 0.4, z,
                    1, 0, 0, 0, 0);
                level.playSound(null, strike.target, SoundEvents.BEACON_AMBIENT,
                    SoundSource.BLOCKS, 1.1F, 0.55F + age / 220.0F);
            }
            return;
        }

        // Charging (3-7s): thickening sky-to-ground column and crackling.
        if (age < 140) {
            double strength = (age - 60) / 80.0;
            for (int i = 0; i < 24; i++) {
                double h = y + (sky - y) * i / 23.0;
                double wobble = 0.10 + 0.30 * (1.0 - strength);
                double angle = phase * 2 + i * 2.39996;
                level.sendParticles(ParticleTypes.END_ROD,
                    x + Math.cos(angle) * wobble, h,
                    z + Math.sin(angle) * wobble, 1, 0, 0, 0, 0);
            }
            if (age % 8 == 0) {
                level.sendParticles(ParticleTypes.ELECTRIC_SPARK, x, y + 1, z,
                    20, 1.4, 1.1, 1.4, 0.06);
                level.playSound(null, strike.target, SoundEvents.RESPAWN_ANCHOR_CHARGE,
                    SoundSource.BLOCKS, 1.2F, 0.65F + (float) strength * 0.7F);
            }
            return;
        }

        // Final three seconds: brilliant projectile descends from the sky.
        double descent = (age - 140) / 60.0;
        double head = sky - (sky - y) * descent * descent;
        for (int i = 0; i < 22; i++) {
            double h = y + (sky - y) * i / 21.0;
            level.sendParticles(ParticleTypes.END_ROD, x, h, z,
                1, 0.06, 0.06, 0.06, 0);
        }
        level.sendParticles(ParticleTypes.FLASH, x, head, z, 1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, x, head, z,
            18, 0.45, 0.7, 0.45, 0.07);
        level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, x, head, z,
            10, 0.25, 0.6, 0.25, 0.015);
        if (age % 10 == 0) {
            level.playSound(null, strike.target, SoundEvents.BEACON_ACTIVATE,
                SoundSource.BLOCKS, 1.3F, 0.75F + (float) descent);
        }
        if (age >= 188) {
            level.sendParticles(ParticleTypes.ELECTRIC_SPARK, x, y + 0.6, z,
                35, 2.2, 0.6, 2.2, 0.1);
        }
    }

    private static void renderImpact(Strike strike) {
        ServerLevel level = strike.level;
        BlockPos pos = strike.target;
        double x = pos.getX() + 0.5;
        double y = pos.getY() + 0.5;
        double z = pos.getZ() + 0.5;
        // Huge *visual* detonation; no Minecraft explosion entity is spawned.
        level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, x, y, z,
            1, 0, 0, 0, 0);
        level.sendParticles(ParticleTypes.FLASH, x, y, z,
            4, 0.4, 0.4, 0.4, 0);
        level.sendParticles(ParticleTypes.ELECTRIC_SPARK, x, y, z,
            170, 3.5, 2.0, 3.5, 0.12);
        level.sendParticles(ParticleTypes.END_ROD, x, y, z,
            90, 3.0, 3.0, 3.0, 0.09);
        level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, x, y, z,
            50, 2.0, 1.0, 2.0, 0.05);
        level.playSound(null, pos, SoundEvents.LIGHTNING_BOLT_THUNDER,
            SoundSource.BLOCKS, 2.0F, 0.75F);
        level.playSound(null, pos, SoundEvents.GENERIC_EXPLODE.value(),
            SoundSource.BLOCKS, 2.0F, 0.7F);
    }

}
