package dev.cybersans.brainmeth.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.vehicle.AbstractMinecart;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Raise only the dry vanilla-rail movement cap from 0.4 to 1.6 blocks/tick
 * (8 -> 32 blocks/second). NeoForge invokes getMaxSpeedWithRail directly from
 * moveMinecartOnRail; no global entity scan or new tick event is necessary.
 *
 * Do not touch powered-rail acceleration, natural slowdown, drag, rail shapes,
 * or minecart movement. Water and custom/modded rails retain their own limits.
 */
@Mixin(AbstractMinecart.class)
public abstract class BrainmethMinecartSpeedMixin {
    private static final double BRAINMETH_MAX_SPEED_ON_RAIL = 1.6D;

    @Inject(method = "getMaxSpeedWithRail", at = @At("RETURN"), cancellable = true)
    private void brainmeth$raiseVanillaRailSpeedLimit(CallbackInfoReturnable<Double> cir) {
        AbstractMinecart cart = (AbstractMinecart) (Object) this;
        if (cart.isInWater()) return;

        BlockPos pos = cart.getCurrentRailPosition();
        BlockState state = cart.level().getBlockState(pos);
        if (state.is(Blocks.RAIL) || state.is(Blocks.POWERED_RAIL)
                || state.is(Blocks.DETECTOR_RAIL) || state.is(Blocks.ACTIVATOR_RAIL)) {
            cir.setReturnValue(BRAINMETH_MAX_SPEED_ON_RAIL);
        }
    }
}
