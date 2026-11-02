package dev.cybersans.brainmeth;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.BookViewScreen;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.neoforge.client.event.ViewportEvent;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** Client-only UI and rendering. Server remains authoritative over every effect. */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID, value = Dist.CLIENT)
public final class BrainmethTomesClient {
    private static volatile boolean redSky;
    private BrainmethTomesClient() {}

    public static void receiveSky(BrainmethTomes.RedSky data, IPayloadContext context) {
        redSky = data.enabled();
    }

    public static boolean isRedSky() {
        Minecraft minecraft = Minecraft.getInstance();
        return redSky && minecraft.level != null
            && minecraft.level.dimension().equals(Level.OVERWORLD);
    }

    @SubscribeEvent
    public static void bookClosed(ScreenEvent.Closing event) {
        if (!(event.getScreen() instanceof BookViewScreen)) return;
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.player == null) return;
        if (isRitualTome(minecraft.player.getMainHandItem())
            || isRitualTome(minecraft.player.getOffhandItem())) {
            PacketDistributor.sendToServer(new BrainmethTomes.CloseTome());
        }
    }

    private static boolean isRitualTome(ItemStack item) {
        if (!item.is(Items.WRITTEN_BOOK)) return false;
        CustomData custom = item.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return false;
        String kind = custom.copyTag().getString("brainmeth_reward");
        return kind.equals("tome_of_bone") || kind.equals("tome_of_catacomb")
            || kind.equals("tome_of_cursed_biome");
    }

    @SubscribeEvent
    public static void fog(ViewportEvent.ComputeFogColor event) {
        if (!isRedSky()) return;
        event.setRed(0.46F);
        event.setGreen(0.015F);
        event.setBlue(0.025F);
    }

    @SubscribeEvent
    public static void disconnect(ClientPlayerNetworkEvent.LoggingOut event) {
        redSky = false;
    }
}
