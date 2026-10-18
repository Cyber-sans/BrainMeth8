package dev.cybersans.brainmeth.mixin;

import dev.cybersans.brainmeth.BrainmethBountyTakeLimit;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Block the fourth Brainmeth board paper before vanilla/Bountiful moves it.
 * Applies to ordinary click, shift-click and hotbar swaps alike. */
@Mixin(AbstractContainerMenu.class)
public abstract class BrainmethBoardPickupMixin {
    @Unique private int brainmeth$pickupSlot = -1;

    @Inject(method = "clicked", at = @At("HEAD"), cancellable = true)
    private void brainmeth$beforeClick(int slotId, int button, ClickType clickType, Player player, CallbackInfo ci) {
        brainmeth$pickupSlot = -1;
        if (!(player instanceof ServerPlayer serverPlayer)) return;
        AbstractContainerMenu menu = (AbstractContainerMenu)(Object)this;
        if (!BrainmethBountyTakeLimit.isBrainmethBoard(menu, slotId)) return;
        // Every action that can remove a bounty, including number-key swaps and
        // throwing it, must be quota-checked. The actual transfer is charged at RETURN.
        if (!BrainmethBountyTakeLimit.mayTake(serverPlayer)) {
            ci.cancel();
            return;
        }
        brainmeth$pickupSlot = slotId;
    }

    @Inject(method = "clicked", at = @At("RETURN"))
    private void brainmeth$afterClick(int slotId, int button, ClickType clickType, Player player, CallbackInfo ci) {
        if (brainmeth$pickupSlot != slotId || !(player instanceof ServerPlayer serverPlayer)) return;
        brainmeth$pickupSlot = -1;
        AbstractContainerMenu menu = (AbstractContainerMenu)(Object)this;
        // Bountiful's per-player virtual board inventory empties the taken slot.
        if (menu.getSlot(slotId).getItem().isEmpty()) {
            BrainmethBountyTakeLimit.didTake(serverPlayer);
        }
    }
}
