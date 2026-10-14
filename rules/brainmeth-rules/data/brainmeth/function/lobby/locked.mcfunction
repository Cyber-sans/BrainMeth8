tag @a[tag=bm_staff,tag=bm_lobby] remove bm_lobby
execute as @a[tag=!bm_staff,tag=!bm_lobby_seen] run title @s title {"text":"BRAINMETH LAUNCH LOUNGE","color":"aqua","bold":true}
execute as @a[tag=!bm_staff,tag=!bm_lobby_seen] run title @s subtitle {"text":"Parkour begins at the green pad","color":"yellow"}
tag @a[tag=!bm_staff,tag=!bm_lobby_seen] add bm_lobby_seen
tag @a[tag=!bm_staff] add bm_lobby
gamemode adventure @a[tag=bm_lobby,gamemode=!adventure]
execute as @a[tag=bm_lobby] at @s unless dimension minecraft:overworld in minecraft:overworld run tp @s 0 202 0
execute as @a[tag=bm_lobby] at @s if dimension minecraft:overworld unless entity @s[x=-23,y=201,z=-23,dx=46,dy=22,dz=46] run tp @s 0 202 0
effect give @a[tag=bm_lobby] minecraft:resistance 2 4 true
effect give @a[tag=bm_lobby] minecraft:saturation 2 0 true
