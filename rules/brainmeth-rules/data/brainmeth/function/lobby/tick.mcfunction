# Non-staff cannot leave or build before official launch, even by teleport/glitch.
execute if score #state bm_launch matches 0 run function brainmeth:lobby/locked
# Players offline at release are also safely moved out of the dismantled lobby on login.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] at @s if dimension minecraft:overworld if entity @s[x=-10,y=198,z=-10,dx=20,dy=12,dz=20] in minecraft:overworld run spreadplayers 0 0 4 35 false @s
# Players offline at release have adventure mode restored on their next login.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] run gamemode survival @s
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby
