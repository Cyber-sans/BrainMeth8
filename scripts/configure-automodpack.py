#!/usr/bin/env python3
"""Configure AutoModpack 4.0.5 so Brainmeth clients get only the staged Packwiz payload."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SYNCED_FILES = [
    "/kubejs/**",
    "!/kubejs/server_scripts/**",
    "/emotes/*",
]


def fresh_config() -> dict:
    # AutoModpack 4.0.5 ServerConfigFieldsV2.
    return {
        "DO_NOT_CHANGE_IT": 2,
        "modpackName": "Brainmeth",
        "modpackHost": True,
        "generateModpackOnStart": True,
        "syncedFiles": SYNCED_FILES,
        "allowEditsInFiles": ["/options.txt", "/config/**"],
        "forceCopyFilesToStandardLocation": [],
        "nonModpackFilesToDelete": {},
        "autoExcludeServerSideMods": True,
        "autoExcludeUnnecessaryFiles": True,
        "requireAutoModpackOnClient": True,
        "nagUnModdedClients": True,
        "nagMessage": "This server provides dedicated modpack through AutoModpack!",
        "nagClickableMessage": "Click here to get the AutoModpack!",
        "nagClickableLink": "https://modrinth.com/project/automodpack",
        "bindAddress": "",
        "bindPort": -1,
        "addressToSend": "",
        "portToSend": -1,
        "disableInternalTLS": False,
        "requireMagicPackets": False,
        "updateIpsOnEveryStart": False,
        "bandwidthLimit": 0,
        "validateSecrets": True,
        "secretLifetime": 336,
        "selfUpdater": False,
        "acceptedLoaders": ["neoforge"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    args = ap.parse_args()

    amp = Path(args.data_root).resolve() / "automodpack"
    amp.mkdir(parents=True, exist_ok=True)
    conf = amp / "automodpack-server.json"

    if conf.exists():
        try:
            data = json.loads(conf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid AutoModpack JSON in {conf}: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected AutoModpack config shape in {conf}")
    else:
        data = fresh_config()

    # AutoModpack 4.0.5 uses syncedFiles. Deliberately omit /mods/*.jar:
    # client/both mods are staged into automodpack/host-modpack/main/mods instead.
    data["syncedFiles"] = list(SYNCED_FILES)
    if not data.get("modpackName"):
        data["modpackName"] = "Brainmeth"

    conf.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    # A short-lived earlier Brainmeth deploy wrote the newer AutoModpack 4.0.6+
    # server.conf format. AutoModpack 4.0.5 ignores it, so remove only our copy.
    wrong = amp / "server.conf"
    if wrong.exists():
        text = wrong.read_text(encoding="utf-8", errors="replace")
        if "Brainmeth-managed AutoModpack server configuration" in text:
            wrong.unlink()
            print(f"Removed ignored AutoModpack config from newer schema: {wrong}")

    print(f"Configured AutoModpack 4.0.5: {conf}")
    print(f"AutoModpack syncedFiles: {data['syncedFiles']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
