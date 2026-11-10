package dev.cybersans.brainmeth;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;
import net.neoforged.neoforge.client.event.ClientPlayerNetworkEvent;

/** Restricts only the potion's brief Creative-mode inventory, not normal Creative. */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID, value = Dist.CLIENT)
public final class BrainmethConsumablesClient {
    private static boolean locked;

    private BrainmethConsumablesClient() {}

    public static void setLocked(boolean state) {
        locked = state;
        if (locked && Minecraft.getInstance().screen instanceof CreativeModeInventoryScreen)
            Minecraft.getInstance().setScreen(null);
    }

    @SubscribeEvent
    public static void preventCreativeMenu(ScreenEvent.Opening event) {
        if (locked && event.getNewScreen() instanceof CreativeModeInventoryScreen) {
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void disconnect(ClientPlayerNetworkEvent.LoggingOut event) {
        locked = false;
    }
}
