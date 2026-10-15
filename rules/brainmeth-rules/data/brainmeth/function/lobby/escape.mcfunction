# Staff-only intentional opt-out. Use /function brainmeth:lobby/enter to rejoin.
tag @s add bm_staff
tag @s remove bm_lobby
tag @s remove bm_lobby_spawned
effect clear @s minecraft:strength
gamemode survival @s
execute in minecraft:overworld run spreadplayers 0 0 4 35 false @s
execute at @s run spawnpoint @s ~ ~ ~
tellraw @s {"text":"Left the lobby. Use /function brainmeth:lobby/enter to return while waiting.","color":"green"}
