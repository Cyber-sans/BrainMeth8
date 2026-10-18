package dev.cybersans.brainmeth;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** System-only redemption bridge for Bountiful's command-type rewards.
 * Bountiful executes rewards as the server and interpolates %PLAYER_NAME%.
 * Never exposed to ordinary player permissions.
 */
@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethBountyDelivery {
    private BrainmethBountyDelivery(){}

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("brainmethbounty")
            .requires(source -> source.hasPermission(4))
            .then(Commands.literal("grant")
                .then(Commands.argument("player",StringArgumentType.string())
                    .then(Commands.argument("reward",StringArgumentType.word())
                        .executes(ctx -> grant(ctx.getSource().getServer(),
                            StringArgumentType.getString(ctx,"player"),
                            StringArgumentType.getString(ctx,"reward")))))));
    }

    private static int grant(MinecraftServer server,String name,String id) {
        if(!name.matches("[A-Za-z0-9_]{3,16}") || !id.matches("[a-z0-9_]{1,64}"))return 0;
        ServerPlayer target=server.getPlayerList().getPlayerByName(name);
        if(target==null)return 0;
        String loot;
        // Mystery labels carry no actual prize IDs to the client. The
        // server chooses the shipment at the instant of redemption.
        if(id.equals("mystery_common"))loot="brainmeth:bounties/rewards/common_pool";
        else if(id.equals("mystery_uncommon"))loot="brainmeth:bounties/rewards/common_pool"; // Legacy papers
        else if(id.equals("mystery_legendary"))loot="brainmeth:bounties/rewards/legendary_pool";
        else if(id.equals("mystery_plushie"))loot="brainmeth:rewards/rare/king_of_brainmeth_crown";
        else if(id.equals("mystery_trophy"))loot="brainmeth:rewards/uncommon/kill_switch";
        else if(id.startsWith("common_"))loot="brainmeth:bounties/rewards/common/"+id.substring(7);
        else if(id.startsWith("uncommon_"))loot="brainmeth:bounties/rewards/uncommon/"+id.substring(9);
        else if(id.startsWith("rare_"))loot="brainmeth:bounties/rewards/rare/"+id.substring(5);
        else if(id.equals("king_of_brainmeth_crown"))loot="brainmeth:rewards/rare/king_of_brainmeth_crown";
        else if(id.equals("kill_switch"))loot="brainmeth:rewards/uncommon/kill_switch";
        else if(id.equals("dragon_egg") || id.equals("mystery_dragon"))loot="brainmeth:bounties/rewards/legendary_pool"; // Legacy papers
        else return 0;
        loot(server,name,loot);
        if(id.startsWith("mystery_"))
            target.sendSystemMessage(Component.literal("Mystery reward revealed! Check your inventory."));
        return 1;
    }

    private static void loot(MinecraftServer server,String player,String table) {
        server.getCommands().performPrefixedCommand(
            server.createCommandSourceStack().withPermission(4).withSuppressedOutput(),
            "loot give "+player+" loot "+table);
    }
}
