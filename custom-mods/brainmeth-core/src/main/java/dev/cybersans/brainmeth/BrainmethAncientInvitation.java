package dev.cybersans.brainmeth;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.ThreadLocalRandom;

/**
 * A secret Common bounty invitation. Before the first award, half of Common
 * redemptions reveal it. Afterwards it is one of 39 equally likely prizes:
 * the original 38 Common shipments plus the invitation.
 */
public final class BrainmethAncientInvitation {
    private static final int ORIGINAL_COMMON_REWARDS = 38;
    private static MinecraftServer loadedServer;
    private static boolean discovered;

    private BrainmethAncientInvitation() {}

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-ancient-invitation.json");
    }

    private static void load(MinecraftServer server) {
        if (loadedServer == server) return;
        discovered = false;
        Path path = file(server);
        if (Files.exists(path)) {
            try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
                JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
                discovered = root.get("discovered").getAsBoolean();
            } catch (Exception e) {
                throw new IllegalStateException("Cannot read ancient invitation discovery state", e);
            }
        }
        loadedServer = server;
    }

    private static void save(MinecraftServer server) {
        JsonObject root = new JsonObject();
        root.addProperty("discovered", true);
        Path target = file(server);
        Path tmp = target.resolveSibling(target.getFileName().toString() + ".tmp");
        try {
            Files.writeString(tmp, root.toString() + "\n", StandardCharsets.UTF_8);
            try {
                Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Cannot save ancient invitation discovery state", e);
        }
    }

    public static boolean grantCommon(ServerPlayer player) {
        MinecraftServer server = player.getServer();
        load(server);
        boolean invitation = discovered
            ? ThreadLocalRandom.current().nextInt(ORIGINAL_COMMON_REWARDS + 1) == 0
            : ThreadLocalRandom.current().nextBoolean();

        if (invitation && !discovered) {
            try {
                save(server);
                discovered = true;
            } catch (RuntimeException e) {
                LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Cannot record ancient invitation discovery", e);
                player.sendSystemMessage(Component.literal("Bounty reward failed; please contact an admin."));
                return false;
            }
        }

        String table = invitation
            ? "brainmeth:bounties/rewards/common/ancient_invitation"
            : "brainmeth:bounties/rewards/common_pool";
        server.getCommands().performPrefixedCommand(
            server.createCommandSourceStack().withPermission(4).withSuppressedOutput(),
            "loot give " + player.getGameProfile().getName() + " loot " + table);
        return true;
    }
}
