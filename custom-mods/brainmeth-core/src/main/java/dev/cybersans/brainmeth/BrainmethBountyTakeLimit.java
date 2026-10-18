package dev.cybersans.brainmeth;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.LevelResource;
import org.slf4j.LoggerFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Enforces three bounty papers taken per player per Minecraft day across all
 * boards containing a Brainmeth decree, irrespective of redemption/discard. */
public final class BrainmethBountyTakeLimit {
    private static final int LIMIT = 3;
    private static final Map<UUID, Record> TAKEN = new HashMap<>();
    private static MinecraftServer loaded;
    private record Record(long day, int count) {}
    private BrainmethBountyTakeLimit() {}

    public static boolean isBrainmethBoard(AbstractContainerMenu menu, int slotIndex) {
        if (!menu.getClass().getName().equals("io.ejekta.bountiful.content.gui.BoardScreenHandler")
                || slotIndex < 0 || slotIndex >= 21) return false;
        Slot slot = menu.getSlot(slotIndex);
        if (!slot.getClass().getName().equals("io.ejekta.bountiful.content.gui.BoardBountySlot")
                || slot.getItem().isEmpty()) return false;
        // Bountiful's GUI has 21 bounty slots followed by 3 decree slots.
        for (int i = 21; i < 24; i++) {
            ItemStack decree = menu.getSlot(i).getItem();
            if (!decree.isEmpty() && decree.getComponentsPatch().toString().contains("brainmeth_board")) return true;
        }
        return false;
    }

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-bounty-take-limits.json");
    }
    private static void load(MinecraftServer server) {
        if (loaded == server) return;
        loaded = server;
        TAKEN.clear();
        if (!Files.isRegularFile(file(server))) return;
        try (var reader = Files.newBufferedReader(file(server), StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            for (var entry : root.entrySet()) {
                JsonObject obj = entry.getValue().getAsJsonObject();
                TAKEN.put(UUID.fromString(entry.getKey()), new Record(obj.get("day").getAsLong(), obj.get("count").getAsInt()));
            }
        } catch (Exception e) {
            LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Could not read bounty take limits; rejecting acquisitions until repaired", e);
            // Do not silently reset players' quota if persistence is corrupted.
            throw new IllegalStateException("Bounty take limits unavailable", e);
        }
    }

    private static long day(ServerPlayer player) {
        // Minecraft day counter advances with /time and sleeping.
        return Math.floorDiv(player.serverLevel().getDayTime(), 24000L);
    }
    public static boolean mayTake(ServerPlayer player) {
        load(player.getServer());
        long today = day(player);
        Record r = TAKEN.get(player.getUUID());
        int count = r == null || r.day != today ? 0 : r.count;
        if (count < LIMIT) return true;
        player.sendSystemMessage(Component.literal("Brainmeth bounty limit: 3 contracts per Minecraft day. Try again tomorrow."));
        return false;
    }
    public static void didTake(ServerPlayer player) {
        MinecraftServer server = player.getServer();
        load(server);
        long today = day(player);
        Record r = TAKEN.get(player.getUUID());
        int count = r == null || r.day != today ? 0 : r.count;
        TAKEN.put(player.getUUID(), new Record(today, Math.min(LIMIT, count + 1)));
        JsonObject root = new JsonObject();
        for (var entry : TAKEN.entrySet()) {
            if (entry.getValue().day != today) continue; // discard old-day records
            JsonObject obj = new JsonObject();
            obj.addProperty("day", entry.getValue().day);
            obj.addProperty("count", entry.getValue().count);
            root.add(entry.getKey().toString(), obj);
        }
        Path target = file(server), tmp = target.resolveSibling(target.getFileName() + ".tmp");
        try {
            Files.writeString(tmp, root.toString() + "\n", StandardCharsets.UTF_8);
            try { Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException e) { Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING); }
        } catch (Exception e) {
            LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Could not save bounty take limits", e);
        }
        player.sendSystemMessage(Component.literal("Brainmeth contracts taken today: " + Math.min(LIMIT, count + 1) + "/3"));
    }
}
