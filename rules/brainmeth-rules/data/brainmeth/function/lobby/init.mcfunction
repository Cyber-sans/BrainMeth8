# The same datapack lifecycle is used for any Brainmeth environment (test or future production).
scoreboard objectives add bm_launch dummy
scoreboard objectives add bm_parkour dummy
scoreboard objectives add bm_course dummy
# Released worlds stay released after restart; missing state means not launched.
execute unless score #state bm_launch matches 0..1 run scoreboard players set #state bm_launch 0
# Keep the 49x49 build footprint loaded before any /fill or /setblock runs.
execute if score #state bm_launch matches 0 in minecraft:overworld run forceload add -24 -24 24 24
# Force upgrade from the previous, broken layout even if its "built" flag survived a restart.
execute if score #state bm_launch matches 0 unless score #layout bm_launch matches 3 run scoreboard players set #layout bm_launch 0
