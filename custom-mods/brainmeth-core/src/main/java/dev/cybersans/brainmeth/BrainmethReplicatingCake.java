package dev.cybersans.brainmeth;

import com.google.gson.*;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CakeBlock;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;
import net.neoforged.neoforge.event.level.BlockEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.minecraft.world.level.storage.LevelResource;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/** Self-replenishing, exponentially replicating decorative cake.
 * Every undisturbed cake can produce one more cake per real day.
 * No hard total replication count, but the processing budget is bounded.
 */
@EventBusSubscriber(modid=BrainmethCore.MOD_ID)
public final class BrainmethReplicatingCake {
    private static final long REPLICATION_INTERVAL = 24 * 3600L;
    private static final int CAKES_CHECKED_PER_SECOND = 20;
    private static final Map<String,Map<Long,Long>> cakes = new HashMap<>();
    private static MinecraftServer loadedServer;
    private static int ticks;
    private record CakeKey(String dimension,long packed) {}
    private static final Deque<CakeKey> rotation=new ArrayDeque<>();
    private BrainmethReplicatingCake(){}
    private static long now(){return Instant.now().getEpochSecond();}
    private static String dim(ServerLevel level){return level.dimension().location().toString();}
    private static String kind(ItemStack item) {
        CustomData d=item.get(DataComponents.CUSTOM_DATA);
        return d==null ? "" : d.copyTag().getString("brainmeth_reward");
    }
    private static boolean hasCake(ServerLevel level,BlockPos at) {
        return cakes.getOrDefault(dim(level),Map.of()).containsKey(at.asLong());
    }
    @SubscribeEvent
    public static void onRightClick(PlayerInteractEvent.RightClickBlock event) {
        if(event.getHand()!=InteractionHand.MAIN_HAND
            ||!(event.getEntity() instanceof ServerPlayer player)
            ||!(event.getLevel() instanceof ServerLevel level))return;
        load(level.getServer());
        ItemStack held=event.getItemStack();
        BlockPos pos=event.getPos();
        if(held.is(Items.CAKE)&&kind(held).equals("replicating_cake")) {
            event.setCanceled(true);
            event.setCancellationResult(InteractionResult.SUCCESS);
            BlockPos target=level.getBlockState(pos).canBeReplaced()?pos:pos.relative(event.getFace());
            if(!level.mayInteract(player,target)||!level.getWorldBorder().isWithinBounds(target)
               || !level.getBlockState(target).canBeReplaced()
               || !Blocks.CAKE.defaultBlockState().canSurvive(level,target)) {
                player.displayClientMessage(Component.literal("Cake cannot be placed here."),true);
                return;
            }
            if(level.setBlock(target,Blocks.CAKE.defaultBlockState(),3)) {
                cakes.computeIfAbsent(dim(level),k->new HashMap<>())
                    .put(target.asLong(),now()+REPLICATION_INTERVAL);
                rotation.addLast(new CakeKey(dim(level),target.asLong()));
                save(level.getServer());
                held.shrink(1);
                player.displayClientMessage(Component.literal(
                    "A very special cake. Leave it untouched for 24 real hours."),true);
            }
            return;
        }
        if(!hasCake(level,pos)||!level.getBlockState(pos).is(Blocks.CAKE))return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        if(!player.canEat(false))return;
        // A normal cake fills two hunger points. The last slice regenerates in place.
        player.getFoodData().eat(2,0.1F);
        int bites=level.getBlockState(pos).getValue(CakeBlock.BITES);
        if(bites>=6)level.setBlock(pos,Blocks.CAKE.defaultBlockState(),3);
        else level.setBlock(pos,level.getBlockState(pos).setValue(CakeBlock.BITES,bites+1),3);
        cakes.get(dim(level)).put(pos.asLong(),now()+REPLICATION_INTERVAL);
        save(level.getServer());
    }
    @SubscribeEvent
    public static void onBreak(BlockEvent.BreakEvent event) {
        if(!(event.getLevel() instanceof ServerLevel level))return;
        load(level.getServer());
        Map<Long,Long> map=cakes.get(dim(level));
        if(map!=null&&map.remove(event.getPos().asLong())!=null) {
            rotation.removeIf(key->key.dimension().equals(dim(level))&&key.packed()==event.getPos().asLong());
            save(level.getServer());
        }
    }
    @SubscribeEvent
    public static void onTick(ServerTickEvent.Post event) {
        MinecraftServer server=event.getServer();
        load(server);
        if(++ticks%20!=0)return;
        // O(20) bounded round-robin rotation, independent of total cake count.
        // Unlike scanning every cake each second, this scales to large colonies.
        if(rotation.isEmpty())return;
        List<CakeKey> selected=new ArrayList<>();
        for(int i=0;i<CAKES_CHECKED_PER_SECOND && !rotation.isEmpty();i++) {
            CakeKey key=rotation.pollFirst();
            if(cakes.getOrDefault(key.dimension(),Map.of()).containsKey(key.packed())) {
                selected.add(key);
                rotation.addLast(key);
            }
        }
        boolean dirty=false;
        for(CakeKey info:selected) {
            String dimension=info.dimension();
            long packed=info.packed();
            Long reproduceAfter=cakes.getOrDefault(dimension,Map.of()).get(packed);
            if(reproduceAfter==null)continue;
            if(now()<reproduceAfter)continue;
            ServerLevel level=null;
            for(ServerLevel candidate:server.getAllLevels())
                if(dim(candidate).equals(dimension)){level=candidate;break;}
            if(level==null)continue;
            BlockPos source=BlockPos.of(packed);
            if(!level.hasChunkAt(source))continue;
            if(!level.getBlockState(source).is(Blocks.CAKE)) {
                cakes.get(dimension).remove(packed);
                rotation.remove(info);
                dirty=true;continue;
            }
            // Seek adjacent safe placement, avoiding player constructions and
            // areas needing chunk generation. If full, retry on next pass.
            Direction[] directions={Direction.NORTH,Direction.SOUTH,Direction.WEST,Direction.EAST};
            for(Direction dir:directions) {
                BlockPos at=source.relative(dir);
                if(!level.hasChunkAt(at)||!level.getWorldBorder().isWithinBounds(at)
                    ||!level.getBlockState(at).isAir()
                    ||!Blocks.CAKE.defaultBlockState().canSurvive(level,at))continue;
                if(level.setBlock(at,Blocks.CAKE.defaultBlockState(),3)) {
                    cakes.computeIfAbsent(dimension,k->new HashMap<>())
                        .put(at.asLong(),now()+REPLICATION_INTERVAL);
                    rotation.addLast(new CakeKey(dimension,at.asLong()));
                    cakes.get(dimension).put(packed,now()+REPLICATION_INTERVAL);
                    dirty=true;
                    break;
                }
            }
        }
        if(dirty)save(server);
    }
    private static Path file(MinecraftServer s) {
        return s.getWorldPath(LevelResource.ROOT).resolve("brainmeth-replicating-cakes.json");
    }
    private static void load(MinecraftServer server) {
        if(loadedServer==server)return;
        loadedServer=server;cakes.clear();rotation.clear();ticks=0;
        if(!Files.isRegularFile(file(server)))return;
        try(var reader=Files.newBufferedReader(file(server),StandardCharsets.UTF_8)) {
            JsonObject object=JsonParser.parseReader(reader).getAsJsonObject();
            for(String dim:object.keySet()) {
                Map<Long,Long> area=new HashMap<>();
                JsonObject items=object.getAsJsonObject(dim);
                for(String key:items.keySet()) {
                    long packed=Long.parseLong(key);
                    area.put(packed,items.get(key).getAsLong());
                    rotation.addLast(new CakeKey(dim,packed));
                }
                cakes.put(dim,area);
            }
        }catch(Exception ex){org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
            .error("Unable to load replicating cakes",ex);}
    }
    private static void save(MinecraftServer server) {
        JsonObject object=new JsonObject();
        cakes.forEach((dim,positions)->{
            JsonObject entries=new JsonObject();
            positions.forEach((block,after)->entries.addProperty(Long.toString(block),after));
            object.add(dim,entries);
        });
        Path dest=file(server),tmp=dest.resolveSibling(dest.getFileName()+".tmp");
        try {
            Files.writeString(tmp,object.toString()+"\n",StandardCharsets.UTF_8);
            try{Files.move(tmp,dest,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
            catch(java.nio.file.AtomicMoveNotSupportedException ex){Files.move(tmp,dest,StandardCopyOption.REPLACE_EXISTING);}
        }catch(IOException ex){org.slf4j.LoggerFactory.getLogger(BrainmethCore.MOD_ID)
            .error("Unable to save replicating cakes",ex);}
    }
}
