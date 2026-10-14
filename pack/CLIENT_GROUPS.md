# Brainmeth AutoModpack client groups

The **test** AutoModpack 5 pack presents three groups, all preselected by default. There is no more
standalone Visual Enhancements or Ambient Audio group.

| Group id / folder | Player label | Selection | Contents |
|---|---|---|---|
| `main` | **Essential** | REQUIRED | Gameplay content, networking, and conservative mandatory/shared dependencies. |
| `recommended` | **Recommended** | RECOMMENDED (preselected) | Client performance, Distant Horizons/SeedGen, shaders and everyday quality-of-life/audio. |
| `extras` | **Extras** | RECOMMENDED (preselected, can be deselected) | Cosmetic particles, alternative animations and preference-based UI. |

Examples of **Recommended**: Sodium, Iris, Distant Horizons, DH SeedGen,
ModernFix, Lithium, AppleSkin, 3D Skin Layers, AmbientSounds, Sounds,
Presence Footsteps and Sound Physics Remastered.

Examples of **Extras**: Better Animations Collection, Effectual,
Falling Leaves, Particle Rain, Eating Animation, EMF, Blur+,
Continuity: NeoForged, and Item Highlighter.

**Dependencies and selection:** Both Recommended and Extras are enabled by default but can be deselected. Extras requires Recommended, so a player
who checks Extras also receives the performance and common libraries
in Recommended. This avoids a mod in Extras starting without a mod in
Recommended that it needs. Libraries required by core game content
remain in Essential even when their only visible function is client QoL.

**Server-only mods:** Only Packwiz metadata with `side = "client"` or
`side = "both"` is staged for AutoModpack. Mods marked `side = "server"`
remain on the Minecraft server and are never copied into any client group.
AutoModpack itself is installed separately and excluded from its own payload.

**Migration:** The required `main` group id is retained to preserve core
identity. The old `visuals` and `ambience` ids are retired. The staging
script migrates previously tracked jar files to their new group
directories and removes their old tracked copies. Existing client
selections for the retired groups won't apply to the new group ids.
Players should inspect the choices on their first reconnect.

**Safety:** `scripts/verify-client-groups.py` checks group assignments,
known cross-group dependencies, group configuration and server-only
exclusions on deploy. The classification is conservative: mods not
explicitly classified as Recommended or Extras default to Essential.
A successful Minecraft client boot with each selection combination is
still required before regarding these categories as runtime-tested.

This configuration applies only to the test migration branch.
