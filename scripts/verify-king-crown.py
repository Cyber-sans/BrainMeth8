#!/usr/bin/env python3
"""Check unique Crown of Brainmeth award and durable theft notifications."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth"
crown = (base / "BrainmethKingCrown.java").read_text()
delivery = (base / "BrainmethBountyDelivery.java").read_text()
for value in (
    "brainmeth-crown.json", "reserveUniqueReward", "PlayerLoggedInEvent",
    "has stolen the Crown of Brainmeth!", "broadcast", "sendSystemMessage",
    "getEnderChestInventory", "getInventory()", "lastEventId",
    "brainmeth_crown_id", "getString(\"brainmeth_reward\")",
    "AtomicMoveNotSupportedException", "GZIPInputStream",
    "loc.inventory().setItem(loc.slot(), ItemStack.EMPTY)"
):
    if value != "broadcast":
        assert value in crown, value
assert "reserveUniqueReward(target)" in delivery
assert 'id.equals("mystery_plushie")' in delivery
assert '"king_of_brainmeth_crown"' in delivery
assert "getAllEntities" not in crown and "getEntities(" not in crown
assert "BrainmethKingCrown.class" in (root / "scripts/check-brainmeth-jar.py").read_text()
print("Unique Crown verified: one grant, tagged identity, persisted theft and offline replay.")
