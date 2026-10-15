# Begin actual survival; irreversible without an explicit lobby reset.
scoreboard players set #state bm_launch 1
scoreboard players set #countdown bm_launch 0
title @a title {"text":"GO!","color":"green","bold":true}
title @a subtitle {"text":"Brainmeth has begun!","color":"yellow"}
execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 1
# Move participants to terrain BEFORE clearing the glass sky arena.
execute in minecraft:overworld run spreadplayers 0 0 4 35 false @a[tag=bm_lobby]
execute in minecraft:overworld as @a[tag=bm_staff,x=-24,y=199,z=-24,dx=48,dy=29,dz=48] run spreadplayers 0 0 4 35 false @s
execute as @a[tag=bm_lobby] at @s run spawnpoint @s ~ ~ ~
gamemode survival @a[tag=bm_lobby]
effect clear @a[tag=bm_lobby] minecraft:strength
tag @a[tag=bm_lobby] remove bm_lobby_spawned
tag @a[tag=bm_lobby] remove bm_lobby
# Cleanup only the self-contained sky lounge, preserving the surface.
execute in minecraft:overworld run kill @e[type=minecraft:text_display,tag=bm_lobby_decor]
execute in minecraft:overworld run fill -24 199 -24 24 205 24 minecraft:air
execute in minecraft:overworld run fill -24 206 -24 24 212 24 minecraft:air
execute in minecraft:overworld run fill -24 213 -24 24 219 24 minecraft:air
execute in minecraft:overworld run fill -24 220 -24 24 226 24 minecraft:air
execute in minecraft:overworld run forceload remove -24 -24 24 24
scoreboard players set #layout bm_launch 0
scoreboard players set #built bm_launch 0
scoreboard players set #bonus bm_launch 0
