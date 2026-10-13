# Brainmeth 1.21.1 NeoForge migration

Status: **staging and validation only**. Branch `migration/neoforge-1.21.1`.
Minecraft 1.21.1, NeoForge 21.1.220, Java 21.

## Safety and isolation

Use a separate checkout, e.g. `/srv/minecraft/brainmeth/server-1211`. Do not switch
the existing `server/` checkout while production is running. The Docker project,
network, installer volume, containers, ports and data directories are separate from
the original 26.2 server. Deploy script blocks production and unknown older worlds.

After GitHub Actions has successfully regenerated the Packwiz metadata:

```bash
git clone --branch migration/neoforge-1.21.1 <private-repo-SSH-URL> /srv/minecraft/brainmeth/server-1211
cd /srv/minecraft/brainmeth/server-1211
./scripts/bootstrap.sh
./scripts/deploy.sh test
docker compose --profile test logs -f --tail=200 minecraft-test
```

Use a new Modrinth App instance with Minecraft 1.21.1, NeoForge 21.1.220,
Java 21 and AutoModpack 4.0.5. Connect on the isolated test port **25585**;
voice UDP port is **25584**. A fresh world will be generated.

## Test checklist

- Packwiz dependency resolution and sides for all mods.
- NeoForge boot and client connection; AutoModpack client installation.
- Sodium/Iris/BBE compatibility; shaders, DH 3.3.3 LOD world generation.
- Supplementaries, Supplementaries Squared, Amendments, Moonlight Lib and recipes.
- Worldgen, player inventory persistence and Simple Voice Chat.

Some uncertain 26.2-only mods are deferred (Krypton Reno, Jasione, Ixeris,
etc.). EMF/ETF are deferred while testing 1.21.1 BBE compatibility.
Never downgrade a 26.2 world to 1.21.1. Do not deploy production until
the new pack has passed a real server/client test.

The push-triggered GitHub workflow must generate fresh `pack/mods` metadata and
`pack/index.toml`. This staging commit alone does not prove compatibility.
