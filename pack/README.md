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

## First-run resource packs

Brainmeth distributes `rules/client-config/defaultoptions-common.toml` through
AutoModpack's **Essential/main** client configuration at
`host-modpack/main/config/defaultoptions-common.toml`.
The already-installed Default Options client mod reads
`config/defaultoptions-common.toml` and enables the 13 selected internal
resource-pack IDs shown in the pack-author screenshot, including the three
voice-chat icon styles, Naturalist spawn eggs, Continuity glass fixes, Vinery
foliage, Vanilla Backport animations, Supplementaries ropes, Moonlight
resources, Eating Animations compatibility, and the Minecraft base packs.
Priority order matches the selected column.

Default Options applies these IDs once using its own journal. Never ship
`options.txt` or `defaultoptions.journal.json`: normal user changes must
remain possible. A user who has already had resource-pack defaults applied
may need to enable new selections manually. Optional cosmetic mods omitted
by the user can make their built-in resource packs unavailable; Default Options
will skip missing IDs rather than crash. Note that the three voice-chat icon
styles overlap, but their order matches the provided selected list.

Validate the staged file with `python3 scripts/verify-resource-packs.py` and,
after deployment, compare the synced client config with
`rules/client-config/defaultoptions-common.toml`. Check the selected packs on
a clean 1.21.1 client after AutoModpack has synchronized; this is not
guaranteed by the static tests.
