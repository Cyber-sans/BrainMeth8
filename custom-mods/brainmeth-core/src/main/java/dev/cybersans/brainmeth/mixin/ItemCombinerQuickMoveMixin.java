package dev.cybersans.brainmeth.mixin;

import dev.cybersans.brainmeth.BrainmethGearRolls;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ItemCombinerMenu;
import net.minecraft.world.inventory.SmithingMenu;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Shift-clicking a smithing result empties the stack before onCraftedBy runs,
 * so roll the result here first. Skipped when the inventory is full: the move
 * would fail and leave a visible roll that could be re-rolled by swapping inputs.
 */
@Mixin(ItemCombinerMenu.class)
public abstract class ItemCombinerQuickMoveMixin {
    @Inject(method = "quickMoveStack", at = @At("HEAD"))
    private void brainmeth$rollSmithingResult(Player player, int index, CallbackInfoReturnable<ItemStack> cir) {
        if (!((Object) this instanceof SmithingMenu smithing) || index != smithing.getResultSlot()) return;
        if (player.getInventory().getFreeSlot() < 0) return;
        BrainmethGearRolls.onSmithed(smithing.getSlot(index).getItem(), smithing, player);
    }
}
