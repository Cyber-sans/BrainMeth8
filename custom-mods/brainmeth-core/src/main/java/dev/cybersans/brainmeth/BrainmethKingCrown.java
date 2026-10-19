package dev.cybersans.brainmeth;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.zip.GZIPInputStream;

/**
 * One persistent Crown of Brainmeth across this world, transferable by ordinary
 * item mechanics. Changes of owner are announced once, with durable catch-up
 * messages for players who were offline. Only online player inventories and
 * ender chests are checked; no world-wide entity scan or player-NBT writes.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethKingCrown {
    private static final String REWARD = "king_of_brainmeth_crown";
    private static final String ID_TAG = "brainmeth_crown_id";
    private static MinecraftServer loadedServer;
    private static boolean issued;
    private static String crownId;
    private static boolean activated;
    private static UUID lastHolder;
    private static String lastHolderName;
    private static int lastEventId;
    private static int elapsed;
    private static final List<Notice> notices = new ArrayList<>();
    private static final Map<UUID, Integer> seen = new HashMap<>();

    private record Notice(int id, String message) {}
    private record Location(ServerPlayer player, net.minecraft.world.Container inventory, int slot, ItemStack stack) {}

    private BrainmethKingCrown() {}

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-crown.json");
    }

    private static void load(MinecraftServer server) {
        if (loadedServer == server) return;
        // Never silently reuse state from a different world (test vs production).
        issued = false;
        crownId = null;
        activated = false;
        lastHolder = null;
        lastHolderName = "";
        lastEventId = 0;
        elapsed = 0;
        notices.clear();
        seen.clear();
        loadedServer = server;
        Path path = file(server);
        if (!Files.exists(path)) {
            // Existing pre-upgrade crowns might be in an offline player's save.
            // Avoid minting another one just because their owner is offline.
            adoptLegacyPlayerData(server);
            if (issued) save(server);
            return;
        }
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            issued = root.get("issued").getAsBoolean();
            if (root.has("crownId") && !root.get("crownId").isJsonNull())
                crownId = root.get("crownId").getAsString();
            activated = root.has("activated") ? root.get("activated").getAsBoolean() : crownId != null;
            if (root.has("lastHolder") && !root.get("lastHolder").isJsonNull())
                lastHolder = UUID.fromString(root.get("lastHolder").getAsString());
            lastHolderName = root.has("lastHolderName") ? root.get("lastHolderName").getAsString() : "";
            lastEventId = root.get("lastEventId").getAsInt();
            for (var item : root.getAsJsonArray("notices")) {
                JsonObject obj = item.getAsJsonObject();
                notices.add(new Notice(obj.get("id").getAsInt(), obj.get("message").getAsString()));
            }
            for (var item : root.getAsJsonObject("seen").entrySet())
                seen.put(UUID.fromString(item.getKey()), item.getValue().getAsInt());
        } catch (Exception e) {
            throw new IllegalStateException("Cannot load the unique Brainmeth Crown state; refusing to create a second crown", e);
        }
    }

    private static void adoptLegacyPlayerData(MinecraftServer server) {
        Path players = server.getWorldPath(LevelResource.ROOT).resolve("playerdata");
        if (!Files.isDirectory(players)) return;
        // Read gzip player NBT only; do not modify player saves. Existing
        // crowns are identified by the uniquely tagged bounty reward ID.
        byte[] marker = REWARD.getBytes(StandardCharsets.UTF_8);
        try (var files = Files.list(players)) {
            for (Path p : files.filter(f -> f.getFileName().toString().endsWith(".dat")).sorted().toList()) {
                byte[] raw;
                try (InputStream in = new GZIPInputStream(Files.newInputStream(p))) {
                    raw = in.readAllBytes();
                }
                if (indexOf(raw, marker) < 0) continue;
                issued = true;
                if (lastHolder == null) {
                    lastHolder = UUID.fromString(p.getFileName().toString().replace(".dat", ""));
                    lastHolderName = lastHolder.toString();
                }
                LoggerFactory.getLogger(BrainmethCore.MOD_ID).info("Found a legacy Crown of Brainmeth in player save {}", p.getFileName());
            }
        } catch (Exception ex) {
            throw new IllegalStateException("Unable to inspect existing Crown of Brainmeth player saves", ex);
        }
    }

    private static int indexOf(byte[] bytes, byte[] pattern) {
        outer: for (int i = 0; i <= bytes.length - pattern.length; i++) {
            for (int j = 0; j < pattern.length; j++)
                if (bytes[i + j] != pattern[j]) continue outer;
            return i;
        }
        return -1;
    }

    private static void save(MinecraftServer server) {
        JsonObject root = new JsonObject();
        root.addProperty("version", 1);
        root.addProperty("issued", issued);
        if (crownId != null) root.addProperty("crownId", crownId);
        root.addProperty("activated", activated);
        if (lastHolder != null) root.addProperty("lastHolder", lastHolder.toString());
        root.addProperty("lastHolderName", lastHolderName);
        root.addProperty("lastEventId", lastEventId);
        JsonArray list = new JsonArray();
        for (Notice notice : notices) {
            JsonObject entry = new JsonObject();
            entry.addProperty("id", notice.id());
            entry.addProperty("message", notice.message());
            list.add(entry);
        }
        root.add("notices", list);
        JsonObject acknowledgements = new JsonObject();
        for (var entry : seen.entrySet()) acknowledgements.addProperty(entry.getKey().toString(), entry.getValue());
        root.add("seen", acknowledgements);
        Path target = file(server);
        Path tmp = target.resolveSibling(target.getFileName().toString() + ".tmp");
        try {
            Files.writeString(tmp, root.toString() + "\n", StandardCharsets.UTF_8);
            try {
                Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException ex) {
                Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ex) {
            throw new IllegalStateException("Unable to persist unique Crown of Brainmeth ownership", ex);
        }
    }

    /**
     * A Mythic crown bounty is a forced transfer, NOT a second crown mint.
     * The previous crown ID is revoked atomically in world state, including
     * crowns held by offline players or hidden in unloaded storage.
     * Obsolete physical items are removed when their inventories are loaded.
     */
    public static boolean grantThroughBounty(ServerPlayer winner) {
        MinecraftServer server = winner.getServer();
        load(server);

        // Roll the SAME loot table used by the original reward so the enchanted
        // Netherite Crown retains every existing enchantment, name and lore.
        // Unlike /loot give, this lets us assign the unique ID BEFORE delivery.
        final ItemStack prize;
        try {
            ResourceKey<LootTable> key = ResourceKey.create(Registries.LOOT_TABLE,
                ResourceLocation.parse("brainmeth:rewards/rare/king_of_brainmeth_crown"));
            LootTable table = server.reloadableRegistries().getLootTable(key);
            List<ItemStack> generated = table.getRandomItems(
                new LootParams.Builder(winner.serverLevel()).create(LootContextParamSets.EMPTY));
            if (generated.size() != 1 || generated.get(0).getCount() != 1
                    || !isCrown(generated.get(0))) {
                throw new IllegalStateException("Crown loot table must generate exactly one tagged Crown");
            }
            prize = generated.get(0);
        } catch (RuntimeException ex) {
            LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Failed to roll Crown of Brainmeth bounty", ex);
            winner.sendSystemMessage(Component.literal("Crown reward failed; please contact an admin.")
                .withStyle(ChatFormatting.RED));
            return false;
        }

        // Save enough state to roll back a failed disk write. Never invalidate
        // the existing crown if ownership cannot first be persisted.
        boolean oldIssued = issued, oldActivated = activated;
        String oldId = crownId, oldHolderName = lastHolderName;
        UUID oldHolder = lastHolder;
        int oldEvent = lastEventId, oldNoticeCount = notices.size();
        Map<UUID, Integer> oldSeen = new HashMap<>(seen);

        String newId = UUID.randomUUID().toString();
        tag(prize, newId);
        issued = true;
        activated = true;
        crownId = newId;
        lastHolder = winner.getUUID();
        lastHolderName = winner.getGameProfile().getName();

        String message = null;
        if (!winner.getUUID().equals(oldHolder)) {
            message = winner.getGameProfile().getName()
                + (oldIssued ? " has stolen the Crown of Brainmeth!"
                             : " has claimed the Crown of Brainmeth!");
            notices.add(new Notice(++lastEventId, message));
            for (ServerPlayer player : server.getPlayerList().getPlayers())
                seen.put(player.getUUID(), lastEventId);
        }
        try {
            save(server);
        } catch (RuntimeException ex) {
            issued = oldIssued;
            activated = oldActivated;
            crownId = oldId;
            lastHolder = oldHolder;
            lastHolderName = oldHolderName;
            lastEventId = oldEvent;
            while (notices.size() > oldNoticeCount) notices.remove(notices.size() - 1);
            seen.clear();
            seen.putAll(oldSeen);
            LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Crown bounty transfer not persisted", ex);
            winner.sendSystemMessage(Component.literal("Crown transfer failed; please contact an admin.")
                .withStyle(ChatFormatting.RED));
            return false;
        }

        // Immediately confiscate every obsolete crown from online players,
        // including equipment and Ender Chests. Offline copies are removed on
        // login; unloaded chests are inert because the old ID is revoked.
        for (ServerPlayer player : server.getPlayerList().getPlayers()) removeRevoked(player);

        if (!winner.getInventory().add(prize)) {
            // The reward is still uniquely identified even if the winner's
            // inventory was full, and can be picked up through normal play.
            winner.drop(prize, false);
        }
        winner.containerMenu.broadcastChanges();
        if (message != null) {
            Component announcement = Component.literal(message).withStyle(ChatFormatting.GOLD);
            for (ServerPlayer player : server.getPlayerList().getPlayers())
                player.sendSystemMessage(announcement);
        }
        return true;
    }

    private static void removeRevoked(ServerPlayer player) {
        if (!activated || crownId == null) return;
        removeRevoked(player, player.getInventory());
        removeRevoked(player, player.getEnderChestInventory());
    }

    private static void removeRevoked(ServerPlayer player, net.minecraft.world.Container inventory) {
        for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
            ItemStack candidate = inventory.getItem(slot);
            if (!isCrown(candidate) || isValidCrown(candidate)) continue;
            inventory.setItem(slot, ItemStack.EMPTY);
            LoggerFactory.getLogger(BrainmethCore.MOD_ID).info(
                "Recalled obsolete Crown of Brainmeth from {}", player.getGameProfile().getName());
        }
        player.containerMenu.broadcastChanges();
    }

    private static boolean isCrown(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && REWARD.equals(data.copyTag().getString("brainmeth_reward"));
    }

    public static boolean isValidCrown(ItemStack stack) {
        if (!isCrown(stack) || crownId == null) return false;
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return crownId.equals(data.copyTag().getString(ID_TAG));
    }

    private static String identity(ItemStack stack) {
        CustomData data = stack.get(DataComponents.CUSTOM_DATA);
        return data == null ? "" : data.copyTag().getString(ID_TAG);
    }

    private static void tag(ItemStack stack) {
        tag(stack, crownId);
    }

    private static void tag(ItemStack stack, String id) {
        CompoundTag tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(ID_TAG, id);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) return;
        load(player.getServer());
        // The offline former owner loses their revoked physical helmet before
        // seeing the transfer notice. No offline player-NBT file is rewritten.
        removeRevoked(player);
        int checkpoint = seen.getOrDefault(player.getUUID(), 0);
        for (Notice notice : notices) {
            if (notice.id() > checkpoint)
                player.sendSystemMessage(Component.literal(notice.message()).withStyle(ChatFormatting.GOLD));
        }
        if (checkpoint < lastEventId) {
            seen.put(player.getUUID(), lastEventId);
            save(player.getServer());
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        load(server);
        if (++elapsed % 20 != 0) return;

        List<ServerPlayer> players = new ArrayList<>(server.getPlayerList().getPlayers());
        for (ServerPlayer player : players) removeRevoked(player);
        // Prefer the previous owner if identical crowns appear via cloning.
        players.sort(Comparator.comparingInt(p -> p.getUUID().equals(lastHolder) ? 0 : 1));
        List<Location> found = new ArrayList<>();
        for (ServerPlayer player : players) {
            scan(player, player.getInventory(), found);
            scan(player, player.getEnderChestInventory(), found);
        }

        Location authentic = null;
        for (Location loc : found) {
            if (crownId != null && crownId.equals(identity(loc.stack()))) {
                authentic = loc;
                break;
            }
        }
        if (authentic == null && !found.isEmpty() && crownId == null) {
            // Upgrade an existing legacy crown in place, while preserving its
            // enchantments and all other item components.
            issued = true;
            crownId = UUID.randomUUID().toString();
            authentic = found.get(0);
            tag(authentic.stack());
            activated = true;
            save(server);
        }
        if (authentic == null && issued && crownId != null && !activated) {
            // The first crown awarded by the new system is created by a loot
            // table without an ID; tag it on its first observed acquisition.
            for (Location loc : found) {
                if (identity(loc.stack()).isEmpty()) {
                    authentic = loc;
                    tag(authentic.stack());
                    activated = true;
                    save(server);
                    break;
                }
            }
        }
        // Remove all unauthorised tagged helmets, including when the real
        // crown is currently in a chest, dropped, or carried by an offline player.
        for (Location loc : found) {
            if (loc != authentic) {
                loc.inventory().setItem(loc.slot(), ItemStack.EMPTY);
                LoggerFactory.getLogger(BrainmethCore.MOD_ID).warn(
                    "Removed duplicate Crown of Brainmeth from {}", loc.player().getGameProfile().getName());
            }
        }
        if (authentic != null) {
            if (!activated) {
                activated = true;
                save(server);
            }
            UUID owner = authentic.player().getUUID();
            if (!owner.equals(lastHolder)) {
                String thief = authentic.player().getGameProfile().getName();
                if (lastHolder != null) {
                    String message = thief + " has stolen the Crown of Brainmeth!";
                    int id = ++lastEventId;
                    notices.add(new Notice(id, message));
                    save(server);
                    for (ServerPlayer p : server.getPlayerList().getPlayers()) {
                        p.sendSystemMessage(Component.literal(message).withStyle(ChatFormatting.GOLD));
                        seen.put(p.getUUID(), id);
                    }
                }
                lastHolder = owner;
                lastHolderName = thief;
                save(server);
            }
        }

        for (ServerPlayer player : players) {
            ItemStack helmet = player.getInventory().armor.get(3);
            if (!isValidCrown(helmet)) continue;
            player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 120, 1, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 120, 0, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 120, 0, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, true));
        }
    }

    private static void scan(ServerPlayer player, net.minecraft.world.Container inventory, List<Location> found) {
        for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
            ItemStack stack = inventory.getItem(slot);
            if (isCrown(stack))
                found.add(new Location(player, inventory, slot, stack));
        }
    }
}
