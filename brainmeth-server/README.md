# Brainmeth Minecraft Server

Fresh Minecraft server stack for `cropduster`.

## Baseline

- Minecraft **26.2**
- **NeoForge 26.2.0.88**
- Java **25**
- Docker Compose
- `itzg/minecraft-server`
- Packwiz as the authoritative modpack definition
- AutoModpack for player synchronisation
- Modrinth App as the recommended player launcher
- GitHub Actions for custom mod validation/builds

NeoForge 26.2 officially targets Java 25-era Minecraft. The custom mod project is based on the current NeoForge 26.2 ModDevGradle template.

## Repository vs runtime

This repository contains definitions and source code. It intentionally does **not** contain worlds, player data, backups, logs, credentials, or generated runtime state.

Production runtime:

```text
/srv/minecraft
```

Test runtime:

```text
/srv/minecraft-test
```

## First bootstrap on cropduster

```bash
git clone <private-repo-url> /opt/brainmeth-server
cd /opt/brainmeth-server
./scripts/bootstrap.sh
```

Start the test instance first:

```bash
./scripts/deploy.sh test
```

Production, once tested:

```bash
./scripts/deploy.sh prod
```

Ports:

- production Minecraft: `25565/tcp`
- production voice: `24454/udp`
- test Minecraft: `25566/tcp`
- test voice: `24455/udp`

## Adding ordinary mods

Install Packwiz on the admin/development machine, then from `pack/`:

```bash
packwiz modrinth add <project>
# or
packwiz curseforge add <project>
```

Commit the resulting TOML changes. Deploy to **test** before production.

## Custom mods

Small shared Brainmeth mechanics live in:

```text
custom-mods/brainmeth-core
```

The initial project targets NeoForge 26.2 and Java 25. CI builds the JAR on every push/PR.

## AutoModpack

AutoModpack is intentionally part of the architecture but is not hard-coded into the empty Packwiz skeleton. Add its current NeoForge 26.2 release through Packwiz as the first pack dependency so Packwiz remains the single authoritative mod/version definition.

Players install AutoModpack once into a normal NeoForge 26.2 Modrinth instance; after that it synchronises the official server pack.

See `docs/PLAYER_SETUP.md`.
