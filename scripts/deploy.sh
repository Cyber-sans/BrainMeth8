#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-test}"
if [[ "$TARGET" != "test" && "$TARGET" != "prod" ]]; then
  echo "Usage: $0 [test|prod]" >&2
  exit 2
fi

# Production is supported exclusively in its dedicated 1.21.1 data directory.
# The level.dat + version marker guard below prevents accidental 26.2 downgrades.
python3 ./scripts/prepare-pack-v5.py --pack-root "$ROOT/pack" --runtime-root "$ROOT/.pack-runtime"
# TEMP: quarantine Minecart Speed on 1.21.1 until its watchdog hang is resolved.
python3 ./scripts/disable-minecart-speed.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-audio-mods.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-qol-mods.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-ui-mods.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-falling-leaves.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-client-extras.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-effectual.py --runtime-root "$ROOT/.pack-runtime"
python3 ./scripts/prepare-no-chat-restrictions.py --runtime-root "$ROOT/.pack-runtime"
# Both collectible mods are mandatory; pinned jar hashes generated for runtime Packwiz.
python3 ./scripts/prepare-collectibles.py --runtime-root "$ROOT/.pack-runtime"
# Required only for 1.21.1; no schedule is created on install.
# Github Actions commits the server-side mod JAR for simple git pull deployment.
python3 ./scripts/prepare-brainmeth-core.py --runtime-root "$ROOT/.pack-runtime" --jar "$ROOT/server-mods/brainmeth-core.jar"
# Operator-only WorldEdit; pinned NeoForge 1.21.1 build, server-side only.
python3 ./scripts/prepare-worldedit.py --runtime-root "$ROOT/.pack-runtime"
# Pinned MIT Orbital Railgun fork: both client/server, one-block-only impact.
python3 ./scripts/prepare-precision-railgun.py --runtime-root "$ROOT/.pack-runtime" --jar "$ROOT/server-mods/brainmeth-precision-railgun.jar"
# Generated Packwiz metadata can inherit a restrictive umask (e.g. 0600).
# nginx serves this directory as a different user; make files world-readable
# and directories traversable before validating and starting containers.
chmod -R a+rX "$ROOT/.pack-runtime"
./scripts/validate.sh

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

if [[ "$TARGET" == "prod" ]]; then
  DATA_DIR="${PROD_DATA_DIR:-/srv/minecraft/brainmeth/prod-1211}"
else
  DATA_DIR="${TEST_DATA_DIR:-/srv/minecraft/brainmeth/test-1211}"
fi

# A world from 26.2 must NEVER be loaded by Minecraft 1.21.1.
mkdir -p "$DATA_DIR"
marker="$DATA_DIR/.brainmeth-minecraft-version"
if [[ -f "$DATA_DIR/world/level.dat" ]]; then
  if [[ ! -f "$marker" ]] || [[ "$(cat "$marker")" != "1.21.1" ]]; then
    echo "Blocked: existing world lacks 1.21.1 marker: $DATA_DIR" >&2
    exit 2
  fi
elif [[ -f "$marker" ]] && [[ "$(cat "$marker")" != "1.21.1" ]]; then
  echo "Blocked: data directory has a different game-version marker" >&2
  exit 2
else
  printf '1.21.1\n' > "$marker"
fi
# Install Brainmeth gameplay rules as a server-side datapack before startup.
# The function runs on every world load/reload; no client changes required.
DATAPACK_SOURCE="$ROOT/rules/brainmeth-rules"
DATAPACK_DEST="$DATA_DIR/world/datapacks/brainmeth-rules"
mkdir -p "$DATA_DIR/world/datapacks"
mkdir -p "$DATAPACK_DEST"
cp -a "$DATAPACK_SOURCE/." "$DATAPACK_DEST/"
# Only retire superseded Brainmeth Bountiful files. Copying over a datapack
# does not remove deleted files, so obsolete tier definitions would survive.
BOUNTY_POOL_DEST="$DATAPACK_DEST/data/bountiful/bounty_pools/brainmeth"
for obsolete in mything_objs.json mything_rews.json \
                uncommon_objs.json uncommon_rews.json \
                rare_objs.json rare_rews.json \
                special_objs.json special_rews.json; do
  rm -f "$BOUNTY_POOL_DEST/$obsolete"
done
OLD_REWARD_POOLS="$DATAPACK_DEST/data/brainmeth/loot_table/bounties/rewards"
rm -f "$OLD_REWARD_POOLS/uncommon_pool.json" "$OLD_REWARD_POOLS/rare_pool.json"

# Preserve Better Days' smooth sleep warp, but slow its maximum from 110x to 40x.
python3 ./scripts/configure-betterdays.py --data-root "$DATA_DIR"

# Minecraft 1.21.1 requires JSON-encoded text inside item-name/lore components.
# This also preserves the live repair on every future deployment.
python3 ./scripts/normalize-rule-components.py --pack "$DATAPACK_DEST"
# No natural plushie/trophy/stand acquisition before custom bounty integration.
python3 ./scripts/lock-collectibles.py --data-root "$DATA_DIR"
# Install the single Brainmeth bounty decree and keep default Bountiful pools out.
python3 ./scripts/configure-bountiful.py --data-root "$DATA_DIR"

