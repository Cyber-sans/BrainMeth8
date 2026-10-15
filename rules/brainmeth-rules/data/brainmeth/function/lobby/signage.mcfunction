# Update the live lobby's floating signs without rebuilding or disrupting the parkour.
# Removes all previous floating lobby labels. Only the single title is restored.
execute in minecraft:overworld run kill @e[type=minecraft:text_display,tag=bm_lobby_decor]
execute in minecraft:overworld run summon minecraft:text_display 0 205 0 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"Brainmeth Lobby","color":"aqua","bold":true}'}
scoreboard players set #signage bm_launch 1
