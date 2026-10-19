package dev.cybersans.brainmeth;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Exactly one random real-world UK time each calendar day for a Crown reminder.
 * The scheduled instant and its completion survive restarts. Messages are
 * broadcast ONLY to people online at that instant; no replay on login.
 */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethCrownTaunts {
    private static final ZoneId UK = ZoneId.of("Europe/London");
    private static final int SPECIAL_RANDOM_PLAYER = 7;
    private static final int NAME_METH = 9;
    private static final String[] TAUNTS = {
        "The rest of you, bend the knee.",
        "You are below them.",
        "They stand above all.",
        "Everybody else smells of poo.",
        "Lower your heads.",
        "Try and take it back.",
        "...for now",
        "", // Random online non-owner: <name> is not.
        "Stillwater, Iranian Giggle.",
        "", // Crown holder name substitution: More like <holder>-meth.
        "Learn his name.",
        "Say his name.",
        "Remember his name.",
        "Inferior lower citizens."
    };

    private static MinecraftServer activeServer;
    private static String scheduledDay = "";
    private static long scheduledEpoch;
    private static boolean fired;
    private static int ticks;

    private BrainmethCrownTaunts() {}

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-crown-daily-taunt.json");
    }

    private static void load(MinecraftServer server) {
        if (activeServer == server) return;
        // Never share the test world's schedule with the production server.
        activeServer = server;
        scheduledDay = "";
        scheduledEpoch = 0;
        fired = false;
        ticks = 0;
        Path path = file(server);
        if (!Files.exists(path)) return;
        try (var reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            JsonObject obj = JsonParser.parseReader(reader).getAsJsonObject();
            scheduledDay = obj.get("day").getAsString();
            scheduledEpoch = obj.get("epoch").getAsLong();
            fired = obj.get("fired").getAsBoolean();
            LocalDate.parse(scheduledDay);
            if (scheduledEpoch <= 0) throw new IllegalArgumentException("Invalid reminder time");
            // If the chosen instant elapsed while the server was stopped,
            // that day's broadcast was missed; NEVER replay it on startup.
            long now = Instant.now().getEpochSecond();
            if (!fired && now >= scheduledEpoch) {
                fired = true;
                save(server);
            }
        } catch (Exception e) {
            throw new IllegalStateException("Unable to restore the daily Crown reminder schedule", e);
        }
    }

    private static void save(MinecraftServer server) {
        JsonObject obj = new JsonObject();
        obj.addProperty("day", scheduledDay);
        obj.addProperty("epoch", scheduledEpoch);
        obj.addProperty("fired", fired);
        Path target = file(server);
        Path temp = target.resolveSibling(target.getFileName() + ".tmp");
        try {
            Files.writeString(temp, obj.toString() + "\n", StandardCharsets.UTF_8);
            try {
                Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temp, target, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            throw new IllegalStateException("Could not save daily Crown reminder schedule", e);
        }
    }

    /**
     * Choose uniformly among the remaining seconds of the current UK day.
     * Following days use the entire 23/24/25-hour UK day, including DST.
     * A server restarted after yesterday's time does not replay yesterday.
     */
    private static void scheduleToday(MinecraftServer server, LocalDate date, long now) {
        long midnightTomorrow = date.plusDays(1).atStartOfDay(UK).toEpochSecond();
        long earliest = now + 1;
        // At the exact last second of the day, use that second rather
        // than trying to choose a time outside the UK calendar day.
        scheduledEpoch = earliest < midnightTomorrow
            ? ThreadLocalRandom.current().nextLong(earliest, midnightTomorrow)
            : now;
        scheduledDay = date.toString();
        fired = false;
        save(server);
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        load(server);
        if (++ticks % 20 != 0) return; // Once per second, not per entity.
        long now = Instant.now().getEpochSecond();
        LocalDate today = Instant.ofEpochSecond(now).atZone(UK).toLocalDate();
        if (!today.toString().equals(scheduledDay)) {
            scheduleToday(server, today, now);
        }
        if (fired || now < scheduledEpoch) return;

        // Mark the date complete before broadcasting, preventing duplicates
        // after restart and ruling out catch-up notifications to late joiners.
        fired = true;
        save(server);

        // The random daily clock always fires, but the taunt and location
        // reveal require the legitimate current owner to be wearing the crown
        // at that exact moment. It will NOT retry if the crown is unequipped.
        ServerPlayer wearer = BrainmethKingCrown.currentWearingHolder(server);
        if (wearer == null) return;
        String holder = wearer.getGameProfile().getName();
        List<ServerPlayer> online = server.getPlayerList().getPlayers();

        UUID holderId = wearer.getUUID();
        List<ServerPlayer> nonOwners = online.stream()
            .filter(p -> !p.getUUID().equals(holderId))
            .toList();

        int selected = ThreadLocalRandom.current().nextInt(TAUNTS.length);
        // Do not name the crown holder as the player who DOESN'T hold it.
        if (selected == SPECIAL_RANDOM_PLAYER && nonOwners.isEmpty()) {
            selected = ThreadLocalRandom.current().nextInt(TAUNTS.length - 1);
            if (selected >= SPECIAL_RANDOM_PLAYER) selected++;
        }

        String suffix;
        if (selected == SPECIAL_RANDOM_PLAYER) {
            ServerPlayer target = nonOwners.get(ThreadLocalRandom.current().nextInt(nonOwners.size()));
            suffix = target.getGameProfile().getName() + " is not.";
        } else if (selected == NAME_METH) {
            suffix = "More like " + holder + "-meth.";
        } else {
            suffix = TAUNTS[selected];
        }
        Component message = Component.literal(
            holder + " still holds the Crown of Brainmeth. " + suffix
        ).withStyle(ChatFormatting.GOLD);
        // This is deliberately NOT part of BrainmethKingCrown's persisted
        // theft notices. Anyone offline at broadcast time simply misses it.
        server.getPlayerList().broadcastSystemMessage(message, false);

        // Only reveal in-game coordinates at the same daily instant as the
        // taunt. Include the dimension so Nether/End locations aren't
        // misrepresented as Overworld coordinates.
        String dimension = wearer.level().dimension().equals(Level.OVERWORLD) ? "Overworld"
            : wearer.level().dimension().equals(Level.NETHER) ? "Nether"
            : wearer.level().dimension().equals(Level.END) ? "End"
            : wearer.level().dimension().location().toString();
        var pos = wearer.blockPosition();
        String location = "The king is ruling at [" + pos.getX() + ", "
            + pos.getY() + ", " + pos.getZ() + "] (" + dimension + ").";
        server.getPlayerList().broadcastSystemMessage(
            Component.literal(location).withStyle(ChatFormatting.YELLOW), false);
    }
}
