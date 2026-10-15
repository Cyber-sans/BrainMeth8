package dev.cybersans.brainmeth;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.world.BossEvent;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.ResolverStyle;
import java.time.zone.ZoneRules;
import java.util.List;

/**
 * Dedicated-server in-game release scheduler. The world is already running:
 * a real-world instant triggers the existing Brainmeth datapack release function.
 *
 * No independent countdown tick state: if the server restarts or stalls, the
 * deadline is checked against the actual wall clock on the next server tick.
 */
@Mod(BrainmethCore.MOD_ID)
public final class BrainmethCore {
    public static final String MOD_ID = "brainmeth_core";
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final ZoneId UK = ZoneId.of("Europe/London");
    private static final DateTimeFormatter INPUT = DateTimeFormatter.ofPattern("uuuu-MM-dd HH:mm")
        .withResolverStyle(ResolverStyle.STRICT);
    private static final DateTimeFormatter OUTPUT = DateTimeFormatter.ofPattern("EEE d MMM yyyy, HH:mm z");
    private static final long[] ANNOUNCEMENTS = {3600, 1800, 600, 300, 60, 30, 10, 5, 4, 3, 2, 1};

    private static MinecraftServer activeServer;
    private static Long launchEpoch;
    private static long scheduledAtEpoch;
    private static long priorRemaining = Long.MIN_VALUE;
    private static int ticks;
    private static ServerBossEvent bar;

    public BrainmethCore(IEventBus modBus, ModContainer container) {
        NeoForge.EVENT_BUS.addListener(BrainmethCore::registerCommands);
        NeoForge.EVENT_BUS.addListener(BrainmethCore::onServerTick);
        LOGGER.info("Brainmeth launch scheduler registered; no launch is scheduled by default");
    }

