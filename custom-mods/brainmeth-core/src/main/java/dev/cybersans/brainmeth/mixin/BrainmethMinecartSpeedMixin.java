package dev.cybersans.brainmeth.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.vehicle.AbstractMinecart;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BaseRailBlock;
import net.minecraft.world.level.block.state.properties.RailShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Keep the 4x dry vanilla-rail speed limit while traversing fast rail movement
 * in short pieces. Only the movement inside moveMinecartOnRail is subdivided:
 * the enclosing vanilla moveAlongTrack still applies drag, acceleration,
 * powered-rail effects and rail callbacks once per game tick.
 *
 * getPosOffs projects each small advance onto the rail beneath the cart,
 * allowing the next advance to follow a different rail shape (notably corners)
 * instead of extrapolating a straight 1.6-block displacement.
 */
@Mixin(AbstractMinecart.class)
public abstract class BrainmethMinecartSpeedMixin {
    @Unique private static final double BRAINMETH_MAX_SPEED_ON_RAIL = 1.6D;
    @Unique private static final double BRAINMETH_MAX_STEP = 0.30D;
    @Unique private static final int BRAINMETH_MAX_STEPS = 8;
    @Unique private Vec3 brainmeth$lastTrackDirection = Vec3.ZERO;

    @Inject(method = "getMaxSpeedWithRail", at = @At("RETURN"), cancellable = true)
    private void brainmeth$raiseVanillaRailSpeedLimit(CallbackInfoReturnable<Double> cir) {
        AbstractMinecart cart = (AbstractMinecart) (Object) this;
        if (cart.isInWater()) return;
        BlockPos pos = cart.getCurrentRailPosition();
        BlockState state = cart.level().getBlockState(pos);
        if (brainmeth$isVanillaRail(state)) cir.setReturnValue(BRAINMETH_MAX_SPEED_ON_RAIL);
    }

    @Unique
    private static boolean brainmeth$isVanillaRail(BlockState state) {
        return state.is(Blocks.RAIL) || state.is(Blocks.POWERED_RAIL)
            || state.is(Blocks.DETECTOR_RAIL) || state.is(Blocks.ACTIVATOR_RAIL);
    }

    @Unique
    private static boolean brainmeth$isSlope(BlockState state) {
        if (!(state.getBlock() instanceof BaseRailBlock rail)) return false;
        RailShape shape = state.getValue(rail.getShapeProperty());
        return shape.isAscending();
    }

    @Inject(method = "moveMinecartOnRail", at = @At("HEAD"), cancellable = true)
    private void brainmeth$substepRailTravel(BlockPos originalRail, CallbackInfo ci) {
        AbstractMinecart cart = (AbstractMinecart) (Object) this;
        brainmeth$lastTrackDirection = Vec3.ZERO;
        if (cart.level().isClientSide || cart.isInWater()) return;
        BlockState originalState = cart.level().getBlockState(originalRail);
        if (!brainmeth$isVanillaRail(originalState)) return;
        // Safety fallback: the high-speed track projection is not yet proven
        // across descending slope-to-flat transitions. Use vanilla movement
        // there instead of risking a cart being pushed into solid blocks.
        if (brainmeth$isSlope(originalState)) return;

        Vec3 velocity = cart.getDeltaMovement();
        double passengerFactor = cart.isVehicle() ? 0.75D : 1.0D;
        double cap = cart.getMaxSpeedWithRail();
        Vec3 movement = new Vec3(
            Mth.clamp(passengerFactor * velocity.x, -cap, cap),
            0.0D,
            Mth.clamp(passengerFactor * velocity.z, -cap, cap));
        double distance = movement.horizontalDistance();
        if (distance <= 0.4D) return; // Vanilla physics for stationary/slow carts.

        int steps = Math.min(BRAINMETH_MAX_STEPS, Math.max(2,
            (int) Math.ceil(distance / BRAINMETH_MAX_STEP)));
        double stride = distance / steps;
        Vec3 direction = movement.normalize();

        for (int i = 0; i < steps; i++) {
            BlockPos rail = cart.getCurrentRailPosition();
            BlockState railState = cart.level().getBlockState(rail);
            if (!brainmeth$isVanillaRail(railState) || brainmeth$isSlope(railState)) break;
            Vec3 from = cart.position();
            // Vanilla's track projection accepts signed distance; choose the
            // orientation aligned with actual travel, not the rail's enum order.
            Vec3 plus = cart.getPosOffs(from.x, from.y, from.z, stride);
            Vec3 minus = cart.getPosOffs(from.x, from.y, from.z, -stride);
            Vec3 target = null;
            double best = -Double.MAX_VALUE;
            for (Vec3 candidate : new Vec3[] {plus, minus}) {
                if (candidate == null) continue;
                Vec3 delta = candidate.subtract(from);
                BlockPos nextRail = BlockPos.containing(candidate.x, candidate.y, candidate.z);
                BlockState nextState = cart.level().getBlockState(nextRail);
                if (brainmeth$isSlope(nextState)) continue;
                double horizontal = delta.horizontalDistance();
                // Reject large discontinuities from invalid/unloaded rail geometry.
                if (horizontal < 1.0E-5D || horizontal > stride + 0.45D) continue;
                double alignment = delta.x * direction.x + delta.z * direction.z;
                if (alignment > best) {
                    best = alignment;
                    target = candidate;
                }
            }
            if (target == null || best <= 0.0D) break;
            Vec3 delta = target.subtract(from);
            // Keep vanilla collision resolution on each short segment.
            cart.move(MoverType.SELF, delta);
            Vec3 actual = cart.position().subtract(from);
            if (actual.horizontalDistanceSqr() < 1.0E-6D) break;
            direction = new Vec3(actual.x, 0.0D, actual.z).normalize();
            brainmeth$lastTrackDirection = direction;
        }
        ci.cancel();
    }

    @Inject(method = "moveAlongTrack", at = @At("RETURN"))
    private void brainmeth$preserveTrackDirection(BlockPos pos, BlockState state, CallbackInfo ci) {
        if (brainmeth$lastTrackDirection.lengthSqr() > 0.0D) {
            AbstractMinecart cart = (AbstractMinecart) (Object) this;
            Vec3 velocity = cart.getDeltaMovement();
            double horizontal = velocity.horizontalDistance();
            if (horizontal > 0.0D) {
                cart.setDeltaMovement(
                    brainmeth$lastTrackDirection.x * horizontal,
                    velocity.y,
                    brainmeth$lastTrackDirection.z * horizontal);
            }
        }
        brainmeth$lastTrackDirection = Vec3.ZERO;
    }
}
