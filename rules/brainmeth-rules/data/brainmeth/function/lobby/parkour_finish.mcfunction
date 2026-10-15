# Reaching the elevated gold finish from the checkpoint counts one lap.
scoreboard players add @s bm_bonus 1
scoreboard players set @s bm_course 0
title @s title {"text":"EXPERT COURSE COMPLETE!","color":"gold","bold":true}
title @s subtitle {"text":"One more lap?","color":"aqua"}
tellraw @s [{"text":"Brainmeth expert completions: ","color":"yellow"},{"score":{"name":"@s","objective":"bm_bonus"},"color":"white"}]
execute at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1
execute at @s run particle minecraft:firework ~ ~1 ~ 0.5 0.5 0.5 0.03 24 normal
execute in minecraft:overworld run tp @s -18 202 -18
