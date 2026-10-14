#!/usr/bin/env python3
"""Validate client group tier assignments without downloading any mod jars.

Run after preparing the complete .pack-runtime. The mandatory fallback protects
new core mods until they have been audited for optional-client installation.
"""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
import tomllib

RANK = {"main": 0, "recommended": 1, "extras": 2}
REQUIRED_DEPENDENCIES = {
    "sounds": ("mru", "yacl"),
    "better-animations-collection": ("puzzles-lib",),
    "blur-plus": ("midnightlib",),
    "better-stats": ("tcdcommons",),
    "eating-animation": ("groovy-mod-loader",),
    "effectual": ("tlib",),
    "item-highlighter": ("iceberg",),
    "legendary-tooltips": ("iceberg", "prism-lib"),
    "entity-model-features": ("entitytexturefeatures",),
    "continuity-neoforged": ("sodium",),
    "distant-horizons-seedgen": ("distanthorizons",),
    "reeses-sodium-options": ("sodium", "sodium-extra"),
}

def client_sets(source: Path) -> tuple[set[str], set[str]]:
    tree = ast.parse(source.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    names = {}
    for statement in fn.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            if statement.targets[0].id in {"recommended_mods", "extra_mods"}:
                names[statement.targets[0].id] = set(ast.literal_eval(statement.value))
    assert set(names) == {"recommended_mods", "extra_mods"}, "Missing client group definitions"
    return names["recommended_mods"], names["extra_mods"]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-root", default=".pack-runtime")
    args = ap.parse_args()
    root = Path(args.pack_root).resolve()
    scripts = Path(__file__).resolve().parent
    recommended, extras = client_sets(scripts / "stage-client-mods.py")
    assert not (recommended & extras), "Mod assigned to multiple optional groups"

    entries = {}
    server = set()
    for file in (root / "mods").glob("*.pw.toml"):
        slug = file.name.removesuffix(".pw.toml")
        info = tomllib.loads(file.read_text(encoding="utf-8"))
        if info["side"] == "server":
            server.add(slug)
        elif slug != "automodpack":
            entries[slug] = info["filename"]
    assert entries, "No Packwiz client metadata found"
    unknown = (recommended | extras) - set(entries)
    assert not unknown, f"Mods assigned to groups but absent from client runtime: {sorted(unknown)}"

    def group(mod: str) -> str:
        if mod in recommended:
            return "recommended"
        if mod in extras:
            return "extras"
        return "main"

    # Recommended must work without Extras; Extras declares it requires Recommended.
    for mod, dependencies in REQUIRED_DEPENDENCIES.items():
        if mod not in entries:
            continue
        for dependency in dependencies:
            assert dependency in entries, f"{mod}: required client dependency {dependency} missing"
            assert RANK[group(dependency)] <= RANK[group(mod)], (
                f"{mod} ({group(mod)}) depends on {dependency} ({group(dependency)}), "
                "which may be deselected"
            )
    assert not (server & (recommended | extras)), "Server-only mods may not enter client selections"

    import importlib.util
    spec = importlib.util.spec_from_file_location("brainmeth_config", scripts / "configure-automodpack.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cfg = module.CONFIG
    assert cfg.count("  General {") == 1, "Expected one category"
    for group_id, label, selection in (
        ("main", "Essential", "REQUIRED"),
        ("recommended", "Recommended", "RECOMMENDED"),
        ("extras", "Extras", "OPTIONAL"),
    ):
        assert f"    {group_id} {{\n      display-name: \"{label}\"" in cfg
        assert f"      selection: {selection}" in cfg
    assert "requires: [main, recommended]" in cfg, "Extras need Recommended for shared dependencies"
    totals = {group_id: sum(group(slug) == group_id for slug in entries) for group_id in RANK}
    print("Validated client groups: " + ", ".join(f"{key}={num}" for key, num in totals.items()))
    print(f"Excluded server-only mods: {len(server)}")

if __name__ == "__main__":
    main()