# Keep targeted DnT enchantment bans on the server, without disabling other enchants.
# The enchantment-disabler mod reads this config at startup.
ENCHANT_CONFIG_SOURCE="$ROOT/rules/server-config/enchantmentdisabler/config.toml"
ENCHANT_CONFIG_DEST="$DATA_DIR/config/enchantmentdisabler/config.toml"
mkdir -p "$(dirname "$ENCHANT_CONFIG_DEST")"
cp "$ENCHANT_CONFIG_SOURCE" "$ENCHANT_CONFIG_DEST"

# Improved Mobs: retain upstream combat/difficulty defaults, disable only
# destructive extra AI (block breaking, theft, explosives, lava and fire).
IMPROVED_MOBS_CONFIG_SOURCE="$ROOT/rules/server-config/improvedmobs/common.toml"
IMPROVED_MOBS_CONFIG_DEST="$DATA_DIR/config/improvedmobs/common.toml"
mkdir -p "$(dirname "$IMPROVED_MOBS_CONFIG_DEST")"
cp "$IMPROVED_MOBS_CONFIG_SOURCE" "$IMPROVED_MOBS_CONFIG_DEST"

# Savage Ender Dragon (Cupboard): JSON config is read at server startup.
# Used by the separate 1.21.1 test and production instances.
DRAGONFIGHT_CONFIG_SOURCE="$ROOT/rules/server-config/dragonfight.json"
DRAGONFIGHT_CONFIG_DEST="$DATA_DIR/config/dragonfight.json"
mkdir -p "$(dirname "$DRAGONFIGHT_CONFIG_DEST")"
cp "$DRAGONFIGHT_CONFIG_SOURCE" "$DRAGONFIGHT_CONFIG_DEST"

# Bosses of Mass Destruction: per-boss encounter tuning (AutoConfig/Jankson).
BOMD_CONFIG_SOURCE="$ROOT/rules/server-config/bosses_of_mass_destruction.json5"
BOMD_CONFIG_DEST="$DATA_DIR/config/bosses_of_mass_destruction.json5"
mkdir -p "$(dirname "$BOMD_CONFIG_DEST")"
cp "$BOMD_CONFIG_SOURCE" "$BOMD_CONFIG_DEST"

# Wither: Reincarnated: patch actual generated config, preserving explosion sizes.
# First boot creates the TOML; redeploy afterwards to apply this tuning.
python3 ./scripts/tune-wither-reincarnated.py --data-root "$DATA_DIR"

# The Knocker: rare encounters regardless of the world's Hard setting.
KNOCKER_CONFIG_SOURCE="$ROOT/rules/server-config/knocker.toml"
KNOCKER_CONFIG_DEST="$DATA_DIR/config/knocker.toml"
mkdir -p "$(dirname "$KNOCKER_CONFIG_DEST")"
cp "$KNOCKER_CONFIG_SOURCE" "$KNOCKER_CONFIG_DEST"

# Remove the stale server-only jar before restarting NeoForge. Packwiz no longer
# lists it, and deletion is limited to this exact mod's filename.
rm -f "$DATA_DIR/mods/minecartspeed-neoforge-1.21.1.jar"
# Remove only the previously broken custom launch mod before reinstallation.
# The validated runtime Packwiz manifest reinstalls the newly built JAR.
rm -f "$DATA_DIR/mods/brainmeth-core.jar"
rm -f "$DATA_DIR/mods/brainmeth-precision-railgun.jar"
python3 ./scripts/configure-automodpack.py --data-root "$DATA_DIR"
python3 ./scripts/stage-client-mods.py --pack-root "$ROOT/.pack-runtime" --data-root "$DATA_DIR"
# Cosmetic resource packs live in AutoModpack Extras, never server /mods.
python3 ./scripts/stage-client-resourcepacks.py --data-root "$DATA_DIR"
# Packwiz can report up-to-date despite missing server dependencies; repair
# only verified mandatory JARs before booting NeoForge.
python3 ./scripts/stage-server-dependencies.py --runtime-root "$ROOT/.pack-runtime" --data-root "$DATA_DIR"
# Server-only ore obfuscation; not distributed to players via AutoModpack.
# Remove Fast Noise (incompatible with AntiXray) from existing production data.
rm -f "$DATA_DIR"/mods/zfastnoise-*.jar
python3 ./scripts/install-antixray.py --data-root "$DATA_DIR"
# Match clients using REI 16.0.799; enable multiplayer recipe item movement.
python3 ./scripts/install-rei-server.py --data-root "$DATA_DIR"
# Local private OGG is wrapped as a resource-only NeoForge client mod in AutoModpack Essential.
# Source lives outside Git and the generated JAR is never committed.
python3 ./scripts/stage-private-music.py --data-root "$DATA_DIR"

docker compose --profile "$TARGET" pull
# Nginx bind mounts the runtime directory inode. Recreate it after atomic regeneration.
docker compose --profile "$TARGET" up -d --force-recreate packwiz
docker compose --profile "$TARGET" up -d

# Pack/config changes are consumed during Minecraft startup, so every deploy
# deliberately recreates the target server without bouncing shared services.
SERVICE="minecraft-$TARGET"
docker compose --profile "$TARGET" up -d --force-recreate --no-deps "$SERVICE"

docker compose ps
