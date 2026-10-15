# Adventure blocks griefing but still allows PvP, punching, sprinting and parkour.
# No Resistance: the prior lounge inadvertently made everyone invulnerable.
tag @a[tag=bm_staff,tag=bm_lobby] remove bm_lobby
execute as @a[tag=!bm_staff,tag=!bm_lobby_seen] run title @s title {"text":"BRAINMETH  |  LAUNCH LOUNGE","color":"aqua","bold":true}
execute as @a[tag=!bm_staff,tag=!bm_lobby_seen] run title @s subtitle {"text":"PvP is live • follow cyan to magenta parkour","color":"yellow"}
tag @a[tag=!bm_staff,tag=!bm_lobby_seen] add bm_lobby_seen
tag @a[tag=!bm_staff] add bm_lobby
# Apply spawnpoint before any arena kills; initialize course progress on first entry.
execute as @a[tag=bm_lobby,tag=!bm_lobby_spawned] in minecraft:overworld run spawnpoint @s 0 201 0
scoreboard players set @a[tag=bm_lobby,tag=!bm_lobby_spawned] bm_course 0
effect clear @a[tag=bm_lobby,tag=!bm_lobby_spawned] minecraft:resistance
tag @a[tag=bm_lobby,tag=!bm_lobby_spawned] add bm_lobby_spawned
gamemode adventure @a[tag=bm_lobby,gamemode=!adventure]
execute as @a[tag=bm_lobby] at @s unless dimension minecraft:overworld in minecraft:overworld run tp @s 0 201 0
execute as @a[tag=bm_lobby] at @s if dimension minecraft:overworld unless entity @s[x=-23,y=201,z=-23,dx=46,dy=24,dz=46] run tp @s 0 201 0
# Strength II makes unarmed fights winnable; do not grant resistance or rapid regeneration.
effect give @a[tag=bm_lobby] minecraft:strength 3 1 true
