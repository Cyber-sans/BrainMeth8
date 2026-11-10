package dev.cybersans.brainmeth.mixin;

import dev.cybersans.brainmeth.BrainmethConsumables;
import net.minecraft.network.protocol.game.ServerboundSetCreativeModeSlotPacket;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import net.minecraft.server.level.ServerPlayer;

/**
 * Creative inventory packets can manufacture arbitrary items without opening
 * the vanilla GUI. Refuse those packets during the potion's single second;
 * normal block placement stays Creative and consumes no held blocks.
 */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class BrainmethCreativeInventoryGuardMixin {
    @Shadow public ServerPlayer player;

    @Inject(method = "handleSetCreativeModeSlot", at = @At("HEAD"), cancellable = true)
    private void brainmeth$blockCreativeMenuItems(ServerboundSetCreativeModeSlotPacket packet, CallbackInfo ci) {
        if (BrainmethConsumables.isPotionCreative(player)) ci.cancel();
    }
}
