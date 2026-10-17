package dev.cybersans.brainmeth;

import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** System-only redemption bridge for Bountiful's command-type rewards.
 * Bountiful executes rewards as the server and interpolates %PLAYER_NAME%.
 * Never exposed to ordinary player permissions.
 */
@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethBountyDelivery {
    private static final Set<UUID> DRAGON_EGG_CLAIMS=new HashSet<>();
    private static MinecraftServer loadedServer;
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
        else if(id.equals("mystery_uncommon"))loot="brainmeth:bounties/rewards/uncommon_pool";
        else if(id.equals("mystery_legendary"))loot="brainmeth:bounties/rewards/rare_pool";
        else if(id.equals("mystery_plushie"))loot="brainmeth:rewards/rare/king_of_brainmeth_crown";
        else if(id.equals("mystery_trophy"))loot="brainmeth:rewards/uncommon/kill_switch";
        else if(id.startsWith("common_"))loot="brainmeth:bounties/rewards/common/"+id.substring(7);
        else if(id.startsWith("uncommon_"))loot="brainmeth:bounties/rewards/uncommon/"+id.substring(9);
        else if(id.startsWith("rare_"))loot="brainmeth:bounties/rewards/rare/"+id.substring(5);
        else if(id.equals("king_of_brainmeth_crown"))loot="brainmeth:rewards/rare/king_of_brainmeth_crown";
        else if(id.equals("kill_switch"))loot="brainmeth:rewards/uncommon/kill_switch";
        else if(id.equals("dragon_egg") || id.equals("mystery_dragon")) {
            load(server);
            boolean first=DRAGON_EGG_CLAIMS.add(target.getUUID());
            if(first){save(server);loot(server,name,"brainmeth:bounties/rewards/rare_pool");}
            // Bountiful consumes the item objective; always return the unique
            // egg, even on repeat hand-ins. Reward only on the first completion.
            server.getCommands().performPrefixedCommand(
                server.createCommandSourceStack().withPermission(4).withSuppressedOutput(),
                "give "+name+" minecraft:dragon_egg 1");
            target.sendSystemMessage(Component.literal(first
                ? "The Dragon's Legacy completed. Your unique egg is returned."
                : "Dragon Egg already claimed: your egg was returned, with no repeat prize."));
            return 1;
        } else return 0;
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
    private static Path file(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-dragon-egg-claims.json");
    }
    private static void load(MinecraftServer server) {
        if(loadedServer==server)return;
        loadedServer=server;DRAGON_EGG_CLAIMS.clear();
        if(!Files.isRegularFile(file(server)))return;
        try(var reader=Files.newBufferedReader(file(server),StandardCharsets.UTF_8)) {
            JsonArray items=JsonParser.parseReader(reader).getAsJsonArray();
            for(var item:items)DRAGON_EGG_CLAIMS.add(UUID.fromString(item.getAsString()));
        } catch(Exception e) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Unable to read one-time dragon egg claims",e);
        }
    }
    private static void save(MinecraftServer server) {
        JsonArray arr=new JsonArray();
        DRAGON_EGG_CLAIMS.forEach(uuid->arr.add(uuid.toString()));
        Path p=file(server),tmp=p.resolveSibling(p.getFileName()+".tmp");
        try{
            Files.writeString(tmp,arr.toString(),StandardCharsets.UTF_8);
            try{Files.move(tmp,p,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
            catch(java.nio.file.AtomicMoveNotSupportedException e){Files.move(tmp,p,StandardCopyOption.REPLACE_EXISTING);}
        } catch(IOException e) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Unable to save dragon egg claims",e);
        }
    }
}
