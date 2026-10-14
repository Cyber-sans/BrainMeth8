execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 run title @a title {"text":"2","color":"gold"}
execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 run playsound minecraft:block.note_block.pling master @a ~ ~ ~ 1 1.4000000000000001
execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 run schedule function brainmeth:lobby/countdown_1 1s replace
