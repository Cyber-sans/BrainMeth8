scoreboard players set #state bm_launch 1
scoreboard players set #countdown bm_launch 0
title @a title {"text":"GO!","color":"green","bold":true}
title @a subtitle {"text":"Brainmeth has begun!","color":"yellow"}
execute as @a at @s run playsound minecraft:entity.ender_dragon.growl master @s ~ ~ ~ 1 1
# Release all waiting players, including staff who are still inside the room.
execute in minecraft:overworld run spreadplayers 0 0 4 35 false @a[tag=bm_lobby]
execute in minecraft:overworld as @a[tag=bm_staff,x=-24,y=199,z=-24,dx=48,dy=25,dz=48] run spreadplayers 0 0 4 35 false @s
gamemode survival @a[tag=bm_lobby]
tag @a[tag=bm_lobby] remove bm_lobby
# Remove the temporary room; don't alter the surface world.
execute in minecraft:overworld run kill @e[type=minecraft:text_display,tag=bm_lobby_decor]
execute in minecraft:overworld run fill -24 199 -24 24 211 24 minecraft:air
execute in minecraft:overworld run fill -24 212 -24 24 224 24 minecraft:air
scoreboard players set #layout bm_launch 0
scoreboard players set #built bm_launch 0
