package dev.cybersans.brainmeth;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundClearTitlesPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.PrimedTnt;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.projectile.ThrownPotion;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.living.LivingEntityUseItemEvent;
import net.neoforged.neoforge.event.entity.ProjectileImpactEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.BlockDropsEvent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.joml.Vector3f;

/** Batch-3 reward abilities, all attached to server-verified custom-data tags.
 * No survival recipes or natural drops exist; Bountiful wiring is separate.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethConsumables {
    private static final String REWARD = "brainmeth_reward";
    private static final long SCALE_SECONDS = 10 * 60;
    private static final int GOD_BUILDUP_TICKS = 5 * 20;
    private static final int GOD_COUNTDOWN_TICKS = 3 * 20;
    private static final int GOD_CREATIVE_TICKS = 20;
    private static final String SCALE_END = "brainmeth_scale_ends";
    private static final String SCALE_AMOUNT = "brainmeth_scale_factor";
    private static final String CREATIVE_END = "brainmeth_creative_ends"; // Legacy potion marker
    private static final String GOD_PHASE = "brainmeth_god_phase";
    private static final String GOD_TICK = "brainmeth_god_tick";
    private static final String GOD_HOVER_Y = "brainmeth_god_hover_y";
    private static final ResourceLocation SCALE_MODIFIER = ResourceLocation.fromNamespaceAndPath(BrainmethCore.MOD_ID, "potion_scale");
    private static final int MAX_FAKE_BLOCKS = 256;
    private static MinecraftServer trackedServer;
    private static final Map<String, Set<Long>> fakeBlocks = new HashMap<>();
    private static final List<PrimedTnt> fakeIgnitions = new ArrayList<>();
    private static final List<PrimedTnt> superIgnitions = new ArrayList<>();

    private BrainmethConsumables() {}

    private static String kind(ItemStack item) {
        CustomData custom = item.get(DataComponents.CUSTOM_DATA);
        return custom == null ? "" : custom.copyTag().getString(REWARD);
    }

    @SubscribeEvent
    public static void onItemUse(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND ||
            !(event.getEntity() instanceof ServerPlayer player) ||
            !(event.getLevel() instanceof ServerLevel level)) return;
        ItemStack item = event.getItemStack();
        String kind = kind(item);
        boolean used = false;
        switch (kind) {
            case "potion_everything" -> {
                if (item.is(Items.POTION)) {
                    applyEverything(player);
                    finishBottle(player, item);
                    used = true;
                }
            }
            case "potion_shrink", "potion_grow" -> {
                if (item.is(Items.POTION)) {
                    beginScale(player, kind.equals("potion_shrink") ? 0.2D : 2.0D);
                    finishBottle(player, item);
                    used = true;
                }
            }
            case "potion_creative" -> {
                // Let vanilla play the full drinking animation and consume
                // the bottle. The god-mode sequence starts on Finish, not click.
                return;
            }
            case "ultimate_chorus_fruit" -> {
                if (item.is(Items.CHORUS_FRUIT)) {
                    if (teleportToLoadedSafeLocation(level, player)) item.shrink(1);
                    used = true;
                }
            }
            default -> { return; } // Splash potions must use vanilla projectile throwing.
        }
        if (used) {
            event.setCancellationResult(InteractionResult.SUCCESS);
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onGodPotionDrunk(LivingEntityUseItemEvent.Finish event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
            || !event.getItem().is(Items.POTION)
            || !"potion_creative".equals(kind(event.getItem()))) return;
        if (player.gameMode.getGameModeForPlayer() == GameType.SURVIVAL
            && !player.getPersistentData().contains(GOD_PHASE)
            && !player.getPersistentData().contains(CREATIVE_END)) {
            startGodBuildUp(player);
        }
    }

    private static long now() { return Instant.now().getEpochSecond(); }

    private static void finishBottle(ServerPlayer player, ItemStack potion) {
        potion.shrink(1);
        ItemStack empty = new ItemStack(Items.GLASS_BOTTLE);
        if (!player.getInventory().add(empty)) player.drop(empty, false);
        player.containerMenu.broadcastChanges();
    }

    private static void applyEverything(ServerPlayer player) {
        // Beneficial potion/vanilla effects only. Excludes levitation and Omen variants.
        List<Holder<MobEffect>> positive = List.of(
            MobEffects.MOVEMENT_SPEED, MobEffects.DIG_SPEED, MobEffects.DAMAGE_BOOST,
            MobEffects.JUMP, MobEffects.REGENERATION, MobEffects.DAMAGE_RESISTANCE,
            MobEffects.FIRE_RESISTANCE, MobEffects.WATER_BREATHING, MobEffects.INVISIBILITY,
            MobEffects.NIGHT_VISION, MobEffects.HEALTH_BOOST, MobEffects.ABSORPTION,
            MobEffects.LUCK, MobEffects.SLOW_FALLING, MobEffects.CONDUIT_POWER,
            MobEffects.DOLPHINS_GRACE, MobEffects.HERO_OF_THE_VILLAGE
        );
        for (Holder<MobEffect> effect : positive) player.addEffect(new MobEffectInstance(effect, 20 * 180, 0));
        player.addEffect(new MobEffectInstance(MobEffects.HEAL, 1, 1));
        player.addEffect(new MobEffectInstance(MobEffects.SATURATION, 1, 0));
    }

    private static void beginScale(ServerPlayer player, double scale) {
        long expiry = now() + SCALE_SECONDS;
        CompoundTag data = player.getPersistentData();
        data.putLong(SCALE_END, expiry);
        data.putDouble(SCALE_AMOUNT, scale);
        updateScale(player, expiry, scale);
    }

    private static void updateScale(ServerPlayer player, long expiry, double scale) {
        AttributeInstance attribute = player.getAttribute(Attributes.SCALE);
        if (attribute == null) return;
        if (expiry <= now() || !player.isAlive()) {
            if (attribute.hasModifier(SCALE_MODIFIER)) attribute.removeModifier(SCALE_MODIFIER);
            player.getPersistentData().remove(SCALE_END);
            player.getPersistentData().remove(SCALE_AMOUNT);
        } else {
            double delta = scale - 1.0D;
            if (!attribute.hasModifier(SCALE_MODIFIER) ||
                Math.abs(attribute.getModifier(SCALE_MODIFIER).amount() - delta) > 0.0001) {
                attribute.addOrUpdateTransientModifier(new AttributeModifier(
                    SCALE_MODIFIER, delta, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
            }
        }
    }

    /** Vanilla drinking completes before five seconds of escalating golden particles. */
    private static void godTitle(ServerPlayer player, String title, String subtitle) {
        player.connection.send(new ClientboundSetTitlesAnimationPacket(0, 24, 0));
        player.connection.send(new ClientboundSetTitleTextPacket(
            Component.literal(title).withStyle(ChatFormatting.GOLD)));
        player.connection.send(new ClientboundSetSubtitleTextPacket(
            Component.literal(subtitle).withStyle(ChatFormatting.GOLD)));
    }

    private static void startGodBuildUp(ServerPlayer player) {
        CompoundTag data = player.getPersistentData();
        data.putString(GOD_PHASE, "buildup");
        data.putLong(GOD_TICK, player.serverLevel().getServer().getTickCount() + GOD_BUILDUP_TICKS);
        data.putDouble(GOD_HOVER_Y, player.getY() + 3.0D);
        godTitle(player, "A divine power awakens", "");
        org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
            .info("Creative Potion golden buildup started for {}", player.getGameProfile().getName());
    }

    private static void clearGodState(ServerPlayer player, boolean slowFalling) {
        CompoundTag data = player.getPersistentData();
        String phase = data.getString(GOD_PHASE);
        if ("creative".equals(phase)) player.setGameMode(GameType.SURVIVAL);
        data.remove(GOD_PHASE);
        data.remove(GOD_TICK);
        data.remove(GOD_HOVER_Y);
        // Slow Falling only at the end of the true Creative second;
        // it safely returns the player to the ground from the hover.
        if (slowFalling && "creative".equals(phase)) {
            player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 8, 0));
            godTitle(player, "God Mode expired", "");
        }
        org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
            .info("Creative Potion {} for {}", slowFalling ? "expired" : "cancelled",
                player.getGameProfile().getName());
    }

    private static void godHealAura(ServerPlayer player, long tick) {
        if (tick % 10 != 0) return;
        AABB range = player.getBoundingBox().inflate(10.0D);
        for (ServerPlayer target : player.serverLevel().getEntitiesOfClass(ServerPlayer.class, range,
             other -> other.isAlive() && other.distanceToSqr(player) <= 100.0D)) {
            target.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 30, 1, true, true));
        }
    }

    private static void godParticles(ServerPlayer player, long remaining, String phase, long tick) {
        if (tick % 3 != 0) return;
        double intensity = "buildup".equals(phase)
            ? 1.0D - Math.max(0, remaining) / (double) GOD_BUILDUP_TICKS : 1.0D;
        int count = 2 + (int) Math.round(30.0D * intensity);
        player.serverLevel().sendParticles(
            new DustParticleOptions(new Vector3f(1.0F, 0.70F, 0.08F), 1.3F),
            player.getX(), player.getY() + 1.0D, player.getZ(),
            count, 0.45D, 0.85D, 0.45D, 0.035D);
    }

    private static void godHover(ServerPlayer player) {
        CompoundTag data = player.getPersistentData();
        double diff = data.getDouble(GOD_HOVER_Y) - player.getY();
        // Slow, controlled upward movement capped near three blocks;
        // during the countdown the same controller maintains the hover.
        double yMotion = Math.max(-0.12D, Math.min(0.14D, diff * 0.13D + 0.075D));
        Vec3 old = player.getDeltaMovement();
        player.setDeltaMovement(old.x, yMotion, old.z);
        player.hurtMarked = true;
        player.fallDistance = 0.0F;
    }

    private static void tickGodMode(ServerPlayer player, long tick) {
        CompoundTag data = player.getPersistentData();
        if (!data.contains(GOD_PHASE)) return;
        String phase = data.getString(GOD_PHASE);
        if (!player.isAlive()) {
            clearGodState(player, false);
            return;
        }
        godHealAura(player, tick);
        long remaining = data.getLong(GOD_TICK) - tick;
        if ("buildup".equals(phase)) {
            godParticles(player, remaining, phase, tick);
            godHover(player);
            if (remaining <= 0) {
                data.putString(GOD_PHASE, "countdown");
                data.putLong(GOD_TICK, tick + GOD_COUNTDOWN_TICKS);
                godTitle(player, "You have obtained the power of God", "3");
            }
        } else if ("countdown".equals(phase)) {
            godParticles(player, remaining, phase, tick);
            godHover(player);
            if (remaining <= 0) {
                if (player.gameMode.getGameModeForPlayer() != GameType.SURVIVAL) {
                    clearGodState(player, false);
                    return;
                }
                data.putString(GOD_PHASE, "creative");
                data.putLong(GOD_TICK, tick + GOD_CREATIVE_TICKS);
                player.setGameMode(GameType.CREATIVE);
                godTitle(player, "GOD MODE ACTIVATED", "");
                org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
                    .info("Creative Potion true Creative activated for {}", player.getGameProfile().getName());
            } else if (remaining == 40 || remaining == 20) {
                godTitle(player, "You have obtained the power of God", String.valueOf(remaining / 20));
            }
        } else if ("creative".equals(phase)) {
            godParticles(player, remaining, phase, tick);
            if (remaining <= 0) clearGodState(player, true);
        } else clearGodState(player, false);
    }

    @SubscribeEvent
    public static void onGodLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        if (event.getEntity() instanceof ServerPlayer player
            && player.getPersistentData().contains(GOD_PHASE)) clearGodState(player, false);
    }

    @SubscribeEvent
    public static void onGodLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        CompoundTag data = player.getPersistentData();
        if (data.contains(GOD_PHASE)) clearGodState(player, false);
        // Recover from the legacy two-second version if a player was saved
        // while its temporary abilities were enabled.
        if (data.contains(CREATIVE_END)) {
            player.getAbilities().mayfly = data.getBoolean("brainmeth_prev_mayfly");
            player.getAbilities().flying = data.getBoolean("brainmeth_prev_flying");
            player.getAbilities().invulnerable = data.getBoolean("brainmeth_prev_invulnerable");
            player.onUpdateAbilities();
            data.remove(CREATIVE_END);
            data.remove("brainmeth_prev_mayfly");
            data.remove("brainmeth_prev_flying");
            data.remove("brainmeth_prev_invulnerable");
        }
    }

    private static boolean teleportToLoadedSafeLocation(ServerLevel level, ServerPlayer player) {
        BlockPos source = player.blockPosition();
        for (int attempt = 0; attempt < 144; attempt++) {
            // Sample a uniformly random point within a disk radius of 1,000.
            double angle = level.random.nextDouble() * (Math.PI * 2);
            // Prefer all loaded destinations first, then fall back to nearby loaded chunks.
            double r = Math.sqrt(level.random.nextDouble()) * (attempt < 96 ? 1000.0 : 160.0);
            int x = source.getX() + (int) Math.round(Math.cos(angle) * r);
            int z = source.getZ() + (int) Math.round(Math.sin(angle) * r);
            // Never generate chunks just for a teleport: that stalls shared servers.
            if (!level.hasChunk(x >> 4, z >> 4)) continue;
            if (!level.getWorldBorder().isWithinBounds(new BlockPos(x, source.getY(), z))) continue;
            BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
                                                new BlockPos(x, source.getY(), z));
            if (top.getY() < level.getMinBuildHeight() + 2 ||
                top.getY() >= level.getMaxBuildHeight() - 2) continue;
            if (!level.getBlockState(top).isAir() || !level.getBlockState(top.above()).isAir()) continue;
            if (level.getBlockState(top.below()).getFluidState().isEmpty() &&
                level.getBlockState(top.below()).isCollisionShapeFullBlock(level, top.below())) {
                player.teleportTo(level, x + 0.5, top.getY(), z + 0.5,
                                  player.getYRot(), player.getXRot());
                player.fallDistance = 0.0F;
                return true;
            }
        }
        return false;
    }

    @SubscribeEvent
    public static void onProjectileImpact(ProjectileImpactEvent event) {
        if (!(event.getProjectile() instanceof ThrownPotion potion) ||
            !(potion.level() instanceof ServerLevel level)) return;
        String kind = kind(potion.getItem());
        if (!kind.equals("splash_binding") && !kind.equals("splash_vanishing") &&
            !kind.equals("splash_coronavirus")) return;
        // Cancel vanilla water-potion effect and resolve the custom impact ourselves.
        event.setCanceled(true);
        Vec3 impact = event.getRayTraceResult().getLocation();
        AABB area = new AABB(impact, impact).inflate(4);
        int affected = 0;
        for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, area,
                     entity -> entity.isAlive() && entity.distanceToSqr(impact) <= 16.0)) {
            if (kind.equals("splash_coronavirus")) {
                for (Holder<MobEffect> effect : List.of(MobEffects.CONFUSION, MobEffects.HUNGER,
                                                        MobEffects.OOZING, MobEffects.WEAKNESS)) {
                    target.addEffect(new MobEffectInstance(effect, 20 * 60 * 8, 0));
                }
            } else {
                var registry = level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT);
                var curse = registry.getOrThrow(kind.equals("splash_binding") ?
                    Enchantments.BINDING_CURSE : Enchantments.VANISHING_CURSE);
                for (EquipmentSlot slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST,
                                                   EquipmentSlot.LEGS, EquipmentSlot.FEET)) {
                    ItemStack armour = target.getItemBySlot(slot);
                    if (!armour.isEmpty() && armour.isDamageableItem()) armour.enchant(curse, 1);
                }
            }
            affected++;
        }
        level.levelEvent(2002, BlockPos.containing(impact), 0);
        potion.discard();
    }

    @SubscribeEvent
    public static void onPlaceTnt(PlayerInteractEvent.RightClickBlock event) {
        // Special TNT in either hand must never take vanilla's ordinary-TNT
        // placement path, otherwise it could become genuinely explosive.
        if (!(event.getEntity() instanceof ServerPlayer player) ||
            !(event.getLevel() instanceof ServerLevel level)) return;
        ItemStack item = event.getItemStack();
        String kind = kind(item);
        if (!item.is(Items.TNT) || (!kind.equals("super_tnt") && !kind.equals("fake_tnt"))) return;
        Direction face = event.getFace();
        if (face == null) return;
        BlockPos at = event.getPos();
        BlockPos target = level.getBlockState(at).canBeReplaced() ? at : at.relative(face);
        if (!level.mayInteract(player, target) || !level.getWorldBorder().isWithinBounds(target) ||
            !level.getBlockState(target).canBeReplaced()) {
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.FAIL);
            return;
        }
        ensureTntLoaded(level.getServer());
        if (kind.equals("fake_tnt")) {
            if (fakeBlockCount() >= MAX_FAKE_BLOCKS) {
                event.setCanceled(true);
                event.setCancellationResult(InteractionResult.FAIL);
                return;
            }
            if (level.setBlock(target, Blocks.TNT.defaultBlockState(), 3)) {
                fakeBlocks.computeIfAbsent(level.dimension().location().toString(), k -> new HashSet<>())
                          .add(target.asLong());
                saveFakeBlocks(level.getServer());
                item.shrink(1);
            }
        } else {
            // A single timed bomb with ~20x TNT energy; power scales as cube root of energy.
            PrimedTnt explosive = new PrimedTnt(level, target.getX() + 0.5,
                target.getY(), target.getZ() + 0.5, player);
            explosive.setFuse(80);
            explosive.getPersistentData().putBoolean("brainmeth_super_tnt", true);
            if (level.addFreshEntity(explosive)) {
                item.shrink(1);
                level.playSound(null, target, SoundEvents.TNT_PRIMED, SoundSource.BLOCKS, 1, 1);
            }
        }
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
    }

    /**
     * Creative breaks do not produce a BlockDropsEvent. Remove the registry
     * entry here; survival drops are handled below after vanilla determines
     * whether a block should drop an item at all.
     */
    @SubscribeEvent
    public static void onBlockBroken(BlockEvent.BreakEvent event) {
        if (event.isCanceled() || !(event.getLevel() instanceof ServerLevel level)
            || !(event.getPlayer() instanceof ServerPlayer player)
            || !player.getAbilities().instabuild) return;
        ensureTntLoaded(level.getServer());
        Set<Long> positions = fakeBlocks.get(level.dimension().location().toString());
        if (positions != null && positions.remove(event.getPos().asLong()))
            saveFakeBlocks(level.getServer());
    }

    /**
     * Placed TNT blocks have no item data. Restore the fake identity on their
     * normal vanilla drops so breaking/replacing the block never turns it into
     * real, explosive TNT. Mutating drops (instead of generating new ones)
     * respects doTileDrops and other mods' loot changes.
     */
    @SubscribeEvent
    public static void onFakeTntDrops(BlockDropsEvent event) {
        ServerLevel level = event.getLevel();
        ensureTntLoaded(level.getServer());
        Set<Long> positions = fakeBlocks.get(level.dimension().location().toString());
        if (positions == null || !positions.remove(event.getPos().asLong())) return;
        saveFakeBlocks(level.getServer());
        if (!event.getState().is(Blocks.TNT)) return;
        for (ItemEntity drop : event.getDrops()) {
            ItemStack stack = drop.getItem();
            if (!stack.is(Items.TNT)) continue;
            CompoundTag tag = new CompoundTag();
            tag.putString(REWARD, "fake_tnt");
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            stack.set(DataComponents.ITEM_NAME,
                Component.literal("Fake TNT").withStyle(ChatFormatting.LIGHT_PURPLE));
            stack.set(DataComponents.LORE, new ItemLore(List.of(
                Component.literal("A prank TNT block. Prime normally, fizzle, and return to a TNT block.")
                    .withStyle(ChatFormatting.GRAY))));
            stack.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        }
    }

    @SubscribeEvent
    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if (!(event.getLevel() instanceof ServerLevel level) ||
            !(event.getEntity() instanceof PrimedTnt tnt)) return;
        ensureTntLoaded(level.getServer());
        CompoundTag tag = tnt.getPersistentData();
        if (tag.getBoolean("brainmeth_super_tnt")) {
            if (!superIgnitions.contains(tnt)) superIgnitions.add(tnt);
            return;
        }
        if (tag.getBoolean("brainmeth_fake_ignited")) {
            if (!fakeIgnitions.contains(tnt)) fakeIgnitions.add(tnt);
            return;
        }
        String dim = level.dimension().location().toString();
        Set<Long> positions = fakeBlocks.get(dim);
        if (positions != null && positions.remove(tnt.blockPosition().asLong())) {
            tag.putBoolean("brainmeth_fake_ignited", true);
            tag.putLong("brainmeth_original_pos", tnt.blockPosition().asLong());
            fakeIgnitions.add(tnt);
            saveFakeBlocks(level.getServer());
        }
    }

    private static void ensureTntLoaded(MinecraftServer server) {
        if (trackedServer == server) return;
        trackedServer = server;
        fakeBlocks.clear();
        fakeIgnitions.clear();
        superIgnitions.clear();
        Path file = registryFile(server);
        if (!Files.exists(file)) return;
        try (var reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            for (String dim : root.keySet()) {
                Set<Long> stored = new HashSet<>();
                JsonArray positions = root.getAsJsonArray(dim);
                for (var position : positions) stored.add(position.getAsLong());
                fakeBlocks.put(dim, stored);
            }
        } catch (Exception ex) {
            BrainmethCoreLog.warn("Cannot load fake TNT positions; not converting unknown blocks: " + ex);
        }
    }

    private static Path registryFile(MinecraftServer server) {
        return server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT)
                     .resolve("brainmeth-fake-tnt.json");
    }

    private static int fakeBlockCount() {
        return fakeBlocks.values().stream().mapToInt(Set::size).sum();
    }

    private static void saveFakeBlocks(MinecraftServer server) {
        JsonObject root = new JsonObject();
        fakeBlocks.forEach((dimension, positions) -> {
            JsonArray encoded = new JsonArray();
            for (long packed : positions) encoded.add(packed);
            root.add(dimension, encoded);
        });
        Path file = registryFile(server);
        Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
        try {
            Files.writeString(tmp, root.toString() + "\n", StandardCharsets.UTF_8);
            try { Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ex) {
            BrainmethCoreLog.warn("Failed to save fake TNT registry: " + ex);
        }
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        ensureTntLoaded(server);
        for (ServerPlayer player : server.getPlayerList().getPlayers()) {
            CompoundTag data = player.getPersistentData();
            if (data.contains(SCALE_END)) updateScale(player, data.getLong(SCALE_END), data.getDouble(SCALE_AMOUNT));
            if (data.contains(GOD_PHASE)) tickGodMode(player, server.getTickCount());
        }
        Iterator<PrimedTnt> fake = fakeIgnitions.iterator();
        while (fake.hasNext()) {
            PrimedTnt tnt = fake.next();
            if (!tnt.isAlive()) { fake.remove(); continue; }
            if (tnt.getFuse() <= 2) {
                ServerLevel level = (ServerLevel) tnt.level();
                BlockPos original = BlockPos.of(tnt.getPersistentData().getLong("brainmeth_original_pos"));
                tnt.discard();
                if (level.getBlockState(original).canBeReplaced()
                    && level.setBlock(original, Blocks.TNT.defaultBlockState(), 3)) {
                    // The same fake TNT remains harmless when primed repeatedly.
                    fakeBlocks.computeIfAbsent(level.dimension().location().toString(),
                        k -> new HashSet<>()).add(original.asLong());
                    saveFakeBlocks(level.getServer());
                }
                level.playSound(null, original, SoundEvents.NOTE_BLOCK_PLING.value(), SoundSource.BLOCKS, 1.0f, 1.25f);
                fake.remove();
            }
        }
        Iterator<PrimedTnt> superTnt = superIgnitions.iterator();
        while (superTnt.hasNext()) {
            PrimedTnt tnt = superTnt.next();
            if (!tnt.isAlive()) { superTnt.remove(); continue; }
            if (tnt.getFuse() <= 2) {
                ServerLevel level = (ServerLevel) tnt.level();
                double x = tnt.getX(), y = tnt.getY(), z = tnt.getZ();
                tnt.discard();
                level.explode(null, x, y, z, (float)(4.0 * Math.cbrt(20)),
                              Level.ExplosionInteraction.TNT);
                superTnt.remove();
            }
        }
    }

    /** Deliberately narrow logger: avoid changing the existing launch scheduler. */
    private static class BrainmethCoreLog {
        static void warn(String message) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).warn(message);
        }
    }
}
