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

AutoModpack should be one of the first real mods added. Players install AutoModpack once in a normal NeoForge 26.2 instance; after that it synchronises the official Brainmeth content from the running server.
