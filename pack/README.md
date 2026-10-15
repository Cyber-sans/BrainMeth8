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


Audio pack update: runtime Packwiz removes Drip Sounds and pins Sounds 2.4.18 LTS, Presence Footsteps (NeoForge), MRU, and YACL for Minecraft 1.21.1. All four new mods are client-only and placed in the recommended Ambient Audio group. Exact Modrinth file hashes are verified during staging. No server-only mods are sent to clients.

## Resource-pack defaults — temporarily disabled

Default Options client config distribution was **rolled back** after causing an
AutoModpack restart/update loop: every restart offered the same
`config/defaultoptions-common.toml` update (778→888 bytes). Default Options
uses Balm config handling and may rewrite the TOML locally; synchronising this
file directly is unsuitable for the current client arrangement.

`scripts/stage-client-mods.py` removes only the previously published
`automodpack/host-modpack/main/config/defaultoptions-common.toml` file.
The mod itself stays installed. The user's own client config is not modified.

The desired internal resource-pack IDs remain documented in
`rules/client-config/defaultoptions-common.toml` but are **not distributed**
until a restart-safe opt-in/bootstrap mechanism has been validated on a fresh
client. Existing client resource packs can still be enabled manually.

After deployment, AutoModpack must publish a fresh pack generation (usually
automatic when the server restarts). A client may see one final removal update;
subsequent restarts must not offer the same change repeatedly.
