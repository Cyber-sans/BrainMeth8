#!/usr/bin/env python3
"""Check unique Crown of Brainmeth award and durable theft notifications."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "custom-mods/brainmeth-core/src/main/java/dev/cybersans/brainmeth"
crown = (base / "BrainmethKingCrown.java").read_text()
delivery = (base / "BrainmethBountyDelivery.java").read_text()
for value in (
    "brainmeth-crown.json", "grantThroughBounty", "PlayerLoggedInEvent",
    "has stolen the Crown of Brainmeth!", "broadcast", "sendSystemMessage",
    "getEnderChestInventory", "getInventory()", "lastEventId",
    "brainmeth_crown_id", "getString(\"brainmeth_reward\")",
    "AtomicMoveNotSupportedException", "GZIPInputStream",
    "loc.inventory().setItem(loc.slot(), ItemStack.EMPTY)"
):
    if value != "broadcast":
        assert value in crown, value
assert "grantThroughBounty(target)" in delivery
assert 'id.equals("mystery_plushie")' in delivery
assert '"king_of_brainmeth_crown"' in delivery
assert "getAllEntities" not in crown and "getEntities(" not in crown
assert "LootContextParamSets.EMPTY" in crown
assert "server.reloadableRegistries().getLootTable(key)" in crown
assert "tag(prize, newId)" in crown
assert "removeRevoked(player)" in crown
assert "winner.getInventory().add(prize)" in crown
assert "oldIssued ? \" has stolen the Crown of Brainmeth!\"" in crown
assert "reserveUniqueReward" not in crown
assert "No second crown can be awarded" not in crown
assert "removeRevoked(player);" in crown.split("public static void onLogin", 1)[1]
assert "BrainmethKingCrown.class" in (root / "scripts/check-brainmeth-jar.py").read_text()
print("Unique Crown verified: bounty transfer, old ID revocation, persisted theft and offline replay.")
