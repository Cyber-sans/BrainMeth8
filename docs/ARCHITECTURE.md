# Architecture

```text
Private GitHub repository
  |
  +-- Packwiz definition -----------------------+
  |                                             |
  +-- custom mod source -> GitHub Actions       |
  |                                             v
  +-- Docker Compose -> internal Packwiz HTTP -> itzg/minecraft-server
                                                |
                                                v
                                         NeoForge 26.2 server
                                                |
                                                v
                                           AutoModpack
                                                |
                                                v
                                              players
```

## Ownership

- **GitHub**: source of truth, review/history, custom-mod source.
- **Packwiz**: official mod/config/version definition.
- **Docker Compose + itzg**: reproducible runtime.
- **AutoModpack**: client synchronisation of the running official pack.
- **`/srv/minecraft/brainmeth/server`**: Git checkout and admin/control files.
- **`/srv/minecraft/brainmeth/prod`**: production runtime/world state, never Git-tracked.
- **`/srv/minecraft/brainmeth/test`**: disposable/experimental runtime.
- **`/mnt/Backup3TB/minecraft/brainmeth/backups`**: production backups on the separate 3 TB drive.

The Packwiz files are served by an internal nginx container so the GitHub repository can remain private; `itzg` consumes `http://packwiz/pack.toml` over the Docker network.
