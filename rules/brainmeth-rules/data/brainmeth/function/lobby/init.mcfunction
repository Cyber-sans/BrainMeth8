# Persistent across reloads/restarts. Release is never undone automatically.
scoreboard objectives add bm_launch dummy
scoreboard objectives add bm_parkour dummy
execute unless score #state bm_launch matches 0..1 run scoreboard players set #state bm_launch 0
execute if score #state bm_launch matches 0 unless score #layout bm_launch matches 2 run function brainmeth:lobby/build
