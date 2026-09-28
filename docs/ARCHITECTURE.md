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
- **Modrinth App**: player launcher and personal client-only extras.
- **`/srv/minecraft`**: production runtime/world state, never Git-tracked.
- **`/srv/minecraft-test`**: disposable/experimental instance.

The Packwiz files are served by an internal nginx container so the GitHub repository can remain private; `itzg` consumes `http://packwiz/pack.toml` over the Docker network.
