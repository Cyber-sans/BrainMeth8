package dev.cybersans.brainmeth;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

import java.util.Locale;

/** Legendary Tracker: reveals one online player's live location per real 24 hours. */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethTracker {
    private static final String COOLDOWN_KEY = "brainmeth_tracker_ready_epoch";
    private static final long COOLDOWN_SECONDS = 24 * 60 * 60;
    private BrainmethTracker() {}

    private static boolean isTracker(ItemStack item) {
        if (!item.is(Items.COMPASS)) return false;
        CustomData data = item.get(DataComponents.CUSTOM_DATA);
        return data != null && "tracker".equals(data.copyTag().getString("brainmeth_reward"));
    }

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("tracker")
            .then(Commands.literal("locate")
                .then(Commands.argument("player", StringArgumentType.word())
                    .suggests((context, builder) -> {
                        for (ServerPlayer p : context.getSource().getServer().getPlayerList().getPlayers())
                            builder.suggest(p.getGameProfile().getName());
                        return builder.buildFuture();
                    })
                    .executes(ctx -> locate(ctx.getSource().getPlayerOrException(),
                        StringArgumentType.getString(ctx, "player"))))));
    }

    private static int locate(ServerPlayer user, String name) {
        if (!isTracker(user.getMainHandItem())) {
            user.sendSystemMessage(Component.literal("Hold the Tracker in your main hand.").withStyle(ChatFormatting.RED));
            return 0;
        }
        if (!name.matches("[A-Za-z0-9_]{3,16}")) {
            user.sendSystemMessage(Component.literal("Choose a valid player name.").withStyle(ChatFormatting.RED));
            return 0;
        }
        ServerPlayer target = user.getServer().getPlayerList().getPlayers().stream()
            .filter(player -> player.getGameProfile().getName().toLowerCase(Locale.ROOT)
                .equals(name.toLowerCase(Locale.ROOT)))
            .findFirst().orElse(null);
        if (target == null) {
            user.sendSystemMessage(Component.literal("That player must be online to reveal their current coordinates.")
                .withStyle(ChatFormatting.RED));
            return 0;
        }
        long now = System.currentTimeMillis() / 1000;
        long ready = user.getPersistentData().getLong(COOLDOWN_KEY);
        if (ready > now) {
            long remaining = ready - now;
            long hours = remaining / 3600;
            long minutes = (remaining % 3600 + 59) / 60;
            user.sendSystemMessage(Component.literal("Tracker recharges in " + hours + "h " + minutes + "m.")
                .withStyle(ChatFormatting.RED));
            return 0;
        }
        // Store the cooldown against the user so swapping/copying Trackers
        // cannot bypass it. Player persistent data survives relog and restart.
        user.getPersistentData().putLong(COOLDOWN_KEY, now + COOLDOWN_SECONDS);
        String dimension = target.level().dimension().equals(Level.OVERWORLD) ? "Overworld"
            : target.level().dimension().equals(Level.NETHER) ? "Nether"
            : target.level().dimension().equals(Level.END) ? "End"
            : target.level().dimension().location().toString();
        var pos = target.blockPosition();
        user.sendSystemMessage(Component.literal(target.getGameProfile().getName()
            + " is at [" + pos.getX() + ", " + pos.getY() + ", " + pos.getZ()
            + "] (" + dimension + ").").withStyle(ChatFormatting.GOLD));
        target.sendSystemMessage(Component.literal("Your coordinates have been leaked!")
            .withStyle(ChatFormatting.RED));
        return 1;
    }

    @SubscribeEvent
    public static void onUse(PlayerInteractEvent.RightClickItem event) {
        if (event.getHand() != InteractionHand.MAIN_HAND
            || !(event.getEntity() instanceof ServerPlayer player)
            || !isTracker(event.getItemStack())) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        player.sendSystemMessage(Component.literal("Tracker: /tracker locate <player> (once per 24 real hours).")
            .withStyle(ChatFormatting.GOLD));
    }
}
