# Iron golems get 2x vanilla health (100 -> 200) and 2x attack damage (15 -> 30).
# Runs every 2 seconds; each golem is buffed once and tagged so it isn't re-healed.
execute as @e[type=minecraft:iron_golem,tag=!bm_buffed] run function brainmeth:golems/apply
schedule function brainmeth:golems/buff 40t replace
