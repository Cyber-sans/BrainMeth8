# Brainmeth Packwiz pack

This directory is the authoritative modpack definition.

Typical commands from this directory:

```bash
packwiz modrinth add <project>
packwiz curseforge add <project>
packwiz update --all
packwiz refresh
```

Packwiz marks each entry as client, server, or both. The Docker server consumes only the server-relevant side through `PACKWIZ_URL`.

AutoModpack should be one of the first real mods added. Players install AutoModpack once in a normal NeoForge 1.21.1 instance; after that it synchronises the official Brainmeth content from the running server.


## AutoModpack 5 deployment (test server)

`./scripts/deploy.sh test` obtains the **exact pinned v5.0.0-rc.4 release**
from Modrinth's API, verifies the version supports NeoForge 1.21.1,
uses its published SHA-512, and creates `.pack-runtime/` with recalculated
Packwiz manifest hashes. The checked-in `pack/` is never modified by a
deployment; `.pack-runtime/` is ignored by Git, served over the private
Docker network, and regenerated on each deploy. This avoids git pull conflicts
and the previous nginx 403 permissions problem. The live test world and its
`automodpack/` credentials are preserved.

The old v4 configuration is not used. `scripts/configure-automodpack.py`
writes `automodpack/server.conf` with v5 HOLEPUNCH transport (no separate
port), validated player secrets, the required `General/main` group, and
two **recommended/preselected** groups under `Enhancements`:
`visuals` (cosmetic/player animation mods) and `ambience` (ambient sound mods).
Gameplay, dependency, and performance mods remain required. Client files
are staged from verified Packwiz hashes; server-only files never enter the
client pack. AutoModpack itself is delivered to each launcher separately,
not through its own hosted pack.

After deploying, wait for Minecraft readiness and test from a fresh NeoForge
1.21.1 client containing AutoModpack 5 only. v5 creates a new certificate and
a new pack generation, so it will ask for trust again and download the pack
again. Keep the test server on the test profile until this is validated.

To publish changes without restarting Minecraft, use
`docker exec brainmeth1211-test rcon-cli "automodpack generate"`
(after the server is ready). The server also publishes on startup when its
content changes. Inspect `docker logs --tail=150 brainmeth1211-test` if an
update or generation fails. Avoid promoting pre-release AutoModpack to
production without a successful clean-client test.

