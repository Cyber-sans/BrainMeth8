# Non-staff cannot leave or build before official launch, even by teleport/glitch.
execute if score #state bm_launch matches 0 run function brainmeth:lobby/locked
# Completing the course counts one lap, gives a celebratory effect and resets to its start.
execute if score #state bm_launch matches 0 as @a[tag=bm_lobby,x=1,y=221,z=-21,dx=2,dy=2,dz=2] run function brainmeth:lobby/parkour_finish
# Players offline at release are also safely moved out of the dismantled lobby on login.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] at @s if dimension minecraft:overworld if entity @s[x=-24,y=198,z=-24,dx=48,dy=27] in minecraft:overworld run spreadplayers 0 0 4 35 false @s
# Players offline at release have adventure mode restored on their next login.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] run gamemode survival @s
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby
