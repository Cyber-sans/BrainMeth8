# Brainmeth Core — scheduled world launch

Dedicated-server-only NeoForge 1.21.1 / Java 21 extension for the shared Brainmeth datapack.
No client install, Docker timers, systemd timers or automated server startup.

## OP commands (tab completion)

| Command | Action |
|---|---|
| `/launch schedule 2026-10-16 18:00` | Set absolute UK local release time (24-hour clock). |
| `/launch reschedule 2026-10-17 18:00` | Move the release deadline. |
| `/launch status` | Show the schedule and time remaining. |
| `/launch cancel` | Cancel the countdown; keep waiting room locked. |
| `/launch now` | Release everyone immediately. |
| `/launch help` | Show command help. |

Only OPs (permission level ≥2) can use these commands. The server must already be running.
**No launch is scheduled on installation.**

Schedules are stored in the **individual world directory** as `brainmeth-launch.json`.
They survive disconnections, restarts, and absence of administrators.
The countdown uses `Instant.now()` and `Europe/London`; it accounts for BST/GMT
and rejects ambiguous/nonexistent local times during clock changes.
The on-screen bossbar and announcements at 60/30/10/5/1 minutes and
final seconds use the actual deadline rather than accumulated Minecraft ticks.

At/after the deadline, the mod runs the **existing**
`function brainmeth:lobby/release` through the Minecraft command dispatcher.
It checks the existing `bm_launch` scoreboard, never teleports players itself,
and never overwrites world launch state. If a server was offline at the deadline,
release happens after the world/data pack loads and the server ticks again.
If an admin uses a legacy release function, the countdown is cancelled on the next check.
The world stays released across restarts.

## Build and deployment

The GitHub workflow `Build Brainmeth server launch mod` compiles this directory
using Java 21 + Gradle 8.14.3, then commits the server-only
`server-mods/brainmeth-core.jar` on the migration branch.
Wait for the workflow to succeed and **git pull again** to get that JAR.
The migration deploy script injects the JAR into the runtime Packwiz index
as `side = "server"`, with verified SHA-256 and an internal Docker-network URL.
Clients do not download the mod.

The **existing 26.2 production world remains untouched**: the migration deployment
explicitly refuses `./scripts/deploy.sh prod`. Do not copy a 1.21.1 mod to 26.2.

## Non-destructive test plan

1. Run `python3 scripts/verify-lobby.py` and `python3 scripts/verify-launch.py`.
2. Boot the isolated test world and run `bash scripts/smoke-test-lobby.sh`.
3. Join with two players; verify fists deal damage and a killed player respawns inside the glass.
4. Complete the cyan/gold/magenta course, check the lap counter, reconnect.
5. Run `/launch schedule <tomorrow> 18:00`, confirm bossbar/status, restart test server,
   verify deadline persisted, then `/launch cancel` and verify bar disappears.
6. On the **test world only**, schedule a release a couple of minutes away,
   log the OP out, let the server release everyone unattended, and verify no
   duplicate release after a restart. This is intentionally not scheduled automatically.

