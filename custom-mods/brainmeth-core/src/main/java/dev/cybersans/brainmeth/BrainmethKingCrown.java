package dev.cybersans.brainmeth;

import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** Legendary wearable reward: never obtainable from the general Rare pool. */
@EventBusSubscriber(modid = BrainmethCore.MOD_ID)
public final class BrainmethKingCrown {
    private static int elapsed = 0;
    private BrainmethKingCrown() {}

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post event) {
        if (++elapsed % 40 != 0) return;
        for (ServerPlayer player : event.getServer().getPlayerList().getPlayers()) {
            ItemStack helmet = player.getInventory().armor.get(3);
            CustomData data = helmet.get(DataComponents.CUSTOM_DATA);
            if (data == null || !"king_of_brainmeth_crown".equals(
                    data.copyTag().getString("brainmeth_reward"))) continue;
            player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_RESISTANCE, 120, 1, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 120, 0, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 120, 0, true, false, true));
            player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, true));
        }
    }
}
