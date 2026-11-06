#!/usr/bin/env python3
"""Read-only production health and Bountiful bounty-integrity audit."""
import hashlib
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/srv/minecraft/brainmeth/prod-1211")
FILENAME = "bountiful-neoforge-8.0.0-beta.2-brainmeth.jar"
POOLS = "data/bountiful/bounty_pools/brainmeth"
SOURCE = ROOT / "rules/brainmeth-rules"
LIVE = DATA / "world/datapacks/brainmeth-rules"
errors = []

def check(ok, desc):
    print(("PASS" if ok else "FAIL") + ": " + desc)
    if not ok:
        errors.append(desc)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect(name):
    try:
        return json.loads(subprocess.check_output(
            ["docker", "inspect", name], text=True, stderr=subprocess.PIPE))[0]
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        check(False, f"Cannot inspect Docker {name}: {exc}")
        return {}

print("=== Brainmeth live production audit (read-only) ===")
prod = inspect("brainmeth1211-prod")
state = prod.get("State", {})
check(state.get("Running") is True, "Production container running")
check(state.get("Health", {}).get("Status") == "healthy", "Production health is healthy")
test = inspect("brainmeth1211-test")
check(test.get("State", {}).get("Running") is False, "Test server stopped")

upstream = ROOT / "server-mods" / FILENAME
installed = DATA / "mods" / FILENAME
jars = sorted(p.name for p in (DATA / "mods").glob("*") if p.is_file() and
              p.suffix.lower() == ".jar" and p.name.lower().startswith("bountiful"))
check(jars == [FILENAME], f"Exactly one Bountiful JAR: {jars}")
check(upstream.is_file() and installed.is_file() and
      sha256(upstream) == sha256(installed), "Production Bountiful matches GitHub-built JAR")
if installed.is_file():
    try:
        with zipfile.ZipFile(installed) as jar:
            creator = jar.read("io/ejekta/bountiful/content/BountyCreator.class")
            pool = jar.read("io/ejekta/bountiful/data/PoolEntry.class")
            check(b"java/util/Collections" in creator and b"shuffle" in creator,
                  "Patched randomization bytecode present")
            check(b"forbidsAny" in creator and b"forbids" in pool,
                  "Bountiful runtime supports real cross-tier exclusions")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        check(False, f"Cannot inspect installed Bountiful classes: {exc}")

runtime_meta = ROOT / ".pack-runtime/mods/bountiful.pw.toml"
if runtime_meta.is_file() and installed.is_file():
    try:
        with runtime_meta.open("rb") as handle:
            meta = tomllib.load(handle)
        check(meta.get("filename") == FILENAME and meta.get("side") == "both" and
              meta.get("download", {}).get("hash") == sha256(installed),
              "Packwiz/AutoModpack points to patched JAR on both client/server")
    except (OSError, ValueError) as exc:
        check(False, f"Packwiz metadata invalid: {exc}")
else:
    check(False, "Runtime Packwiz metadata available")

config_path = DATA / "config/bountiful/bountiful.json"
try:
    config = json.loads(config_path.read_text())
    bounty = config["bounty"]
    board = config["board"]
    expected = {
        "allowDecreeMixing": False, "shouldHaveTimersAndExpire": False,
        "reverseMatchingAlgorithm": False,
        "initialCountPreference": {"min": 1, "max": 1},
        "fillerCountPreference": {"min": 1, "max": 1},
    }
    check(all(bounty.get(k) == v for k, v in expected.items()) and
          board.get("updateFrequencySecs") == 900,
          "Live config: isolated decree, 1 objective/reward, 15m, no expiry")
except (OSError, ValueError, KeyError) as exc:
    check(False, f"Live Bountiful config unavailable: {exc}")

names = ["common_objs", "common_rews", "legendary_objs", "legendary_rews",
         "mythic_objs", "mythic_rews"]
pools = {}
for name in names:
    rel = Path(POOLS) / (name + ".json")
    try:
        source_bytes = (SOURCE / rel).read_bytes()
        live_bytes = (LIVE / rel).read_bytes()
        check(source_bytes == live_bytes, f"Deployed pool matches GitHub: {name}")
        pools[name] = json.loads(live_bytes)
    except (OSError, ValueError) as exc:
        check(False, f"Missing or invalid deployed pool {name}: {exc}")

if len(pools) == 6:
    rewards = [r for n in names if n.endswith("_rews") for r in pools[n]["content"].values()]
    tested = 0
    violations = []
    for name in ("common_objs", "legendary_objs", "mythic_objs"):
        for key, obj in pools[name]["content"].items():
            forbidden = [(e["type"], e["content"]) for e in obj.get("forbids", [])]
            if len(forbidden) != len(set(forbidden)):
                violations.append(f"{name}.{key}: duplicate exclusions")
            for reward in rewards:
                tested += 1
                actual_allowed = (reward["type"], reward["content"]) not in forbidden
                expected_allowed = obj["markers"] == reward["markers"]
                if actual_allowed != expected_allowed:
                    violations.append(f"{name}.{key}: {reward['content']} wrong tier")
    check(not violations, f"All {tested} live objective/reward combinations enforce tiers")
    if violations:
        print("  First errors:", *violations[:8], sep="\n  ")

print("=== Latest production log lines (informational) ===")
try:
    log = subprocess.run(["docker", "logs", "--tail", "400", "brainmeth1211-prod"],
                         capture_output=True, text=True, timeout=20).stdout
    lines = [line for line in log.splitlines() if
             "Done (" in line or "bountiful" in line.lower() or
             "exception" in line.lower() or "fatal" in line.lower()]
    for line in lines[-12:]:
        print(line[:260])
except (OSError, subprocess.TimeoutExpired) as exc:
    print("Could not read logs:", exc)

print(f"=== RESULTS: {len(errors)} failed check(s) ===")
if errors:
    print(*errors, sep="\n- ")
    sys.exit(1)
print("Installed patch, configuration, health and tier definitions verified.")
print("NOTE: Generated-bounty sampling is still needed to prove gameplay behavior.")
