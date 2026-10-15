# The atrium is a live structure, not a misleading scoreboard flag.
# Do not teleport players into an unbuilt room; wait for all four outer chunks to load.
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -24 205 5 minecraft:cyan_stained_glass run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block 0 226 0 minecraft:light_blue_stained_glass run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -18 201 -18 minecraft:cyan_concrete run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 if score #layout bm_launch matches 3 unless block -7 222 -19 minecraft:gold_block run scoreboard players set #layout bm_launch 0
execute if score #state bm_launch matches 0 in minecraft:overworld if loaded -24 205 -24 if loaded -24 205 24 if loaded 24 205 -24 if loaded 24 205 24 unless score #layout bm_launch matches 3 run function brainmeth:lobby/build
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run function brainmeth:lobby/locked
# Checkpoint is reached by walking on the elevated gold platform, not standing on the floor below.
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,x=-9,y=214,z=3,dx=2,dy=1,dz=2] run scoreboard players set @s bm_course 1
execute if score #state bm_launch matches 0 in minecraft:overworld as @a[tag=bm_lobby,scores={bm_course=1..},x=-8,y=223,z=-20,dx=2,dy=1,dz=2] run function brainmeth:lobby/parkour_finish
# Persisted pre-launch spawnpoints are reset when a player returns after launch.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] at @s if dimension minecraft:overworld if entity @s[x=-24,y=199,z=-24,dx=48,dy=29,dz=48] in minecraft:overworld run spreadplayers 0 0 4 35 false @s
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] at @s run spawnpoint @s ~ ~ ~
execute if score #state bm_launch matches 1 run gamemode survival @a[tag=bm_lobby]
execute if score #state bm_launch matches 1 run effect clear @a[tag=bm_lobby] minecraft:strength
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby_spawned
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby
