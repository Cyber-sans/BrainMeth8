# OP can return to the waiting room after /function brainmeth:lobby/escape.
execute unless score #state bm_launch matches 0 run tellraw @s {"text":"Launch has already started; the waiting room is closed.","color":"red"}
execute if score #state bm_launch matches 0 unless score #layout bm_launch matches 3 run tellraw @s {"text":"The glass lounge is still being constructed. Try again shortly.","color":"yellow"}
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run tag @s remove bm_staff
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run tag @s remove bm_lobby_spawned
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run tag @s remove bm_lobby_seen
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run tag @s add bm_lobby
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 run scoreboard players set @s bm_course 0
execute if score #state bm_launch matches 0 if score #layout bm_launch matches 3 in minecraft:overworld run tp @s 0 201 0
