#!/usr/bin/env python3
"""Build a safety-patched Orbital Railgun: Renewed (MIT) for Brainmeth.

Upstream: https://github.com/Rayness/orbital-railgun-renewed
Pinned revision: 1.21.1 @ 76e3379fe14f44e2738e50674440e59797fa809f
Credits: Mishkis (original), Rayness (NeoForge port).
No unmodified upstream strike is ever deployed. The upstream crater code is
REPLACED, not configured, and the server validates every shot.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

UPSTREAM = "https://github.com/Rayness/orbital-railgun-renewed.git"
PIN = "76e3379fe14f44e2738e50674440e59797fa809f"
SOURCE = "src/main/java/io/github/mishkis/orbital_railgun/"
MANAGER = r"""package io.github.mishkis.orbital_railgun.util;

import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Iterator;
import java.util.Queue;
import java.util.UUID;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * Brainmeth precision-only replacement for the upstream crater and damage
 * engine. Keeps the upstream shaders, sounds, networking and 35-second windup.
 * Never explodes, damages entities, force-loads chunks or changes other blocks.
 */
public final class OrbitalRailgunStrikeManager {
    public record Strike(BlockPos pos, BlockState originalState, UUID shooter,
                         int startTick, ResourceKey<Level> dimension) {}

    public static final Queue<Strike> activeStrikes = new ConcurrentLinkedQueue<>();
    public static void initialize() {}

    public static void tick(MinecraftServer server) {
        Iterator<Strike> iterator = activeStrikes.iterator();
        while (iterator.hasNext()) {
            Strike strike = iterator.next();
            int age = server.getTickCount() - strike.startTick();
            if (age < 700) continue;
            iterator.remove();

            ServerLevel level = server.getLevel(strike.dimension());
            if (level == null || !level.hasChunkAt(strike.pos())
                || !level.getWorldBorder().isWithinBounds(strike.pos())) continue;
            ServerPlayer shooter = server.getPlayerList().getPlayer(strike.shooter());
            if (shooter == null || shooter.level() != level) continue;

            BlockState state = level.getBlockState(strike.pos());
            if (!state.equals(strike.originalState()) || state.isAir()
                || !state.getFluidState().isEmpty() || state.hasBlockEntity()
                || state.getDestroySpeed(level, strike.pos()) < 0
                || !level.mayInteract(shooter, strike.pos())
                || !shooter.mayUseItemAt(strike.pos(),
                    net.minecraft.core.Direction.UP, shooter.getMainHandItem())) continue;

            // Exactly ONE block. No drops, damage, fire, explosion or crater.
            level.destroyBlock(strike.pos(), false, shooter);
        }
    }
}
"""
NETWORK = r"""package io.github.mishkis.orbital_railgun.network;

import io.github.mishkis.orbital_railgun.client.OrbitalRailgunClientHooks;
import io.github.mishkis.orbital_railgun.item.OrbitalRailgunItems;
import io.github.mishkis.orbital_railgun.sound.OrbitalRailgunSounds;
import io.github.mishkis.orbital_railgun.util.OrbitalRailgunStrikeManager;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.neoforged.neoforge.network.PacketDistributor;
import java.time.Instant;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;

public final class OrbitalRailgunNetwork {
    private static final double MAX_RANGE = 128.0;

    public static void register(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar("1");
        registrar.playToServer(ShootPayload.TYPE, ShootPayload.STREAM_CODEC, OrbitalRailgunNetwork::handleShoot);
        registrar.playToClient(ClientSyncPayload.TYPE, ClientSyncPayload.STREAM_CODEC, OrbitalRailgunNetwork::handleClientSync);
    }

