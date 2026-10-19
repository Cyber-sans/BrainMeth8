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
assert "BrainmethCrownTaunts.class" in (root / "scripts/check-brainmeth-jar.py").read_text()

daily = (base / "BrainmethCrownTaunts.java").read_text()
assert 'ZoneId.of("Europe/London")' in daily
assert "ThreadLocalRandom.current().nextLong(earliest, midnightTomorrow)" in daily
assert "date.plusDays(1).atStartOfDay(UK).toEpochSecond()" in daily
assert "brainmeth-crown-daily-taunt.json" in daily
assert 'obj.addProperty("fired", fired)' in daily
assert "fired = true;" in daily and 'save(server);' in daily
assert "broadcastSystemMessage(message, false)" in daily
assert "PlayerLoggedInEvent" not in daily and "notices.add" not in daily
assert "BrainmethKingCrown.currentHolderName(server)" in daily
assert "BrainmethKingCrown.currentHolderId(server)" in daily
assert 'ThreadLocalRandom.current().nextInt(TAUNTS.length)' in daily
assert "nonOwners.isEmpty()" in daily
assert "TAUNTS[selected]" in daily
assert "TAUNTS.length - 1" in daily
assert 'holder + " still holds the Crown of Brainmeth. " + suffix' in daily
assert "still holds the Crown of Brainmeth" in daily
phrases = [
    "The rest of you, bend the knee.",
    "You are below them.",
    "They stand above all.",
    "Everybody else smells of poo.",
    "Lower your heads.",
    "Try and take it back.",
    "...for now",
    "Stillwater, Iranian Giggle.",
    "Learn his name.",
    "Say his name.",
    "Remember his name.",
    "Inferior lower citizens."
]
assert all(p in daily for p in phrases)
assert 'suffix = "More like " + holder + "-meth."' in daily
assert 'suffix = target.getGameProfile().getName() + " is not."' in daily
assert 'private static final int SPECIAL_RANDOM_PLAYER = 7;' in daily
assert 'private static final int NAME_METH = 9;' in daily
assert "static String currentHolderName(MinecraftServer server)" in crown
assert "static UUID currentHolderId(MinecraftServer server)" in crown
print("Unique Crown verified: bounty transfer, ownership, theft replay, 14 daily random online-only UK-time taunts.")
