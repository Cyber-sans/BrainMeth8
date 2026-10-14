tag @a[tag=bm_staff,tag=bm_lobby] remove bm_lobby
tag @a[tag=!bm_staff] add bm_lobby
gamemode adventure @a[tag=bm_lobby,gamemode=!adventure]
execute as @a[tag=bm_lobby] at @s unless dimension minecraft:overworld in minecraft:overworld run tp @s 0 202 0
execute as @a[tag=bm_lobby] at @s if dimension minecraft:overworld unless entity @s[x=-9,y=201,z=-9,dx=18,dy=5,dz=18] run tp @s 0 202 0
effect give @a[tag=bm_lobby] minecraft:resistance 2 4 true
effect give @a[tag=bm_lobby] minecraft:saturation 2 0 true