    private static void handleShoot(ShootPayload payload, IPayloadContext context) {
        context.enqueueWork(() -> {
            if (!(context.player() instanceof ServerPlayer shooter)) return;
            ItemStack held = shooter.getMainHandItem();
            if (!held.is(OrbitalRailgunItems.ORBITAL_RAILGUN.get())) return;
            if (shooter.getCooldowns().isOnCooldown(OrbitalRailgunItems.ORBITAL_RAILGUN.get())) return;
            long now = Instant.now().getEpochSecond();
            if (shooter.getPersistentData().getLong("brainmeth_orbital_ready_epoch") > now) return;

            // Never trust the target in a client packet. Recompute server-side.
            HitResult hit = shooter.pick(MAX_RANGE, 0.0F, false);
            if (!(hit instanceof BlockHitResult blockHit) || hit.getType() != HitResult.Type.BLOCK) return;
            BlockPos pos = blockHit.getBlockPos();
            if (!shooter.serverLevel().hasChunkAt(pos)
                || !shooter.serverLevel().getWorldBorder().isWithinBounds(pos)
                || !shooter.serverLevel().mayInteract(shooter, pos)
                || !shooter.mayUseItemAt(pos, Direction.UP, held)) return;
            BlockState state = shooter.serverLevel().getBlockState(pos);
            if (state.isAir() || !state.getFluidState().isEmpty()
                || state.hasBlockEntity() || state.getDestroySpeed(shooter.serverLevel(), pos) < 0) return;

            // Prevent simultaneous shots at the same block and packet spam.
            if (OrbitalRailgunStrikeManager.activeStrikes.size() >= 4
                || OrbitalRailgunStrikeManager.activeStrikes.stream()
                    .anyMatch(s -> s.shooter().equals(shooter.getUUID()))) return;

            shooter.getPersistentData().putLong("brainmeth_orbital_ready_epoch", now + 600);
            OrbitalRailgunItems.ORBITAL_RAILGUN.get().shoot(shooter);
            shooter.serverLevel().playSound(null, pos,
                OrbitalRailgunSounds.RAILGUN_SHOOT.get(), SoundSource.PLAYERS, 1.0F, 1.0F);
            OrbitalRailgunStrikeManager.activeStrikes.add(
                new OrbitalRailgunStrikeManager.Strike(pos, state, shooter.getUUID(),
                    shooter.server.getTickCount(), shooter.serverLevel().dimension()));

            // The original cinematic is client-rendered, but only nearby players
            // need the synchronization packet.
            for (ServerPlayer observer : shooter.server.getPlayerList().getPlayers()) {
                if (observer.serverLevel() == shooter.serverLevel()
                    && observer.position().distanceToSqr(pos.getCenter()) <= 300 * 300) {
                    PacketDistributor.sendToPlayer(observer, new ClientSyncPayload(pos));
                }
            }
        });
    }

    private static void handleClientSync(ClientSyncPayload payload, IPayloadContext context) {
        context.enqueueWork(() -> OrbitalRailgunClientHooks.onStrikeSync(payload.pos()));
    }
}
"""

def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--workdir", type=Path, required=True)
    args = p.parse_args()
    dest = args.workdir.resolve()
    if dest.exists():
        raise SystemExit(f"Refusing to overwrite existing directory: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run("git", "clone", "--filter=blob:none", "--no-checkout", UPSTREAM, str(dest))
    run("git", "checkout", "--detach", PIN, cwd=dest)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
    if sha != PIN:
        raise SystemExit(f"Unexpected upstream revision: {sha}")

    base = dest / SOURCE
    (base / "util/OrbitalRailgunStrikeManager.java").write_text(MANAGER)
    (base / "network/OrbitalRailgunNetwork.java").write_text(NETWORK)

    item = base / "item/OrbitalRailgunItem.java"
    original = item.read_text()
    assert "addCooldown(this, 2400)" in original, "Upstream cooldown changed"
    item.write_text(original.replace("addCooldown(this, 2400)", "addCooldown(this, 12000)"))

    mod = base / "OrbitalRailgun.java"
    original = mod.read_text()
    assert "modEventBus.addListener(OrbitalRailgunItems::addToCreativeTab);" in original
    mod.write_text(original.replace(
        "modEventBus.addListener(OrbitalRailgunItems::addToCreativeTab);",
        "// Brainmeth: item only available through bounty reward; no creative tab entry."))

    # No crafting recipe. This item is exclusively distributed via Bountiful.
    recipe = dest / "src/main/resources/data/orbital_railgun/recipe/orbital_railgun.json"
    if not recipe.is_file():
        raise SystemExit("Upstream recipe moved: aborting")
    recipe.unlink()

    # Verify destructive upstream implementation has been completely replaced.
    assert "setBlockAndUpdate" not in MANAGER
    assert "entity.hurt(" not in MANAGER
    assert "level.explode(" not in MANAGER
    assert "destroyBlock(strike.pos(), false, shooter)" in MANAGER
    assert "shooter.pick(MAX_RANGE" in NETWORK
    print("Pinned, patched and checked Orbital Railgun: Renewed (one-block precision).")
    print(f"Build with: cd {dest} && gradle --no-daemon clean build")

if __name__ == "__main__":
    main()
