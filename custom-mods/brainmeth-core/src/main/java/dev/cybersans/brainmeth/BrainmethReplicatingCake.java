package dev.cybersans.brainmeth;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CakeBlock;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.minecraft.world.level.storage.LevelResource;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/**
 * A single-use-placeable cake that provides six slices per hour.
 * The last slice is never edible; after six bites, the cake is locked while
 * it regrows one slice every ten real minutes. It never clones or drops itself.
 */
@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethReplicatingCake {
    private static final long SLICE_REGEN_SECONDS = 10 * 60L;
    private static final int CAKES_CHECKED_PER_SECOND = 20;
    // Value 0 = not regenerating. Positive = epoch second of next slice.
    private static final Map<String,Map<Long,Long>> cakes = new HashMap<>();
    private static MinecraftServer loadedServer;
    private static int ticks;
    private record CakeKey(String dimension,long packed) {}
    private static final Deque<CakeKey> rotation = new ArrayDeque<>();

    private BrainmethReplicatingCake() {}
    private static long now() { return Instant.now().getEpochSecond(); }
    private static String dim(ServerLevel level) { return level.dimension().location().toString(); }

    private static String kind(ItemStack item) {
        CustomData data = item.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString("brainmeth_reward");
    }

    private static boolean hasCake(ServerLevel level,BlockPos pos) {
        return cakes.getOrDefault(dim(level),Map.of()).containsKey(pos.asLong());
    }

    @SubscribeEvent
    public static void onRightClick(PlayerInteractEvent.RightClickBlock event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;
        load(level.getServer());
        ItemStack held = event.getItemStack();
        BlockPos pos = event.getPos();

        if (event.getHand() == InteractionHand.MAIN_HAND
            && held.is(Items.CAKE) && kind(held).equals("replicating_cake")) {
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.SUCCESS);
            BlockPos target = level.getBlockState(pos).canBeReplaced()
                ? pos : pos.relative(event.getFace());
            if (!level.mayInteract(player,target)
                || !level.getWorldBorder().isWithinBounds(target)
                || !level.getBlockState(target).canBeReplaced()
                || !Blocks.CAKE.defaultBlockState().canSurvive(level,target)) {
                // No special hint on placement; the item appears to be ordinary cake.
                return;
            }
            if (level.setBlock(target,Blocks.CAKE.defaultBlockState(),3)) {
                cakes.computeIfAbsent(dim(level),k -> new HashMap<>())
                    .put(target.asLong(),0L);
                rotation.addLast(new CakeKey(dim(level),target.asLong()));
                save(level.getServer());
                held.shrink(1);
            }
            return;
        }

        if (!hasCake(level,pos) || !level.getBlockState(pos).is(Blocks.CAKE)) return;
        // Cancel both hands so vanilla CakeBlock cannot consume the protected
        // final slice, including via offhand fallback.
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        if (event.getHand() != InteractionHand.MAIN_HAND) return;
        if (!player.canEat(false)) return;

        int bites = level.getBlockState(pos).getValue(CakeBlock.BITES);
        Map<Long,Long> area = cakes.get(dim(level));
        long nextSlice = area.getOrDefault(pos.asLong(),0L);
        if (nextSlice > 0L || bites >= 6) {
            // A legacy cake may already have reached its last slice.
            if (nextSlice == 0L && bites >= 6) {
                area.put(pos.asLong(),now()+SLICE_REGEN_SECONDS);
                save(level.getServer());
            }
            return;
        }

        player.getFoodData().eat(2,0.1F);
        int newBites = bites+1;
        if (!level.setBlock(pos,level.getBlockState(pos).setValue(CakeBlock.BITES,newBites),3))
            return;
        if (newBites >= 6) {
            area.put(pos.asLong(),now()+SLICE_REGEN_SECONDS);
            save(level.getServer());
        }
    }

    @SubscribeEvent
    public static void onBreak(BlockEvent.BreakEvent event) {
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        load(level.getServer());
        Map<Long,Long> area = cakes.get(dim(level));
        if (area != null && area.remove(event.getPos().asLong()) != null) {
            rotation.removeIf(key -> key.dimension().equals(dim(level))
                && key.packed() == event.getPos().asLong());
            save(level.getServer());
        }
        // CakeBlock naturally drops no item; no replacement cake is awarded.
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        load(server);
        if (++ticks % 20 != 0 || rotation.isEmpty()) return;

        List<CakeKey> selected = new ArrayList<>();
        for (int i=0; i<CAKES_CHECKED_PER_SECOND && !rotation.isEmpty(); i++) {
            CakeKey key = rotation.pollFirst();
            if (cakes.getOrDefault(key.dimension(),Map.of()).containsKey(key.packed())) {
                selected.add(key);
                rotation.addLast(key);
            }
        }

        long current = now();
        boolean dirty = false;
        for (CakeKey key : selected) {
            String dimension = key.dimension();
            long packed = key.packed();
            Map<Long,Long> area = cakes.get(dimension);
            if (area == null || !area.containsKey(packed)) continue;

            ServerLevel level = null;
            for (ServerLevel candidate : server.getAllLevels())
                if (dim(candidate).equals(dimension)) { level = candidate; break; }
            if (level == null) continue;

            BlockPos pos = BlockPos.of(packed);
            if (!level.hasChunkAt(pos)) continue; // Never load/generate chunks.
            if (!level.getBlockState(pos).is(Blocks.CAKE)) {
                area.remove(packed);
                rotation.remove(key);
                dirty = true;
                continue;
            }

            int bites = level.getBlockState(pos).getValue(CakeBlock.BITES);
            long nextSlice = area.get(packed);
            if (nextSlice == 0L) {
                // Migrate legacy last-slice cakes without restoring the final slice.
                if (bites >= 6) {
                    area.put(packed,current+SLICE_REGEN_SECONDS);
                    dirty = true;
                }
                continue;
            }
            if (bites == 0) {
                area.put(packed,0L);
                dirty = true;
                continue;
            }
            if (current < nextSlice) continue;

            // Wall-clock catch-up also works across server restarts and unloads.
            int slices = (int)Math.min((long)bites,
                1L + (current-nextSlice)/SLICE_REGEN_SECONDS);
            int remainingBites = bites-slices;
            if (!level.setBlock(pos,level.getBlockState(pos)
                .setValue(CakeBlock.BITES,remainingBites),3)) continue;
            area.put(packed,remainingBites == 0 ? 0L
                : nextSlice+slices*SLICE_REGEN_SECONDS);
            dirty = true;
        }
        if (dirty) save(server);
    }

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT)
            .resolve("brainmeth-replicating-cakes.json");
    }

    private static void load(MinecraftServer server) {
        if (loadedServer == server) return;
        loadedServer = server;
        cakes.clear();
        rotation.clear();
        ticks = 0;
        Path source = file(server);
        if (!Files.isRegularFile(source)) return;
        try (var reader = Files.newBufferedReader(source,StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            boolean legacy = !root.has("version");
            JsonObject dimensions = legacy ? root : root.getAsJsonObject("cakes");
            for (String dimension : dimensions.keySet()) {
                Map<Long,Long> area = new HashMap<>();
                JsonObject positions = dimensions.getAsJsonObject(dimension);
                for (String packedString : positions.keySet()) {
                    long packed = Long.parseLong(packedString);
                    // Legacy values were next CLONE time; discard them.
                    long nextSlice = legacy ? 0L : positions.get(packedString).getAsLong();
                    area.put(packed,nextSlice);
                    rotation.addLast(new CakeKey(dimension,packed));
                }
                cakes.put(dimension,area);
            }
            if (legacy) {
                // Keep the pre-migration world data for rollback.
                Path backup = source.resolveSibling("brainmeth-replicating-cakes.v1-backup.json");
                if (Files.notExists(backup)) Files.copy(source,backup);
                save(server);
            }
        } catch (Exception ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
                .error("Unable to load regenerating cakes",ex);
        }
    }

    private static void save(MinecraftServer server) {
        JsonObject root = new JsonObject();
        root.addProperty("version",2);
        JsonObject dimensions = new JsonObject();
        cakes.forEach((dimension,positions) -> {
            JsonObject entries = new JsonObject();
            positions.forEach((packed,nextSlice) ->
                entries.addProperty(Long.toString(packed),nextSlice));
            dimensions.add(dimension,entries);
        });
        root.add("cakes",dimensions);

        Path destination = file(server);
        Path tmp = destination.resolveSibling(destination.getFileName()+".tmp");
        try {
            Files.writeString(tmp,root.toString()+"\n",StandardCharsets.UTF_8);
            try {
                Files.move(tmp,destination,StandardCopyOption.REPLACE_EXISTING,
                    StandardCopyOption.ATOMIC_MOVE);
            } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                Files.move(tmp,destination,StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
                .error("Unable to save regenerating cakes",ex);
        }
    }
}
