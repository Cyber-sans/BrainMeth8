package dev.cybersans.brainmeth;

import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerData;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.npc.VillagerType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/** Batch 6 special server-only rewards. All item identities are custom-data tagged. */
@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethOddities {
    private static final String MARKER = "brainmeth_reward";
    private static final long THREE_HOURS = 10800L;
    private static final long ONE_DAY = 86400L;
    private static final long ONE_HOUR = 3600L;
    private static final String BUTLER_MARKER = "brainmeth_butler_owner";
    private static final String BUTLER_EXPIRY = "brainmeth_butler_expiry";
    private static final String CROWN_MARKER = "brainmeth_crown_owner";
    private static final Map<String,List<Message>> inbox = new HashMap<>();
    private static final Map<UUID,Villager> butlers = new HashMap<>();
    private static final Map<UUID,Display.TextDisplay> crowns = new HashMap<>();
    private static MinecraftServer loadedServer;
    private static long restartAtTick = -1;
    private static int ticks;
    private record Message(String from, String body) {}
    private BrainmethOddities() {}
    private static long now() { return Instant.now().getEpochSecond(); }
    private static String kind(ItemStack item) {
        CustomData d=item.get(DataComponents.CUSTOM_DATA);
        return d==null ? "" : d.copyTag().getString(MARKER);
    }
    private static boolean recharge(ServerPlayer player,ItemStack item,String field,long period,String name) {
        CustomData existing=item.get(DataComponents.CUSTOM_DATA);
        if(existing==null)return false;
        CompoundTag tag=existing.copyTag();
        long current=now(),next=tag.getLong(field);
        if(next>current) {
            player.displayClientMessage(Component.literal(name+" ready in "+(next-current)+" seconds."),true);
            return false;
        }
        tag.putLong(field,current+period);
        item.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
        return true;
    }

    @SubscribeEvent
    public static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("crystalball")
            .then(Commands.literal("send")
                .then(Commands.argument("recipient",StringArgumentType.word())
                    .then(Commands.argument("message",StringArgumentType.greedyString())
                        .executes(ctx->send(ctx.getSource().getPlayerOrException(),
                            StringArgumentType.getString(ctx,"recipient"),
                            StringArgumentType.getString(ctx,"message")))))));
    }
    private static int send(ServerPlayer sender,String username,String content) {
        ItemStack ball=sender.getMainHandItem();
        if(!ball.is(Items.ENDER_EYE)||!kind(ball).equals("crystal_ball")) {
            sender.displayClientMessage(Component.literal("Hold the Crystal Ball in your main hand."),false);
            return 0;
        }
        if(!username.matches("[A-Za-z0-9_]{3,16}")) {
            sender.displayClientMessage(Component.literal("Use a valid player name."),false);
            return 0;
        }
        String message=content.strip().replace('\n',' ').replace('\r',' ');
        if(message.isEmpty() || message.length()>120) {
            sender.displayClientMessage(Component.literal("Message must contain 1 to 120 characters."),false);
            return 0;
        }
        MinecraftServer server=sender.serverLevel().getServer();
        load(server);
        String key=username.toLowerCase(Locale.ROOT);
        ServerPlayer online=server.getPlayerList().getPlayers().stream()
            .filter(p->p.getGameProfile().getName().equalsIgnoreCase(username))
            .findFirst().orElse(null);
        if(online==null && (inbox.values().stream().mapToInt(List::size).sum()>=256
                || inbox.getOrDefault(key,List.of()).size()>=8)) {
            sender.displayClientMessage(Component.literal("That message queue is full."),false);
            return 0;
        }
        if(!recharge(sender,ball,"crystal_ready",THREE_HOURS,"Crystal Ball"))return 0;
        if(online!=null) showTitle(online,sender.getName().getString(),message);
        else {
            inbox.computeIfAbsent(key,k->new ArrayList<>()).add(new Message(sender.getName().getString(),message));
            save(server);
        }
        sender.displayClientMessage(Component.literal("Crystal message sent to "+username+"."),false);
        return 1;
    }
    private static void showTitle(ServerPlayer to,String sender,String body) {
        to.connection.send(new ClientboundSetTitlesAnimationPacket(10,100,20));
        to.connection.send(new ClientboundSetTitleTextPacket(Component.literal("Message from "+sender).withStyle(ChatFormatting.LIGHT_PURPLE)));
        to.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(body).withStyle(ChatFormatting.AQUA)));
        to.sendSystemMessage(Component.literal("[Crystal Ball] "+sender+": "+body));
    }
    @SubscribeEvent
    public static void onItemUse(PlayerInteractEvent.RightClickItem event) {
        if(event.getHand()!=InteractionHand.MAIN_HAND
            ||!(event.getEntity() instanceof ServerPlayer player)
            ||!(event.getLevel() instanceof ServerLevel level))return;
        ItemStack item=event.getItemStack();
        String k=kind(item);
        boolean handled=true;
        switch(k) {
            case "crystal_ball" -> player.displayClientMessage(Component.literal(
                "Hold the ball and type /crystalball send <player> <message>."),false);
            case "kill_switch" -> {
                if(!item.is(Items.STONE_BUTTON))break;
                if(!"true".equalsIgnoreCase(System.getenv("BRAINMETH_ALLOW_KILLSWITCH"))) {
                    player.displayClientMessage(Component.literal("Kill Switch disabled on this server."),false);
                    break;
                }
                if(restartAtTick>=0) {
                    player.displayClientMessage(Component.literal("Restart already scheduled."),false);
                    break;
                }
                restartAtTick=level.getServer().getTickCount()+200L;
                item.shrink(1);
                level.getServer().getPlayerList().broadcastSystemMessage(
                    Component.literal(player.getName().getString()+" pulled the KILL SWITCH! Restarting in 10 seconds.")
                        .withStyle(ChatFormatting.RED),false);
            }
            case "cognitohazard_book" -> {
                if(!item.is(Items.WRITTEN_BOOK))break;
                player.kill();
            }
            case "fake_death_certificate" -> {
                if(!item.is(Items.PAPER))break;
                CustomData data=item.get(DataComponents.CUSTOM_DATA);
                CompoundTag tag=data==null?new CompoundTag():data.copyTag();
                if(tag.getLong("last_fake_death")+5>now())break;
                tag.putLong("last_fake_death",now());
                item.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
                String[] endings={"was struck by a flying potato","forgot to breathe",
                    "tried to swim through air","was slain by a highly emotional chicken",
                    "discovered gravity twice","was overwhelmed by a mild inconvenience",
                    "lost an argument with a fence","was vaporised by absolutely nothing"};
                String message=player.getName().getString()+" "+endings[level.random.nextInt(endings.length)];
                level.getServer().getPlayerList().broadcastSystemMessage(Component.literal(message),false);
            }
            case "butlers_bell" -> {
                if(!item.is(Items.BELL))break;
                Villager existing=butlers.get(player.getUUID());
                if(existing!=null&&existing.isAlive()) {
                    player.displayClientMessage(Component.literal("Mr. Deeds is already on duty."),true);
                    break;
                }
                if(!recharge(player,item,"butler_ready",ONE_DAY,"Butler's Bell"))break;
                Villager butler=EntityType.VILLAGER.create(level);
                if(butler==null)break;
                butler.setVillagerData(new VillagerData(VillagerType.PLAINS,VillagerProfession.NITWIT,1));
                butler.setCustomName(Component.literal("Mr. Deeds"));
                butler.setCustomNameVisible(true);
                butler.setInvulnerable(true);
                butler.getPersistentData().putUUID(BUTLER_MARKER,player.getUUID());
                butler.getPersistentData().putLong(BUTLER_EXPIRY,now()+300L);
                butler.moveTo(player.getX()+1.0,player.getY(),player.getZ()+1.0,
                    player.getYRot(),0);
                level.addFreshEntity(butler);
                butlers.put(player.getUUID(),butler);
                player.displayClientMessage(Component.literal("Mr. Deeds is at your service. For 5 minutes."),true);
            }
            case "manifesto" -> {
                // Written book opens with normal vanilla UI; never cancel the item use.
                handled=false;
            }
            default -> handled=false;
        }
        if(handled) {
            event.setCancellationResult(InteractionResult.SUCCESS);
            event.setCanceled(true);
        }
    }
    @SubscribeEvent
    public static void onEntityJoin(EntityJoinLevelEvent event) {
        if(event.getLevel() instanceof ServerLevel joinedLevel) load(joinedLevel.getServer());
        Entity entity=event.getEntity();
        if(entity instanceof Villager v&&v.getPersistentData().hasUUID(BUTLER_MARKER)) {
            butlers.put(v.getPersistentData().getUUID(BUTLER_MARKER),v);
        }
        if(entity instanceof Display.TextDisplay d&&d.getPersistentData().hasUUID(CROWN_MARKER)) {
            crowns.put(d.getPersistentData().getUUID(CROWN_MARKER),d);
        }
    }
    private static void updateCrown(ServerPlayer player) {
        UUID id=player.getUUID();
        boolean wearing=kind(player.getInventory().armor.get(3)).equals("crown_of_nothing");
        Display.TextDisplay old=crowns.get(id);
        if(!wearing) {
            if(old!=null){old.discard();crowns.remove(id);}
            return;
        }
        if(old==null||!old.isAlive()||old.level()!=player.level()) {
            if(old!=null)old.discard();
            Display.TextDisplay d=EntityType.TEXT_DISPLAY.create(player.serverLevel());
            if(d==null)return;
            // Vanilla TextDisplay setters are private in 1.21.1; use its
            // data-component command after spawning rather than reflection.
            d.setNoGravity(true);
            d.setInvulnerable(true);
            d.getPersistentData().putUUID(CROWN_MARKER,id);
            player.serverLevel().addFreshEntity(d);
            player.serverLevel().getServer().getCommands().performPrefixedCommand(
                player.serverLevel().getServer().createCommandSourceStack()
                    .withPermission(4).withSuppressedOutput(),
                "data merge entity " + d.getUUID()
                    + " {text:'{\\\"text\\\":\\\"King of Absolutely Nothing\\\",\\\"color\\\":\\\"gold\\\"}',billboard:\"center\",background:0,see_through:1b}");
            crowns.put(id,d);
            old=d;
        }
        old.moveTo(player.getX(),player.getY()+2.2,player.getZ(),0,0);
    }
    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server=event.getServer();
        load(server);
        if(restartAtTick>=0&&server.getTickCount()>=restartAtTick) {
            restartAtTick=-1;
            // Built-in command saves world and shuts down normally. Docker
            // restart:unless-stopped relaunches the test container.
            server.getCommands().performPrefixedCommand(
                server.createCommandSourceStack().withPermission(4),"stop");
            return;
        }
        if(++ticks%5!=0)return;
        for(ServerPlayer player:server.getPlayerList().getPlayers()) {
            updateCrown(player);
        }
        if(ticks%20!=0)return;
        for(ServerPlayer player:server.getPlayerList().getPlayers()) {
            List<Message> waiting=inbox.remove(player.getGameProfile().getName().toLowerCase(Locale.ROOT));
            if(waiting!=null) {
                for(Message m:waiting)showTitle(player,m.from(),m.body());
                save(server);
            }
        }
        Iterator<Map.Entry<UUID,Villager>> iter=butlers.entrySet().iterator();
        while(iter.hasNext()) {
            var entry=iter.next();
            Villager butler=entry.getValue();
            if(!butler.isAlive()){iter.remove();continue;}
            ServerPlayer owner=server.getPlayerList().getPlayer(entry.getKey());
            if(now()>=butler.getPersistentData().getLong(BUTLER_EXPIRY)
                ||owner==null) {
                butler.discard();
                iter.remove();
                continue;
            }
            if(butler.level()!=owner.level())continue;
            double distance=butler.distanceToSqr(owner);
            if(distance>225) butler.teleportTo(owner.getX()+1,owner.getY(),owner.getZ()+1);
            else if(distance>6.25)butler.getNavigation().moveTo(owner,1.13);
            else butler.getNavigation().stop();
        }
        // Clear orphaned labels if a player disconnects or loses the crown.
        Iterator<Map.Entry<UUID,Display.TextDisplay>> labels=crowns.entrySet().iterator();
        while(labels.hasNext()) {
            var entry=labels.next();
            if(server.getPlayerList().getPlayer(entry.getKey())==null) {
                entry.getValue().discard();
                labels.remove();
            }
        }
    }
    private static Path path(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-crystal-messages.json");
    }
    private static void load(MinecraftServer server) {
        if(loadedServer==server)return;
        inbox.clear();butlers.clear();crowns.clear();ticks=0;restartAtTick=-1;
        loadedServer=server;
        if(!Files.isRegularFile(path(server)))return;
        try(var reader=Files.newBufferedReader(path(server),StandardCharsets.UTF_8)) {
            JsonObject object=JsonParser.parseReader(reader).getAsJsonObject();
            for(String name:object.keySet()) {
                List<Message> messages=new ArrayList<>();
                for(var element:object.getAsJsonArray(name)) {
                    JsonObject m=element.getAsJsonObject();
                    messages.add(new Message(m.get("sender").getAsString(),m.get("body").getAsString()));
                }
                inbox.put(name,messages);
            }
        }catch(Exception ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Cannot load Crystal Ball messages",ex);
        }
    }
    private static void save(MinecraftServer server) {
        JsonObject object=new JsonObject();
        inbox.forEach((name,messages)->{
            JsonArray items=new JsonArray();
            for(Message m:messages){
                JsonObject value=new JsonObject();value.addProperty("sender",m.from());
                value.addProperty("body",m.body());items.add(value);
            }
            object.add(name,items);
        });
        Path p=path(server),tmp=p.resolveSibling(p.getFileName()+".tmp");
        try {
            Files.writeString(tmp,object.toString()+"\n",StandardCharsets.UTF_8);
            try{Files.move(tmp,p,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
            catch(java.nio.file.AtomicMoveNotSupportedException ex){Files.move(tmp,p,StandardCopyOption.REPLACE_EXISTING);}
        }catch(IOException ex){org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID).error("Cannot persist Crystal Ball messages",ex);}
    }
}
