#!/usr/bin/env python3
"""Stage the explicit Packwiz client payload into AutoModpack's host-modpack area.

Only Packwiz entries marked client or both are published to clients.
Essential is mandatory, Recommended is preselected, Extras is opt-in. Server-only
mods stay in /data/mods for NeoForge but never enter AutoModpack's client pack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import shutil
import tomllib
import urllib.request
from urllib.parse import quote


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm.replace("-", ""))
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-root", required=True)
    ap.add_argument("--data-root", required=True)
    args = ap.parse_args()

    pack_root = Path(args.pack_root).resolve()
    data_root = Path(args.data_root).resolve()
    base = data_root / "automodpack" / "host-modpack"
    # Everything not in these curated lists is Essential by default. This is
    # deliberately conservative: a new gameplay mod or shared library must not
    # accidentally land in a group players may deselect.
    recommended_mods = {
        "3dskinlayers",
        "ambientsounds",
        "appleskin",
        "badoptimizations",
        "better-advancements",
        "better-block-entities",
        "betterf3",
        "c2me-neoforge",
        "chat-heads",
        "client-tweaks",
        "controlling",
        "crash-assistant",
        "cut-through",
        "default-options",
        "distant-horizons-seedgen",
        "distanthorizons",
        "dynamic-fps",
        "enchantment-descriptions",
        "entityculling",
        "entitytexturefeatures",
        "fast-ip-ping",
        "ferrite-core",
        "immediatelyfast",
        "inventory-essentials",
        "iris",
        "just-zoom",
        "lambdynamiclights",
        "lithium",
        "modernfix",
        "moreculling",
        "mouse-tweaks",
        "mru",
        "particle-core",
        "presence-footsteps",
        "reeses-sodium-options",
        "rei",
        "searchables",
        "shulkerboxtooltip",
        "sodium",
        "sodium-extra",
        "sound-physics-remastered",
        "sounds",
        "yacl",
    }
    extra_mods = {
        "advancement-plaques",
        "better-animations-collection",
        "better-ping-display",
        "blur-plus",
        "chatanimation",
        "continuity-neoforged",
        "eating-animation",
        "effectual",
        "entity-model-features",
        "falling-leaves",
        "groovy-mod-loader",
        "item-highlighter",
        "legendary-tooltips",
        "midnightlib",
        "not-enough-animations",
        "polytone",
        "screenshot-to-clipboard",
        "tlib",
        "visuality-forge",
        "wavey-capes",
    }
    assert not (recommended_mods & extra_mods), "Client groups must be disjoint"

    def group_for(meta: Path) -> str:
        name = meta.name.removesuffix(".pw.toml")
        if name in extra_mods:
            return "extras"
        if name in recommended_mods:
            return "recommended"
        return "main"

    # Source of truth for output group ids is AutoModpack server.conf.
    for group in ("main", "recommended", "extras"):
        (base / group / "mods").mkdir(parents=True, exist_ok=True)

    state_file = data_root / "automodpack" / ".brainmeth-packwiz-client-files.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    wanted: dict[str, dict[str, str]] = {}

    for meta in sorted((pack_root / "mods").rglob("*.pw.toml")):
        with meta.open("rb") as f:
            info = tomllib.load(f)
        if info.get("side") not in {"client", "both"}:
            continue

        # AutoModpack distributes/updates itself separately and must not be
        # embedded inside its own hosted pack.
        if meta.name == "automodpack.pw.toml":
            continue

        filename = info["filename"]
        dl = info["download"]
        if Path(filename).name != filename or filename in {".", ".."}:
            raise ValueError(f"Unsafe mod filename in {meta}: {filename!r}")
        urls = []
        if dl.get("url"):
            urls.append(dl["url"])
        elif dl.get("mode") == "metadata:curseforge":
            cf = info.get("update", {}).get("curseforge", {})
            if "file-id" not in cf or "project-id" not in cf:
                raise ValueError(f"Missing CurseForge file/project ID: {meta}")
            file_id = int(cf["file-id"])
            project_id = int(cf["project-id"])
            cdn_path = f"{file_id // 1000}/{file_id % 1000}/{quote(filename)}"
            urls.extend([
                f"https://mediafilez.forgecdn.net/files/{cdn_path}",
                f"https://edge.forgecdn.net/files/{cdn_path}",
                f"https://www.curseforge.com/api/v1/mods/{project_id}/files/{file_id}/download",
            ])
        else:
            raise ValueError(f"Unsupported Packwiz download mode in {meta}: {dl!r}")
        if filename in wanted:
            raise ValueError(f"Duplicate mod filename in Packwiz: {filename}")
        wanted[filename] = {
            "group": group_for(meta),

            "urls": urls,
            "hash_format": dl.get("hash-format", "sha256"),
            "hash": dl["hash"],
        }

    try:
        prev_data = json.loads(state_file.read_text(encoding="utf-8"))
        previous = ({name: "main" for name in prev_data}
                    if isinstance(prev_data, list) else dict(prev_data))
    except (FileNotFoundError, json.JSONDecodeError):
        previous = {}

    for filename, old_group in sorted(previous.items()):
        if filename not in wanted or old_group != wanted[filename]["group"]:
            old_path = base / old_group / "mods" / filename
            if old_path.is_file():
                if filename in wanted and digest(old_path, wanted[filename]["hash_format"]) == wanted[filename]["hash"].lower():
                    new_path = base / wanted[filename]["group"] / "mods" / filename
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(old_path, new_path)
                print(f"Removing obsolete staged location: {old_group}/{filename}")
                old_path.unlink()

    for filename, spec in wanted.items():
        target = base / spec["group"] / "mods"
        dest = target / filename
        algo = spec["hash_format"].replace("-", "")

        if dest.is_file() and digest(dest, algo) == spec["hash"].lower():
            print(f"Client mod already current: {filename}")
            continue

        print(f"Downloading client-pack mod: {filename}", flush=True)
        failures = []
        tmp_path = None
        for url in spec["urls"]:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Brainmeth-Packwiz-Client-Stager/1.0"},
                )
                with urllib.request.urlopen(req, timeout=60) as response, tempfile.NamedTemporaryFile(
                    dir=target, delete=False
                ) as tmp:
                    tmp_path = Path(tmp.name)
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        tmp.write(chunk)
                actual = digest(tmp_path, algo)
                if actual != spec["hash"].lower():
                    raise RuntimeError(
                        f"Hash mismatch: expected {spec['hash']}, got {actual}"
                    )
                break
            except (OSError, RuntimeError) as exc:
                failures.append(f"{url}: {exc}")
                if tmp_path is not None:
                    tmp_path.unlink(missing_ok=True)
                    tmp_path = None
        if tmp_path is None:
            raise RuntimeError(
                f"Unable to download verified client mod {filename}. "
                "CurseForge may restrict automated downloads. Tried:\\n  "
                + "\\n  ".join(failures)
            )
        tmp_path.replace(dest)

    # Default Options/Balm rewrites its own common TOML on the client.
    # Publishing it with AutoModpack caused a persistent 778B -> 888B
    # restart/update loop. Remove only this previously staged file;
    # leave other client configs, mods and user preferences untouched.
    legacy_defaults = base / "main" / "config" / "defaultoptions-common.toml"
    if legacy_defaults.exists():
        legacy_defaults.unlink()
        print("Removed looping Default Options client config from AutoModpack payload.")
    # Never delete the user's own client-side config file here.

    state_file.write_text(json.dumps({name: spec["group"] for name, spec in sorted(wanted.items())}, indent=2) + "\n")
    print(f"Staged {len(wanted)} Packwiz client/both mod(s) across AutoModpack v5 groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
