# Non-staff cannot leave or build before official launch, even by teleport/glitch.
execute if score #state bm_launch matches 0 run function brainmeth:lobby/locked
# Players offline at release have adventure mode restored on their next login.
execute if score #state bm_launch matches 1 as @a[tag=bm_lobby] run gamemode survival @s
execute if score #state bm_launch matches 1 run tag @a[tag=bm_lobby] remove bm_lobby
