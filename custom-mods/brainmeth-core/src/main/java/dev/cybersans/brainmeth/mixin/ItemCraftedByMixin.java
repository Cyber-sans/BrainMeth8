package dev.cybersans.brainmeth.mixin;

import dev.cybersans.brainmeth.BrainmethGearRolls;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Item#onCraftedBy runs for normal and shift-click crafting while the result stack
 * is still intact; NeoForge's ItemCraftedEvent receives an emptied stack on shift-click.
 */
@Mixin(Item.class)
public abstract class ItemCraftedByMixin {
    @Inject(method = "onCraftedBy", at = @At("HEAD"))
    private void brainmeth$rollCraftedGear(ItemStack stack, Level level, Player player, CallbackInfo ci) {
        BrainmethGearRolls.onCrafted(stack, level, player);
    }
}
