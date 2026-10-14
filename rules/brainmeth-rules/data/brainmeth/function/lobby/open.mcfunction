scoreboard players set #state bm_launch 1
scoreboard players set #countdown bm_launch 0
title @a title {"text":"GO!","color":"green","bold":true}
title @a subtitle {"text":"Brainmeth has begun!","color":"yellow"}
playsound minecraft:entity.ender_dragon.growl master @a ~ ~ ~ 1 1
# Release players to safe terrain near origin (surface placement handles variable world height).
execute in minecraft:overworld run spreadplayers 0 0 4 35 false @a[tag=bm_lobby]
gamemode survival @a[tag=bm_lobby]
tag @a[tag=bm_lobby] remove bm_lobby
# Remove the temporary room; don't alter the surface world.
execute in minecraft:overworld run fill -10 199 -10 10 207 10 minecraft:air
scoreboard players set #built bm_launch 0
