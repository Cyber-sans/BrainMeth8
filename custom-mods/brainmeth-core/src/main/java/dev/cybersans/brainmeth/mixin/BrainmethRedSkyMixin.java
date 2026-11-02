package dev.cybersans.brainmeth.mixin;

import dev.cybersans.brainmeth.BrainmethTomesClient;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Client-only red sky during an active midnight ritual in the Overworld. */
@Mixin(ClientLevel.class)
public abstract class BrainmethRedSkyMixin {
    @Inject(method = "getSkyColor", at = @At("RETURN"), cancellable = true)
    private void brainmeth$bloodSky(Vec3 camera, float partialTick, CallbackInfoReturnable<Vec3> cir) {
        if (BrainmethTomesClient.isRedSky()) {
            cir.setReturnValue(new Vec3(0.72D, 0.018D, 0.025D));
        }
    }
}
