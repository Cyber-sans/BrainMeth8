package dev.cybersans.brainmeth;

import com.google.gson.*;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.BlockPos;
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
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.npc.VillagerData;
import net.minecraft.world.entity.npc.VillagerProfession;
import net.minecraft.world.entity.npc.VillagerType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.storage.LevelResource;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.level.BlockDropsEvent;

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
    private static final ChatFormatting[] WHISPER_PALETTE = {
        ChatFormatting.DARK_PURPLE, ChatFormatting.DARK_BLUE,
        ChatFormatting.DARK_AQUA, ChatFormatting.DARK_RED,
        ChatFormatting.DARK_GREEN
    };
    private static final Map<String,List<Message>> inbox = new HashMap<>();
    private static final Map<UUID,Villager> butlers = new HashMap<>();
    // Dimension -> placed bell position -> real-world epoch when it is ready again.
    private static final Map<String,Map<Long,Long>> placedBells = new HashMap<>();
    private static final Map<UUID,PendingBell> pendingBellPlacements = new HashMap<>();
    private record PendingBell(String dimension, long tick, long readyEpoch) {}
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
        if(online!=null) showTitle(online,message);
        else {
            inbox.computeIfAbsent(key,k->new ArrayList<>()).add(new Message(sender.getName().getString(),message));
            save(server);
        }
        return 1;
    }
    private static Component colouredWhisper(String body) {
        var result = Component.empty();
        Random random = new Random();
        int previous = -1;
        // Iterate code points so Unicode characters are not split into invalid surrogate halves.
        for (int offset = 0; offset < body.length();) {
            int codePoint = body.codePointAt(offset);
            offset += Character.charCount(codePoint);
            String glyph = new String(Character.toChars(codePoint));
            if (Character.isWhitespace(codePoint)) {
                result.append(Component.literal(glyph));
                continue;
            }
            int shade = random.nextInt(WHISPER_PALETTE.length);
            if (shade == previous) shade = (shade + 1) % WHISPER_PALETTE.length;
            previous = shade;
            result.append(Component.literal(glyph).withStyle(WHISPER_PALETTE[shade]));
        }
        return result;
    }

    private static void showTitle(ServerPlayer to,String body) {
        Component coloured = colouredWhisper(body);
        to.connection.send(new ClientboundSetTitlesAnimationPacket(10,100,20));
        to.connection.send(new ClientboundSetTitleTextPacket(
            Component.literal("A Whisper from Beyond").withStyle(ChatFormatting.DARK_PURPLE)));
        to.connection.send(new ClientboundSetSubtitleTextPacket(coloured));
        // Only the sender gets an acknowledgement; recipients see no attribution.
        to.sendSystemMessage(Component.literal("[Crystal Ball] ")
            .withStyle(ChatFormatting.DARK_GRAY).append(coloured.copy()));
    }
    @SubscribeEvent
    public static void onItemUse(PlayerInteractEvent.RightClickItem event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;
        ItemStack item=event.getItemStack();
        // The Butler's Bell only works as a placed, rung block, never in the hand.
        if (item.is(Items.BELL) && kind(item).equals("butlers_bell")) return;
        if (event.getHand() != InteractionHand.MAIN_HAND) return;
        String k=kind(item);
        boolean handled=true;
        switch(k) {
            case "crystal_ball" -> { /* Command usage is documented in the item lore. */ }
            case "kill_switch" -> {
                if(!item.is(Items.STONE_BUTTON))break;
                if(!"true".equalsIgnoreCase(System.getenv("BRAINMETH_ALLOW_KILLSWITCH"))) {
                    break;
                }
                if(restartAtTick>=0) {
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
    /**
     * A special bell places using vanilla's normal BellBlockItem behaviour.
     * The subsequent EntityPlaceEvent records its position and cooldown.
     * Ringing that particular placed bell (with any item or an empty hand)
     * summons Mr. Deeds. Ordinary bells are unaffected.
     */
    @SubscribeEvent
    public static void onBellUseOnBlock(PlayerInteractEvent.RightClickBlock event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)) return;
        load(level.getServer());
        String dimension = level.dimension().location().toString();
        long pos = event.getPos().asLong();
        Map<Long,Long> bells = placedBells.get(dimension);
        if (level.getBlockState(event.getPos()).is(Blocks.BELL)
            && bells != null && bells.containsKey(pos)) {
            // Do not cancel: vanilla must still ring the actual bell.
            if (event.getHand() == InteractionHand.MAIN_HAND) {
                summonButler(player, level, event.getPos());
            }
            return;
        }
        ItemStack held = event.getItemStack();
        if (!held.is(Items.BELL) || !kind(held).equals("butlers_bell")) return;
        CustomData data = held.get(DataComponents.CUSTOM_DATA);
        long ready = data == null ? 0L : data.copyTag().getLong("butler_ready");
        pendingBellPlacements.put(player.getUUID(),
            new PendingBell(dimension, level.getGameTime(), ready));
        // Do not cancel: vanilla placement checks block support and protection.
    }

    @SubscribeEvent
    public static void onBellPlaced(BlockEvent.EntityPlaceEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
            || !(event.getLevel() instanceof ServerLevel level)
            || !event.getPlacedBlock().is(Blocks.BELL)) return;
        PendingBell pending = pendingBellPlacements.remove(player.getUUID());
        if (pending == null || pending.tick() != level.getGameTime()
            || !pending.dimension().equals(level.dimension().location().toString())) return;
        load(level.getServer());
        placedBells.computeIfAbsent(pending.dimension(), k -> new HashMap<>())
            .put(event.getPos().asLong(), pending.readyEpoch());
        savePlacedBells(level.getServer());
    }

    @SubscribeEvent
    public static void onBellBroken(BlockEvent.BreakEvent event) {
        if (event.isCanceled() || !(event.getLevel() instanceof ServerLevel level)
            || !event.getState().is(Blocks.BELL)
            || !event.getPlayer().getAbilities().instabuild) return;
        load(level.getServer());
        Map<Long,Long> bells = placedBells.get(level.dimension().location().toString());
        if (bells != null && bells.remove(event.getPos().asLong()) != null)
            savePlacedBells(level.getServer());
    }

    @SubscribeEvent
    public static void onBellDrops(BlockDropsEvent event) {
        if (!event.getState().is(Blocks.BELL)) return;
        ServerLevel level = event.getLevel();
        load(level.getServer());
        Map<Long,Long> bells = placedBells.get(level.dimension().location().toString());
        if (bells == null) return;
        Long ready = bells.remove(event.getPos().asLong());
        if (ready == null) return;
        savePlacedBells(level.getServer());
        for (ItemEntity drop : event.getDrops()) {
            ItemStack item = drop.getItem();
            if (!item.is(Items.BELL)) continue;
            CompoundTag tag = new CompoundTag();
            tag.putString(MARKER, "butlers_bell");
            tag.putLong("butler_ready", ready);
            item.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            item.set(DataComponents.ITEM_NAME,
                Component.literal("The Butler's Bell").withStyle(ChatFormatting.LIGHT_PURPLE));
            item.set(DataComponents.LORE, new ItemLore(List.of(
                Component.literal("Place it, then ring it to summon Mr. Deeds for five minutes.")
                    .withStyle(ChatFormatting.GRAY),
                Component.literal("One summon per real day. Keeps its magic when picked up.")
                    .withStyle(ChatFormatting.GRAY))));
            item.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
            item.set(DataComponents.MAX_STACK_SIZE, 1);
        }
    }

    private static void summonButler(ServerPlayer player, ServerLevel level, BlockPos bellPos) {
        Map<Long,Long> bells = placedBells.get(level.dimension().location().toString());
        if (bells == null) return;
        Long ready = bells.get(bellPos.asLong());
        if (ready == null || ready > now()) return;
        Villager existing = butlers.get(player.getUUID());
        if (existing != null && existing.isAlive()) return;

        Villager butler = EntityType.VILLAGER.create(level);
        if (butler == null) return;
        butler.setVillagerData(new VillagerData(VillagerType.PLAINS,VillagerProfession.NITWIT,1));
        butler.setCustomName(Component.literal("Mr. Deeds"));
        butler.setCustomNameVisible(true);
        butler.setInvulnerable(true);
        butler.getPersistentData().putUUID(BUTLER_MARKER, player.getUUID());
        butler.getPersistentData().putLong(BUTLER_EXPIRY, now() + 300L);
        butler.moveTo(player.getX(), player.getY(), player.getZ(), player.getYRot(), 0);
        if (!level.addFreshEntity(butler)) return;

        butlers.put(player.getUUID(), butler);
        // Cooldown belongs to the placed bell, and follows it when picked up.
        bells.put(bellPos.asLong(), now() + ONE_DAY);
        savePlacedBells(level.getServer());
    }

    private static Path placedBellsPath(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("brainmeth-butler-bells.json");
    }

    private static void loadPlacedBells(MinecraftServer server) {
        placedBells.clear();
        Path file = placedBellsPath(server);
        if (!Files.isRegularFile(file)) return;
        try (var reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            for (String dimension : root.keySet()) {
                Map<Long,Long> entries = new HashMap<>();
                JsonObject positions = root.getAsJsonObject(dimension);
                for (String packed : positions.keySet()) {
                    entries.put(Long.parseLong(packed), positions.get(packed).getAsLong());
                }
                placedBells.put(dimension, entries);
            }
        } catch (Exception ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
                .error("Cannot load Butler's Bell positions", ex);
        }
    }

    private static void savePlacedBells(MinecraftServer server) {
        JsonObject root = new JsonObject();
        placedBells.forEach((dimension, positions) -> {
            JsonObject entries = new JsonObject();
            positions.forEach((pos, ready) -> entries.addProperty(Long.toString(pos), ready));
            root.add(dimension, entries);
        });
        Path file = placedBellsPath(server);
        Path tmp = file.resolveSibling(file.getFileName() + ".tmp");
        try {
            Files.writeString(tmp, root.toString() + "\n", StandardCharsets.UTF_8);
            try {
                Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING,
                    StandardCopyOption.ATOMIC_MOVE);
            } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException ex) {
            org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
                .error("Cannot save Butler's Bell positions", ex);
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
                for(Message m:waiting)showTitle(player,m.body());
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
        inbox.clear();butlers.clear();crowns.clear();pendingBellPlacements.clear();ticks=0;restartAtTick=-1;
        loadedServer=server;
        loadPlacedBells(server);
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
