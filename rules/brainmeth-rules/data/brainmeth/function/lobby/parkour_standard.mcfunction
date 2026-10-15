# Earn the normal lap at the original gold finish without teleporting the player.
# The optional orange expert route begins directly from this platform.
scoreboard players add @s bm_parkour 1
scoreboard players set @s bm_course 2
title @s title {"text":"PARKOUR COMPLETE!","color":"gold","bold":true}
title @s subtitle {"text":"Expert route unlocked! Follow the orange jumps.","color":"red"}
tellraw @s [{"text":"Brainmeth standard laps: ","color":"yellow"},{"score":{"name":"@s","objective":"bm_parkour"},"color":"white"}]
execute at @s run playsound minecraft:ui.toast.challenge_complete master @s ~ ~ ~ 1 1
