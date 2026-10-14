scoreboard players set #countdown bm_launch 1
title @a title {"text":"BRAINMETH","color":"gold","bold":true}
title @a subtitle {"text":"Launching in 10 seconds","color":"yellow"}
playsound minecraft:block.note_block.pling master @a ~ ~ ~ 1 1
schedule function brainmeth:lobby/countdown_5 5s replace
