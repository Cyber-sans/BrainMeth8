# The atrium is a live structure, not a misleading scoreboard flag.
# Do not teleport players into an unbuilt room; wait for all four outer chunks to load.
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -24 205 5 minecraft:cyan_stained_glass run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block 0 226 0 minecraft:light_blue_stained_glass run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -18 201 -18 minecraft:cyan_concrete run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -7 222 -19 minecraft:gold_block run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 unless score #layout bm_launch matches 3 run function brainmeth:lobby/build
# Upgrade signage in-place on already-built v3 lobbies; never clear or rebuild the room for text changes.
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 in minecraft:overworld if loaded 0 205 0 unless score #signage bm_launch matches 1 run function brainmeth:lobby/signage
# The expert route is constructed once even for lobbies built before this release.
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 in minecraft:overworld if loaded 11 223 18 if score #bonus bm_launch matches 1 unless block 11 223 18 minecraft:emerald_block run scoreboard players set #bonus bm_launch 0
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 in minecraft:overworld if loaded 11 223 18 unless score #bonus bm_launch matches 1 run function brainmeth:lobby/bonus
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run function brainmeth:lobby/locked
# Checkpoint is reached by walking on the elevated gold platform, not standing on the floor below.
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,x=-9,y=214,z=3,dx=2,dy=1,dz=2] run scoreboard players set @s bm_course 1
# Finishing the existing magenta section earns a normal lap and unlocks the optional expert route.
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,scores={bm_course=1},x=-8,y=223,z=-20,dx=2,dy=1,dz=2] run function brainmeth:lobby/parkour_standard
# The emerald platform is reached only after the magenta checkpoint/finish.
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,scores={bm_course=2},x=11,y=224,z=18,dx=1,dy=1,dz=1] run function brainmeth:lobby/parkour_finish
# Once the player returns to the start, reset the expert unlock for a fresh normal lap.
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,scores={bm_course=2},x=-19,y=202,z=-19,dx=2,dy=1,dz=2] run scoreboard players set @s bm_course 0
# Repair players who still have the legacy sky spawnpoint, including already-released players who lost bm_lobby.
# bm_lobby_seen survives launch, so it is a reliable marker for affected accounts.
execute if score #state bm_launch matches 1 in minecraft:overworld run tag @a[tag=bm_lobby_seen,x=-24,y=190,z=-24,dx=48,dy=192,dz=48] add bm_launch_rescue
execute if score #state bm_launch matches 1 in minecraft:overworld run tag @a[tag=bm_lobby,x=-24,y=190,z=-24,dx=48,dy=192,dz=48] add bm_launch_rescue
execute if score #state bm_launch matches 1 in minecraft:overworld run spreadplayers 200 200 8 32 false @a[tag=bm_launch_rescue]
execute if score #state bm_launch matches 1 as @a[tag=bm_launch_rescue] at @s run spawnpoint @s ~ ~ ~
execute if score #state bm_launch matches 1 run tag @a[tag=bm_launch_rescue] remove bm_launch_rescue
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] at @s run spawnpoint @s ~ ~ ~
execute if score #state bm_launch matches 1 run gamemode survival @a[tag=bm_lobby]
execute if score #state bm_launch matches 1 run effect clear @a[tag=bm_lobby] minecraft:strength
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby_spawned
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby
