# Brainmeth Minecraft Server

Fresh Minecraft server stack for `cropduster`.

## Baseline

- Minecraft **26.2**
- **NeoForge 26.2.0.88**
- Java **25 / GraalVM**
- Docker Compose + `itzg/minecraft-server`
- Packwiz as the authoritative mod/config definition
- AutoModpack for client synchronisation
- GitHub for version control and custom-mod source

## Layout on cropduster

```text
/srv/minecraft/brainmeth/
├── server/   # Git repo: Compose, Packwiz, scripts, docs, custom-mod source
├── prod/     # Production Minecraft runtime data
└── test/     # Test Minecraft runtime data

/mnt/Backup3TB/minecraft/brainmeth/
└── backups/  # Daily compressed production backups
```

The Git repo contains definitions/source only. Worlds, player data, generated configs, downloaded runtime files and logs live in `prod/` or `test/`. Backups stay on the separate 3 TB backup drive.

## Ports

- production Minecraft: `25577/tcp`
- production voice: `25576/udp`
- test Minecraft: `25575/tcp`
- test voice: `25574/udp`

## Runtime defaults

- Production heap: **6G**
- Test heap: **3G**
- GraalVM 25
- MeowIce + GraalVM JVM flags
- whitelist disabled
- Docker and Minecraft log rotation enabled
- Watchtower disabled for Brainmeth containers
- daily production backup at about **05:00 local time**, with 10m / 5m / 60s in-game warnings

## First bootstrap on cropduster

Clone the private repo to:

```bash
/srv/minecraft/brainmeth/server
```

Then:

```bash
cd /srv/minecraft/brainmeth/server
./scripts/bootstrap.sh
```

Start test:

```bash
./scripts/deploy.sh test
```

Start production:

```bash
./scripts/deploy.sh prod
```

## Adding ordinary mods

Use Packwiz on the development/admin side, then commit and push:

```bash
cd pack
packwiz modrinth add <project>
# or
packwiz curseforge add <project>
git add .
git commit
git push
```

Then on `cropduster`:

```bash
cd /srv/minecraft/brainmeth/server
git pull
```

Packwiz is the source of truth. Server-only mods must be marked server-side so they are not distributed to clients.

## Custom mods

Custom NeoForge mods live in:

```text
custom-mods/
```

The initial shared mod is:

```text
custom-mods/brainmeth-core
```

Target **NeoForge 26.2 / Java 25**, build a JAR, then add the approved artifact into the Packwiz/server flow. GitHub Actions can build/validate custom mods.

## AutoModpack

AutoModpack synchronises the official required client content from the running server to players. It should be added through Packwiz so Packwiz remains the authoritative mod/version definition.