    private static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(
            Commands.literal("launch")
                .requires(s -> s.hasPermission(2))
                .executes(ctx -> showStatus(ctx.getSource()))
                .then(Commands.literal("status").executes(ctx -> showStatus(ctx.getSource())))
                .then(Commands.literal("schedule")
                    .then(Commands.argument("when", StringArgumentType.greedyString())
                        .suggests((ctx, builder) -> {
                            LocalDate today = LocalDate.now(UK);
                            builder.suggest(today.plusDays(1) + " 18:00");
                            builder.suggest(today.plusDays(2) + " 18:00");
                            return builder.buildFuture();
                        })
                        .executes(ctx -> schedule(ctx.getSource(), StringArgumentType.getString(ctx, "when")))))
                .then(Commands.literal("reschedule")
                    .then(Commands.argument("when", StringArgumentType.greedyString())
                        .executes(ctx -> schedule(ctx.getSource(), StringArgumentType.getString(ctx, "when")))))
                .then(Commands.literal("cancel").executes(ctx -> cancel(ctx.getSource())))
                .then(Commands.literal("now").executes(ctx -> releaseNow(ctx.getSource())))
                .then(Commands.literal("help").executes(ctx -> help(ctx.getSource())))
        );
    }

    private static int help(CommandSourceStack source) {
        source.sendSuccess(() -> Component.literal(
            "Launch: /launch schedule 2026-10-16 18:00 | /launch status | /launch cancel | /launch now"
        ), false);
        return 1;
    }

    private static int showStatus(CommandSourceStack source) {
        ensureLoaded(source.getServer());
        if (!isWaiting(source.getServer())) {
            source.sendSuccess(() -> Component.literal("Brainmeth world has already launched."), false);
        } else if (launchEpoch == null) {
            source.sendSuccess(() -> Component.literal("Waiting room active. No release scheduled. Use /launch schedule YYYY-MM-DD HH:mm (UK time)."), false);
        } else {
            long seconds = Math.max(0, launchEpoch - Instant.now().getEpochSecond());
            source.sendSuccess(() -> Component.literal("Scheduled: " + display(launchEpoch)
                + " (UK time). Remaining: " + duration(seconds)), false);
        }
        return 1;
    }

    private static int schedule(CommandSourceStack source, String input) {
        ensureLoaded(source.getServer());
        if (!isWaiting(source.getServer())) {
            source.sendFailure(Component.literal("Already launched: cannot schedule another world release."));
            return 0;
        }
        final long when;
        try {
            LocalDateTime local = LocalDateTime.parse(input.trim(), INPUT);
            ZoneRules rules = UK.getRules();
            List<ZoneOffset> offsets = rules.getValidOffsets(local);
            if (offsets.size() != 1) {
                source.sendFailure(Component.literal("UK local time is missing or ambiguous due to the clock change. Choose another time."));
                return 0;
            }
            when = local.toEpochSecond(offsets.get(0));
        } catch (RuntimeException ex) {
            source.sendFailure(Component.literal("Use /launch schedule YYYY-MM-DD HH:mm (24-hour UK time), e.g. /launch schedule 2026-10-16 18:00"));
            return 0;
        }
        long now = Instant.now().getEpochSecond();
        if (when <= now + 5) {
            source.sendFailure(Component.literal("Choose a UK release time at least 5 seconds in the future."));
            return 0;
        }
        try {
            save(source.getServer(), when, now);
        } catch (IOException ex) {
            LOGGER.error("Cannot persist Brainmeth launch schedule", ex);
            source.sendFailure(Component.literal("Schedule NOT saved; check the server log/disk."));
            return 0;
        }
        launchEpoch = when;
        scheduledAtEpoch = now;
        priorRemaining = when - now;
        hideBar();
        source.sendSuccess(() -> Component.literal("Release scheduled for " + display(when)
            + ". The server will release everyone automatically; no admin needs to be online."), true);
        LOGGER.info("Launch scheduled: {} by {}", display(when), source.getTextName());
        return 1;
    }

    private static int cancel(CommandSourceStack source) {
        ensureLoaded(source.getServer());
        if (launchEpoch == null) {
            source.sendSuccess(() -> Component.literal("No launch countdown is scheduled."), false);
            return 1;
        }
        if (!deleteSchedule(source.getServer())) {
            source.sendFailure(Component.literal("Could not clear the saved schedule; no change was made."));
            return 0;
        }
        clearInMemory();
        source.sendSuccess(() -> Component.literal("Scheduled release cancelled. Waiting room remains locked."), true);
        LOGGER.info("Launch schedule cancelled by {}", source.getTextName());
        return 1;
    }

    private static int releaseNow(CommandSourceStack source) {
        ensureLoaded(source.getServer());
        if (!isWaiting(source.getServer())) {
            source.sendFailure(Component.literal("The world is already released (or the lobby datapack is not loaded)."));
            return 0;
        }
        if (!release(source.getServer())) {
            source.sendFailure(Component.literal("Release failed; check the lobby datapack and server log."));
            return 0;
        }
        if (!deleteSchedule(source.getServer())) {
            LOGGER.error("Launch succeeded, but old schedule could not be deleted. It will not cause a duplicate release.");
        }
        clearInMemory();
        source.sendSuccess(() -> Component.literal("World released. All waiting players were sent to Survival."), true);
        LOGGER.info("Brainmeth world released manually by {}", source.getTextName());
        return 1;
    }

    private static void onServerTick(ServerTickEvent.Post event) {
        MinecraftServer server = event.getServer();
        ensureLoaded(server);
        if (launchEpoch == null) return;
        if (++ticks % 20 != 0) return;

        long now = Instant.now().getEpochSecond();
        long remaining = launchEpoch - now;
        if (remaining <= 0) {
            // A missed deadline after restart is handled here, without any online admin.
            if (!isWaiting(server)) {
                LOGGER.warn("Scheduled launch found already released; clearing stale schedule");
                if (deleteSchedule(server)) clearInMemory();
                return;
            }
            if (release(server)) {
                LOGGER.info("Automatic Brainmeth launch released at {} (scheduled {})",
                    Instant.now(), display(launchEpoch));
                if (!deleteSchedule(server)) {
                    LOGGER.error("Automatic release succeeded but schedule could not be removed; safe to retry cleanup");
                }
                clearInMemory();
            } else {
                LOGGER.error("Automatic release failed; will retry while schedule remains active");
            }
            return;
        }

        updateBar(server, remaining);
        for (long threshold : ANNOUNCEMENTS) {
            if (priorRemaining > threshold && remaining <= threshold) {
                final String message = threshold <= 10
                    ? "BRAINMETH LAUNCH IN " + threshold + "!"
                    : "Brainmeth launch in " + duration(threshold) + ".";
                server.getPlayerList().broadcastSystemMessage(Component.literal(message), false);
                if (threshold <= 10) {
                    for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                        player.sendSystemMessage(Component.literal(message));
                    }
                }
                LOGGER.info("Launch countdown: {} remaining", duration(threshold));
                break;
            }
        }
        priorRemaining = remaining;
    }

    private static boolean isWaiting(MinecraftServer server) {
        // Minecraft 1.21.1 command execution is void; read the persistent
        // datapack scoreboard directly, without issuing probe commands.
        net.minecraft.world.scores.Objective objective = server.getScoreboard().getObjective("bm_launch");
        if (objective == null) return false;
        net.minecraft.world.scores.ReadOnlyScoreInfo state = server.getScoreboard().getPlayerScoreInfo(
            net.minecraft.world.scores.ScoreHolder.forNameOnly("#state"), objective);
        return state != null && state.value() == 0;
    }

    private static boolean release(MinecraftServer server) {
        try {
            CommandSourceStack source = server.createCommandSourceStack().withPermission(4).withSuppressedOutput();
            server.getCommands().performPrefixedCommand(source, "function brainmeth:lobby/release");
            return !isWaiting(server);
        } catch (Exception ex) {
            LOGGER.error("Brainmeth datapack launch function failed", ex);
            return false;
        }
    }

    private static void updateBar(MinecraftServer server, long remaining) {
        if (bar == null) {
            bar = new ServerBossEvent(Component.literal("Brainmeth launch"), BossEvent.BossBarColor.BLUE,
                BossEvent.BossBarOverlay.PROGRESS);
        }
        bar.setVisible(true);
        bar.setName(Component.literal("BRAINMETH LAUNCH  |  " + duration(remaining)
            + "  |  " + display(launchEpoch)));
        long original = Math.max(1, launchEpoch - scheduledAtEpoch);
        bar.setProgress(Math.max(0.0f, Math.min(1.0f, (float) remaining / original)));
        List<ServerPlayer> players = server.getPlayerList().getPlayers();
        for (ServerPlayer player : players) bar.addPlayer(player);
        // Avoid keeping disconnected players across relogs, even with a long schedule.
        for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
            if (!players.contains(player)) bar.removePlayer(player);
        }
    }

    private static void hideBar() {
        if (bar != null) {
            bar.removeAllPlayers();
            bar.setVisible(false);
            bar = null;
        }
    }

    private static void ensureLoaded(MinecraftServer server) {
        if (activeServer == server) return;
        hideBar();
        activeServer = server;
        launchEpoch = null;
        scheduledAtEpoch = 0;
        priorRemaining = Long.MIN_VALUE;
        ticks = 0;
        Path file = file(server);
        if (Files.notExists(file)) return;
        try {
            JsonObject obj;
            try (var reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
                obj = JsonParser.parseReader(reader).getAsJsonObject();
            }
            long deadline = obj.get("launchEpoch").getAsLong();
            long created = obj.get("scheduledAtEpoch").getAsLong();
            if (deadline <= created || created <= 0) throw new IOException("Invalid schedule timestamps");
            launchEpoch = deadline;
            scheduledAtEpoch = created;
            priorRemaining = Math.max(0, deadline - Instant.now().getEpochSecond());
            LOGGER.info("Restored persistent Brainmeth launch deadline {}", display(deadline));
        } catch (Exception ex) {
            LOGGER.error("Cannot load Brainmeth launch schedule; refusing to guess a release time", ex);
        }
    }

    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-launch.json");
    }

    private static void save(MinecraftServer server, long when, long created) throws IOException {
        Path target = file(server);
        Path tmp = target.resolveSibling(target.getFileName() + ".tmp");
        JsonObject data = new JsonObject();
        data.addProperty("launchEpoch", when);
        data.addProperty("scheduledAtEpoch", created);
        Files.writeString(tmp, data.toString() + System.lineSeparator(), StandardCharsets.UTF_8);
        try {
            Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
        } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
            Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private static boolean deleteSchedule(MinecraftServer server) {
        try {
            Files.deleteIfExists(file(server));
            return true;
        } catch (IOException ex) {
            LOGGER.error("Cannot delete saved Brainmeth launch schedule", ex);
            return false;
        }
    }

    private static void clearInMemory() {
        launchEpoch = null;
        scheduledAtEpoch = 0;
        priorRemaining = Long.MIN_VALUE;
        hideBar();
    }

    private static String display(long epoch) {
        return Instant.ofEpochSecond(epoch).atZone(UK).format(OUTPUT);
    }

    private static String duration(long seconds) {
        long hours = seconds / 3600;
        long mins = (seconds % 3600) / 60;
        long secs = seconds % 60;
        if (hours > 0) return String.format("%dh %02dm %02ds", hours, mins, secs);
        if (mins > 0) return String.format("%dm %02ds", mins, secs);
        return secs + "s";
    }
}
