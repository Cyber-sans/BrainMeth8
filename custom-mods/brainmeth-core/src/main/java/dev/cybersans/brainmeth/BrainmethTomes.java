package dev.cybersans.brainmeth;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.logging.LogUtils;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.MobSpawnSettings;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.EventHooks;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;
import net.neoforged.neoforge.network.registration.PayloadRegistrar;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/**
 * Three world-wide midnight rituals. Server authority owns state, cooldowns and
 * spawning; the client only reports book-screen close and renders a red sky.
 *
 * No biome modifiers, gamerule writes, chunk generation, or changes to other
 * mods' spawn tables. All additional spawns obey NATURAL placement hooks and
 * are bounded by a local population cap and a strict per-second work budget.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethTomes {
    private static final Logger LOG = LogUtils.getLogger();
    private static final String MARKER = "brainmeth_reward";
    private static final String COOLDOWN = "brainmeth_tome_ready_epoch";
    private static final long RECHARGE_SECONDS = 30L * 24 * 60 * 60;
    private static final long EVENT_TICKS = 7L * 24000L;
    private static final long DAY_TICKS = 24000L;
    private static final long MIDNIGHT = 18000L;
    private static final int BOOST_ATTEMPTS_PER_PLAYER_SECOND = 100;
    private static final int MAX_EXTRA_SPAWNS_PER_SECOND = 12;
    private static final int MAX_NEARBY_HOSTILES = 70;
    private static final Map<UUID, OpenBook> opened = new HashMap<>();

    private enum Ritual {
        NONE("", ""), BONE("tome_of_bone", "Tome of Bone"),
        CATACOMB("tome_of_catacomb", "Tome of Catacomb"),
        CURSED("tome_of_cursed_biome", "Tome of the Cursed Biome");
        final String itemTag;
        final String title;
        Ritual(String tag, String title) { this.itemTag = tag; this.title = title; }
        static Ritual of(String tag) {
            for (Ritual ritual : values()) if (!tag.isEmpty() && tag.equals(ritual.itemTag)) return ritual;
            return NONE;
        }
    }

    private record OpenBook(Ritual kind, InteractionHand hand, long tick) {}
    private static MinecraftServer loadedServer;
    private static Ritual ritual = Ritual.NONE;
    private static long nextMidnight;
    private static long endGameTime;
    private static int ticks;
    private static long lastSpawnWaveNanos;

    private BrainmethTomes() {}

    public static void registerPayloads(RegisterPayloadHandlersEvent event) {
        PayloadRegistrar registrar = event.registrar("1");
        registrar.playToServer(CloseTome.TYPE, CloseTome.CODEC, BrainmethTomes::receiveClose);
        registrar.playToClient(RedSky.TYPE, RedSky.CODEC, BrainmethTomes::receiveSky);
        BrainmethConsumables.registerPayload(registrar);
    }

    public record CloseTome() implements CustomPacketPayload {
        public static final Type<CloseTome> TYPE = new Type<>(
            ResourceLocation.fromNamespaceAndPath(BrainmethCore.MOD_ID, "tome_closed"));
        public static final StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, CloseTome> CODEC =
            StreamCodec.unit(new CloseTome());
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    public record RedSky(boolean enabled) implements CustomPacketPayload {
        public static final Type<RedSky> TYPE = new Type<>(
            ResourceLocation.fromNamespaceAndPath(BrainmethCore.MOD_ID, "blood_sky"));
        public static final StreamCodec<net.minecraft.network.RegistryFriendlyByteBuf, RedSky> CODEC =
            StreamCodec.composite(ByteBufCodecs.BOOL, RedSky::enabled, RedSky::new);
        @Override public Type<? extends CustomPacketPayload> type() { return TYPE; }
    }

    private static void receiveSky(RedSky packet, IPayloadContext context) {
        if (context.player().level().isClientSide()) BrainmethTomesClient.receiveSky(packet, context);
    }

    private static void receiveClose(CloseTome packet, IPayloadContext context) {
        if (context.player() instanceof ServerPlayer player) closeBook(player);
    }

    private static String tag(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString(MARKER);
    }

    @SubscribeEvent
    public static void bookOpened(PlayerInteractEvent.RightClickItem event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        ItemStack item = event.getItemStack();
        if (!item.is(Items.WRITTEN_BOOK)) return;
        Ritual kind = Ritual.of(tag(item));
        if (kind == Ritual.NONE) return;
        load(player.getServer());
        opened.put(player.getUUID(), new OpenBook(kind, event.getHand(), player.serverLevel().getGameTime()));
        // Do not cancel the vanilla action: the client must open all six pages.
    }

    private static void closeBook(ServerPlayer player) {
        OpenBook book = opened.remove(player.getUUID());
        if (book == null || player.serverLevel().getGameTime() - book.tick() > 20L * 60 * 15) return;
        ItemStack item = player.getItemInHand(book.hand());
        if (!item.is(Items.WRITTEN_BOOK) || Ritual.of(tag(item)) != book.kind()) return;
        MinecraftServer server = player.getServer();
        load(server);
        ServerLevel overworld = server.overworld();
        if (ritual != Ritual.NONE) {
            player.sendSystemMessage(Component.literal("Another Tome ritual is already pending or active.")
                .withStyle(ChatFormatting.RED));
            return;
        }
        CustomData data = item.get(DataComponents.CUSTOM_DATA);
        if (data == null) return;
        CompoundTag tag = data.copyTag();
        long now = Instant.now().getEpochSecond();
        long ready = tag.getLong(COOLDOWN);
        if (ready > now) {
            player.sendSystemMessage(Component.literal("This Tome recharges in "
                + ((ready - now + 86399) / 86400) + " real-world day(s).")
                .withStyle(ChatFormatting.RED));
            return;
        }

        long dayTime = overworld.getDayTime();
        long midnight = Math.floorDiv(dayTime, DAY_TICKS) * DAY_TICKS + MIDNIGHT;
        if (midnight <= dayTime) midnight += DAY_TICKS;
        ritual = book.kind();
        nextMidnight = midnight;
        endGameTime = 0;
        if (!save(server)) {
            ritual = Ritual.NONE;
            nextMidnight = 0;
            player.sendSystemMessage(Component.literal("Ritual could not be saved; activation cancelled.")
                .withStyle(ChatFormatting.RED));
            return;
        }
        tag.putLong(COOLDOWN, now + RECHARGE_SECONDS);
        item.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        player.containerMenu.broadcastChanges();
        server.getPlayerList().broadcastSystemMessage(
            Component.literal("The " + ritual.title + " has been activated")
                .withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD), false);
        player.sendSystemMessage(Component.literal("The curse will rise at the following midnight.")
            .withStyle(ChatFormatting.DARK_RED));
        LOG.info("{} activated by {}. Pending until Overworld dayTime {}.",
            ritual.title, player.getGameProfile().getName(), nextMidnight);
    }

    @SubscribeEvent
    public static void onLoggedIn(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        load(player.getServer());
        PacketDistributor.sendToPlayer(player, new RedSky(endGameTime != 0));
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        opened.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        load(server);
        if (ritual == Ritual.NONE) return;
        ServerLevel level = server.overworld();
        if (endGameTime == 0) {
            if (level.getDayTime() < nextMidnight) return;
            endGameTime = level.getGameTime() + EVENT_TICKS;
            level.setDayTime(nextMidnight);
            save(server);
            PacketDistributor.sendToAllPlayers(new RedSky(true));
            LOG.info("Brainmeth midnight ritual started: {} ({} game ticks)", ritual.title, EVENT_TICKS);
        }
        if (level.getGameTime() >= endGameTime) {
            LOG.info("Brainmeth midnight ritual ended: {}", ritual.title);
            ritual = Ritual.NONE;
            nextMidnight = 0;
            endGameTime = 0;
            ticks = 0;
            save(server);
            PacketDistributor.sendToAllPlayers(new RedSky(false));
            return;
        }
        // Freeze only the Overworld daylight clock. gameTime still advances and
        // is the timer, so seven Minecraft days elapse despite frozen daylight.
        if (level.getDayTime() != nextMidnight) level.setDayTime(nextMidnight);
        if (++ticks % 20 != 0 || !level.getGameRules().getBoolean(GameRules.RULE_DOMOBSPAWNING)) return;
        // Measure the actual last 20 server ticks without relying on an
        // unstable cross-version TPS API. Skip bonus spawning below ~13 TPS.
        long nowNanos = System.nanoTime();
        boolean overloaded = lastSpawnWaveNanos != 0
            && nowNanos - lastSpawnWaveNanos > 20L * 75_000_000L;
        lastSpawnWaveNanos = nowNanos;
        if (!overloaded) bonusSpawnWave(level);
    }

    private static void bonusSpawnWave(ServerLevel level) {
        int totalSpawned = 0;
        List<ServerPlayer> players = level.players();
        for (ServerPlayer player : players) {
            if (player.isSpectator() || !player.isAlive()) continue;
            if (totalSpawned >= MAX_EXTRA_SPAWNS_PER_SECOND) return;
            // The global hostile cap protects other mods' entity budgets too.
            int localCount = level.getEntitiesOfClass(Mob.class,
                player.getBoundingBox().inflate(64, 40, 64), e -> e instanceof Enemy).size();
            if (localCount >= MAX_NEARBY_HOSTILES) continue;
            int remaining = Math.min(4, MAX_EXTRA_SPAWNS_PER_SECOND - totalSpawned);
            int playerSpawned = 0;
            for (int n = 0; n < BOOST_ATTEMPTS_PER_PLAYER_SECOND
                    && playerSpawned < remaining; n++) {
                if (spawnOne(level, player)) {
                    playerSpawned++;
                    totalSpawned++;
                }
            }
        }
    }

    private static boolean spawnOne(ServerLevel level, ServerPlayer player) {
        int dx = level.random.nextInt(97) - 48;
        int dz = level.random.nextInt(97) - 48;
        if (dx * dx + dz * dz < 24 * 24) return false;
        int x = player.getBlockX() + dx;
        int z = player.getBlockZ() + dz;
        BlockPos sample = new BlockPos(x, player.getBlockY(), z);
        if (!level.hasChunkAt(sample) || !level.getWorldBorder().isWithinBounds(sample)) return false;
        int surface = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
        int y = player.getBlockY() < surface - 12
            ? player.getBlockY() + level.random.nextInt(21) - 10 : surface;
        if (y < level.getMinBuildHeight() + 2 || y >= level.getMaxBuildHeight() - 2) return false;
        BlockPos pos = new BlockPos(x, y, z);
        if (!level.hasChunkAt(pos) || !level.getBlockState(pos).isAir()) return false;

        EntityType<?> type = switch (ritual) {
            case BONE -> EntityType.SKELETON;
            case CATACOMB -> EntityType.ZOMBIE;
            case CURSED -> chooseBiomeMonster(level, pos);
            default -> null;
        };
        if (type == null) return false;
        Entity mobEntity = type.create(level);
        if (!(mobEntity instanceof Mob mob) || !(mob instanceof Enemy)) return false;
        @SuppressWarnings("unchecked")
        EntityType<? extends Mob> mobType = (EntityType<? extends Mob>) type;
        if (!SpawnPlacements.checkSpawnRules(mobType, level, MobSpawnType.NATURAL, pos, level.random))
            return false;
        mob.moveTo(x + 0.5, y, z + 0.5, level.random.nextFloat() * 360, 0);
        if (!EventHooks.checkSpawnPosition(mob, level, MobSpawnType.NATURAL)) return false;
        mob.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), MobSpawnType.NATURAL, null);
        return level.addFreshEntity(mob);
    }

    /** Cursed biome uses the biome's actual naturally-spawning hostile entries,
     * including compatible modded mobs, rather than editing any spawn tables. */
    private static EntityType<?> chooseBiomeMonster(ServerLevel level, BlockPos pos) {
        List<MobSpawnSettings.SpawnerData> entries = level.getBiome(pos).value()
            .getMobSettings().getMobs(MobCategory.MONSTER).unwrap();
        int total = 0;
        for (MobSpawnSettings.SpawnerData entry : entries) {
            if (entry.type.getCategory() == MobCategory.MONSTER)
                total += entry.getWeight().asInt();
        }
        if (total <= 0) return null;
        int roll = level.random.nextInt(total);
        for (MobSpawnSettings.SpawnerData entry : entries) {
            if (entry.type.getCategory() != MobCategory.MONSTER) continue;
            roll -= entry.getWeight().asInt();
            if (roll < 0) return entry.type;
        }
        return null;
    }

    @SubscribeEvent
    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("tomes")
            .requires(s -> s.hasPermission(2))
            .then(Commands.literal("status").executes(ctx -> {
                load(ctx.getSource().getServer());
                String status = ritual == Ritual.NONE ? "No ritual pending or active"
                    : endGameTime == 0 ? ritual.title + " pending at midnight " + nextMidnight
                    : ritual.title + " active; " + Math.max(0, endGameTime
                        - ctx.getSource().getServer().overworld().getGameTime()) + " ticks left";
                ctx.getSource().sendSuccess(() -> Component.literal(status), false);
                return 1;
            }))
            .then(Commands.literal("cancel").executes(ctx -> {
                load(ctx.getSource().getServer());
                ritual = Ritual.NONE;
                nextMidnight = 0;
                endGameTime = 0;
                ticks = 0;
                boolean saved = save(ctx.getSource().getServer());
                PacketDistributor.sendToAllPlayers(new RedSky(false));
                ctx.getSource().sendSuccess(() -> Component.literal(saved
                    ? "Tome ritual cancelled; normal Overworld time resumes."
                    : "Ritual stopped but could not be saved; check server logs."), true);
                return saved ? 1 : 0;
            })));
    }

    private static Path stateFile(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-tomes.json");
    }

    private static void load(MinecraftServer server) {
        if (loadedServer == server) return;
        loadedServer = server;
        ritual = Ritual.NONE;
        nextMidnight = 0;
        endGameTime = 0;
        ticks = 0;
        lastSpawnWaveNanos = 0;
        opened.clear();
        Path path = stateFile(server);
        if (!Files.exists(path)) return;
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            JsonObject data = JsonParser.parseReader(reader).getAsJsonObject();
            Ritual restored = Ritual.valueOf(data.get("ritual").getAsString());
            if (restored == Ritual.NONE) return;
            long midnight = data.get("midnight").getAsLong();
            long end = data.get("endGameTime").getAsLong();
            if (midnight < 0 || midnight % DAY_TICKS != MIDNIGHT || end < 0)
                throw new IOException("Invalid Tome schedule");
            ritual = restored;
            nextMidnight = midnight;
            endGameTime = end;
            LOG.info("Restored Brainmeth ritual {} at midnight {} until gameTime {}",
                ritual, midnight, end);
        } catch (Exception ex) {
            LOG.error("Could not read Tome state; refusing to resume corrupt ritual", ex);
            ritual = Ritual.NONE;
            nextMidnight = 0;
            endGameTime = 0;
        }
    }

    private static boolean save(MinecraftServer server) {
        Path path = stateFile(server);
        Path tmp = path.resolveSibling(path.getFileName() + ".tmp");
        JsonObject data = new JsonObject();
        data.addProperty("ritual", ritual.name());
        data.addProperty("midnight", nextMidnight);
        data.addProperty("endGameTime", endGameTime);
        try {
            Files.writeString(tmp, data.toString() + System.lineSeparator(), StandardCharsets.UTF_8);
            try {
                Files.move(tmp, path, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(tmp, path, StandardCopyOption.REPLACE_EXISTING);
            }
            return true;
        } catch (IOException ex) {
            LOG.error("Cannot save Brainmeth Tome state", ex);
            return false;
        }
    }
}
