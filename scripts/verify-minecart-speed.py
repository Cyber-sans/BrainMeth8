#!/usr/bin/env python3
"""Static safety checks for Brainmeth Core's 4x vanilla minecart cap."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
base = root / "custom-mods/brainmeth-core/src/main"
src = (base / "java/dev/cybersans/brainmeth/mixin/BrainmethMinecartSpeedMixin.java").read_text()
mixins = json.loads((base / "resources/brainmeth_core.mixins.json").read_text())
assert "BrainmethMinecartSpeedMixin" in mixins["mixins"]
assert '@Mixin(AbstractMinecart.class)' in src
assert 'method = "getMaxSpeedWithRail"' in src
assert 'at = @At("RETURN")' in src
assert '1.6D' in src
for block in ("RAIL", "POWERED_RAIL", "DETECTOR_RAIL", "ACTIVATOR_RAIL"):
    assert f"Blocks.{block}" in src
assert "cart.isInWater()" in src
assert "cart.level().getBlockState(pos)" in src
for risky in ("ServerTickEvent", "getEntities(", "getAllEntities(", "setDeltaMovement(", "moveMinecartOnRail("):
    assert risky not in src, risky
deploy = (root / "scripts/deploy.sh").read_text()
assert "disable-minecart-speed.py" in deploy  # Quarantine old plugin
assert 'rm -f "$DATA_DIR/mods/minecartspeed-neoforge-1.21.1.jar"' in deploy
print("Minecart cap validated: 1.6 blocks/tick on dry vanilla rails; old scanner mod excluded.")
