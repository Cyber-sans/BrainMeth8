# One completed lap: record the total and return the player to the start.
scoreboard players add @s bm_parkour 1
title @s title {"text":"PARKOUR COMPLETE!","color":"gold","bold":true}
title @s subtitle {"text":"Try for another lap!","color":"aqua"}
tellraw @s [{"text":"Brainmeth parkour laps: ","color":"yellow"},{"score":{"name":"@s","objective":"bm_parkour"},"color":"white"}]
execute at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1
execute at @s run particle minecraft:firework ~ ~1 ~ 0.5 0.5 0.5 0.03 24 normal
tp @s -18 201 -18
