package dev.cybersans.brainmeth;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.block.CropGrowEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Enormous trophy-only oak, ~114 blocks high, crown roughly 78 blocks wide.
 * Construction is incremental and persisted, never forces chunk loading,
 * and never overwrites non-replaceable player blocks.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethTreeOfLife {
    private static final int HEIGHT = 96;
    private static final int CROWN_RADIUS = 39;
    private static final int CROWN_CENTER = 88;
    private static final int CROWN_HEIGHT = 24;
    private static final int BUILD_BUDGET_PER_TICK = 650;
    private static final int MAX_PENDING = 32;
    private static final int MAX_PLAN_BLOCKS = 190_000;
    private static final Map<String, Set<Long>> saplings = new HashMap<>();
    private static final List<TreeJob> jobs = new ArrayList<>();
    private static MinecraftServer loadedServer;
    private static int tick;

    private record Placement(long packed, BlockState block) {}
    private static final class TreeJob {
        final String dimension;
        final BlockPos root;
        int progress;
        List<Placement> plan;
        TreeJob(String dimension, BlockPos root, int progress) {
            this.dimension = dimension;
            this.root = root;
            this.progress = progress;
        }
    }
    private BrainmethTreeOfLife() {}
    private static String dimension(ServerLevel level) { return level.dimension().location().toString(); }
    private static boolean tracked(ServerLevel level, BlockPos pos) {
        return saplings.getOrDefault(dimension(level), Set.of()).contains(pos.asLong());
    }
    private static String kind(ItemStack item) {
        CustomData data = item.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString("brainmeth_reward");
    }

    @SubscribeEvent
    public static void onRightClick(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() != InteractionHand.MAIN_HAND ||
            !(event.getEntity() instanceof ServerPlayer player) ||
            !(event.getLevel() instanceof ServerLevel level)) return;
        load(level.getServer());
        ItemStack item = event.getItemStack();
        BlockPos selected = event.getPos();
        if (item.is(Items.OAK_SAPLING) && kind(item).equals("tree_of_life")) {
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.SUCCESS);
            BlockPos at = level.getBlockState(selected).canBeReplaced() ?
                selected : selected.relative(event.getFace());
            if (allTracked() >= MAX_PENDING || !level.getWorldBorder().isWithinBounds(at) ||
                !level.mayInteract(player, at) || !level.getBlockState(at).canBeReplaced() ||
                !Blocks.OAK_SAPLING.defaultBlockState().canSurvive(level, at)) {
                player.displayClientMessage(Component.literal("Cannot plant the Tree of Life here."), true);
                return;
            }
            if (level.setBlock(at, Blocks.OAK_SAPLING.defaultBlockState(), 3)) {
                saplings.computeIfAbsent(dimension(level), k -> new HashSet<>()).add(at.asLong());
                save(level.getServer());
                item.shrink(1);
                player.displayClientMessage(Component.literal(
                    "Tree of Life planted. Right-click it with a full stack (64) of bonemeal."), true);
            }
            return;
        }
        if (item.is(Items.BONE_MEAL) && tracked(level, selected)) {
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.SUCCESS);
            if (!level.getBlockState(selected).is(Blocks.OAK_SAPLING)) {
                saplings.get(dimension(level)).remove(selected.asLong());
                save(level.getServer());
                player.displayClientMessage(Component.literal("Sapling is no longer present."), true);
                return;
            }
            if (item.getCount() < 64) {
                player.displayClientMessage(Component.literal("The Tree of Life requires 64 bonemeal at once."), true);
                return;
            }
            if (!jobs.isEmpty()) {
                player.displayClientMessage(Component.literal("Another enormous tree is growing. Try after it finishes."), true);
                return;
            }
            String problem = siteProblem(level, selected);
            if (problem != null) {
                player.displayClientMessage(Component.literal("Cannot grow Tree of Life: " + problem), true);
                return;
            }
            TreeJob job = new TreeJob(dimension(level), selected, 0);
            job.plan = makePlan(selected);
            if (job.plan.size() > MAX_PLAN_BLOCKS) {
                player.displayClientMessage(Component.literal("Tree block limit exceeded; no bone meal spent."), true);
                return;
            }
            jobs.add(job);
            saplings.get(dimension(level)).remove(selected.asLong());
            save(level.getServer());
            item.shrink(64);
            // Construction continues over many ticks; an interrupted build resumes from disk.
            player.displayClientMessage(Component.literal(
                "The Tree of Life awakens! About 114 blocks high, 78 blocks across."), false);
        }
    }

    @SubscribeEvent
    public static void onNaturalGrow(CropGrowEvent.Pre event) {
        if (event.getLevel() instanceof ServerLevel level &&
            event.getState().is(Blocks.OAK_SAPLING)) {
            load(level.getServer());
            if (tracked(level, event.getPos()))
                event.setResult(CropGrowEvent.Pre.Result.DO_NOT_GROW);
        }
    }

    @SubscribeEvent
    public static void onBreak(BlockEvent.BreakEvent event) {
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        load(level.getServer());
        Set<Long> stored = saplings.get(dimension(level));
        if (stored != null && stored.remove(event.getPos().asLong())) save(level.getServer());
    }

    private static int allTracked() {
        return saplings.values().stream().mapToInt(Set::size).sum();
    }

    private static String siteProblem(ServerLevel level, BlockPos root) {
        // Require entire footprint already loaded (no costly structure chunk generation).
        int minX = root.getX() - CROWN_RADIUS - 3;
        int maxX = root.getX() + CROWN_RADIUS + 3;
        int minZ = root.getZ() - CROWN_RADIUS - 3;
        int maxZ = root.getZ() + CROWN_RADIUS + 3;
        if (root.getY() + 118 >= level.getMaxBuildHeight() ||
            root.getY() < level.getMinBuildHeight() + 2) return "insufficient world height";
        for (int cx = minX >> 4; cx <= maxX >> 4; cx++) {
            for (int cz = minZ >> 4; cz <= maxZ >> 4; cz++) {
                if (!level.hasChunk(cx, cz)) return "nearby chunks not loaded; stay in the area";
            }
        }
        if (!level.getWorldBorder().isWithinBounds(new BlockPos(minX, root.getY(), minZ)) ||
            !level.getWorldBorder().isWithinBounds(new BlockPos(maxX, root.getY(), maxZ)))
            return "too close to world border";
        // Do not push through artificial builds or cave ceilings.
        for (int y = 1; y < HEIGHT + 5; y++) {
            for (int dx = -3; dx <= 3; dx++) for (int dz = -3; dz <= 3; dz++) {
                if (dx * dx + dz * dz > 9) continue;
                BlockPos test = root.offset(dx, y, dz);
                BlockState state = level.getBlockState(test);
                if (!state.isAir() && !state.canBeReplaced() && !state.is(Blocks.OAK_LEAVES))
                    return "trunk would collide with an existing structure";
            }
        }
        return null;
    }

    private static void put(Map<Long, BlockState> blocks, BlockPos root,
                            int dx, int dy, int dz, BlockState state) {
        blocks.put(root.offset(dx, dy, dz).asLong(), state);
    }

    private static double noise(int x, int y, int z) {
        double a = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719) * 43758.5453;
        return a - Math.floor(a);
    }

    private static List<Placement> makePlan(BlockPos root) {
        // Linked map avoids duplicates. Wood is overlaid after all foliage.
        Map<Long, BlockState> blocks = new LinkedHashMap<>();
        BlockState leaves = Blocks.OAK_LEAVES.defaultBlockState().setValue(LeavesBlock.PERSISTENT, true);
        BlockState vertical = Blocks.OAK_LOG.defaultBlockState().setValue(BlockStateProperties.AXIS, Direction.Axis.Y);

        // Massive organic flattened ellipsoid. Uneven surface, small air pockets.
        for (int y = CROWN_CENTER - CROWN_HEIGHT; y <= CROWN_CENTER + CROWN_HEIGHT; y++) {
            double vy = (y - CROWN_CENTER) / (double) CROWN_HEIGHT;
            for (int x = -CROWN_RADIUS; x <= CROWN_RADIUS; x++) {
                for (int z = -CROWN_RADIUS; z <= CROWN_RADIUS; z++) {
                    double r = (double)(x * x + z * z) / (CROWN_RADIUS * CROWN_RADIUS);
                    double edge = r + vy * vy;
                    if (edge > 1.0 + (noise(x / 3, y / 3, z / 3) - 0.5) * 0.10) continue;
                    if (noise(x, y, z) < 0.022 && edge > 0.60) continue;
                    put(blocks, root, x, y, z, leaves);
                }
            }
        }
        // Satellite crowns provide an irregular spread at mid-level.
        for (int b = 0; b < 12; b++) {
            double angle = (Math.PI * 2 * b / 12.0) + (b % 3) * 0.18;
            int bx = (int)Math.round(Math.cos(angle) * (22 + b % 5));
            int bz = (int)Math.round(Math.sin(angle) * (22 + b % 5));
            int by = 60 + (b * 7) % 22;
            int radius = 9 + b % 5;
            for (int x = -radius; x <= radius; x++) for (int z = -radius; z <= radius; z++)
                for (int y = -7; y <= 9; y++) {
                    double ellipsoid = (double)(x*x + z*z) / (radius*radius) + (y*y)/81.0;
                    if (ellipsoid <= 1.0 && noise(x + bx, y + by, z + bz) > 0.035)
                        put(blocks, root, bx+x, by+y, bz+z, leaves);
                }
        }

        // Radiating thick roots, trunk 10 blocks wide at base tapering upward.
        for (int y = 0; y < HEIGHT; y++) {
            int radius = y < 18 ? 5 : y < 52 ? 4 : y < 76 ? 3 : 2;
            for (int x = -radius; x <= radius; x++) for (int z = -radius; z <= radius; z++)
                if (x*x + z*z <= radius*radius + 1) put(blocks, root, x, y, z, vertical);
        }
        for (int b = 0; b < 16; b++) {
            double angle = Math.PI * 2 * b / 16.0;
            double ux = Math.cos(angle), uz = Math.sin(angle);
            int begin = 48 + (b*11)%31;
            int length = 26 + (b%4)*3;
            BlockState branch = Blocks.OAK_LOG.defaultBlockState().setValue(BlockStateProperties.AXIS,
                Math.abs(ux) > Math.abs(uz) ? Direction.Axis.X : Direction.Axis.Z);
            for (int s = 0; s <= length; s++) {
                int x = (int)Math.round(ux * s);
                int z = (int)Math.round(uz * s);
                int y = begin + (int)Math.round(s * (0.46 + (b%3)*0.08));
                int thick = s < 9 ? 3 : s < 21 ? 2 : 1;
                for (int a=-thick; a<=thick; a++) for (int d=-thick; d<=thick; d++)
                    if (a*a + d*d <= thick*thick+1)
                        put(blocks, root, x+a, y, z+d, branch);
            }
        }
        for (int b=0;b<8;b++) {
            double angle = Math.PI * b / 4;
            double ux = Math.cos(angle), uz = Math.sin(angle);
            for (int i=3;i<=17;i++) for(int w=-1;w<=1;w++)
                put(blocks,root,(int)Math.round(ux*i)+(int)Math.round(uz*w),
                    Math.min(5,i/5), (int)Math.round(uz*i)-(int)Math.round(ux*w),vertical);
        }
        if (blocks.size() > MAX_PLAN_BLOCKS) throw new IllegalStateException("Giant tree exceeds block cap");
        List<Placement> list = new ArrayList<>(blocks.size());
        blocks.forEach((packed, state) -> list.add(new Placement(packed, state)));
        return list;
    }

    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        load(server);
        if (jobs.isEmpty()) return;
        TreeJob job = jobs.get(0);
        ServerLevel level = server.getAllLevels().stream()
            .filter(l -> dimension(l).equals(job.dimension)).findFirst().orElse(null);
        if (level == null) return;
        if (job.plan == null) job.plan = makePlan(job.root);
        int changes = 0, advanced = 0;
        while (job.progress < job.plan.size() && changes < BUILD_BUDGET_PER_TICK) {
            Placement entry = job.plan.get(job.progress);
            BlockPos at = BlockPos.of(entry.packed);
            if (!level.hasChunkAt(at)) break; // Pause until player loads area, no force-loading.
            job.progress++;
            advanced++;
            BlockState existing = level.getBlockState(at);
            // Never touch solid blocks, player builds, fluids, or block entities.
            if (existing.isAir() || existing.canBeReplaced() || existing.is(Blocks.OAK_LEAVES) ||
                (at.equals(job.root) && existing.is(Blocks.OAK_SAPLING))) {
                if (level.setBlock(at, entry.block, 2)) changes++;
            }
        }
        if (job.progress >= job.plan.size()) {
            jobs.remove(0);
            save(server);
            server.getPlayerList().broadcastSystemMessage(
                Component.literal("A Tree of Life has finished growing!"), false);
        } else if (advanced > 0 && ++tick % 20 == 0) {
            save(server); // Crash-resumable cursor, not a giant snapshot.
        }
    }

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT)
            .resolve("brainmeth-life-trees.json");
    }

    private static void load(MinecraftServer server) {
        if (loadedServer == server) return;
        loadedServer = server;
        saplings.clear();
        jobs.clear();
        tick = 0;
        if (!Files.isRegularFile(file(server))) return;
        try (var reader = Files.newBufferedReader(file(server), StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            JsonObject sprouts = root.getAsJsonObject("saplings");
            if (sprouts != null) for (String dimension : sprouts.keySet()) {
                Set<Long> values = new HashSet<>();
                for (var pos : sprouts.getAsJsonArray(dimension)) values.add(pos.getAsLong());
                saplings.put(dimension, values);
            }
            JsonArray scheduled = root.getAsJsonArray("jobs");
            if (scheduled != null) for (var element : scheduled) {
                JsonObject object = element.getAsJsonObject();
                jobs.add(new TreeJob(object.get("dimension").getAsString(),
                    BlockPos.of(object.get("root").getAsLong()), object.get("progress").getAsInt()));
            }
        } catch (Exception ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error(
                "Cannot load Tree of Life state: leaving it untouched", ex);
        }
    }

    private static void save(MinecraftServer server) {
        JsonObject root = new JsonObject(), sprouts = new JsonObject();
        saplings.forEach((dimension, values) -> {
            JsonArray positions = new JsonArray();
            for (long packed : values) positions.add(packed);
            sprouts.add(dimension, positions);
        });
        root.add("saplings", sprouts);
        JsonArray pending = new JsonArray();
        for (TreeJob job : jobs) {
            JsonObject value = new JsonObject();
            value.addProperty("dimension",job.dimension);
            value.addProperty("root", job.root.asLong());
            value.addProperty("progress",job.progress);
            pending.add(value);
        }
        root.add("jobs", pending);
        Path path = file(server), tmp = path.resolveSibling(path.getFileName()+".tmp");
        try {
            Files.writeString(tmp, root.toString()+"\n", StandardCharsets.UTF_8);
            try { Files.move(tmp,path,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE); }
            catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                Files.move(tmp,path,StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error(
                "Cannot save Tree of Life state", ex);
        }
    }
}
