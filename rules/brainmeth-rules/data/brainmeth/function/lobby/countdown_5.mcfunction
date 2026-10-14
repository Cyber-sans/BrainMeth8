execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 run title @a title {"text":"5","color":"gold"}
execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 as @a at @s run playsound minecraft:block.note_block.pling master @s ~ ~ ~ 1 1
execute if score #state bm_launch matches 0 if score #countdown bm_launch matches 1 run schedule function brainmeth:lobby/countdown_4 1s replace
