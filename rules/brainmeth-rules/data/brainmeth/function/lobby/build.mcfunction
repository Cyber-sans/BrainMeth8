# Brainmeth launch lounge v3: full 49x49 glass atrium, PvP floor, two-stage playable parkour.
# All commands use overworld absolute coordinates; all 16 chunks are forceloaded by lobby/init.
# Clear and replace the whole previous v2 layout. Slice under the 32,768 /fill limit.
execute in minecraft:overworld run kill @e[type=minecraft:text_display,tag=bm_lobby_decor]
execute in minecraft:overworld run fill -24 199 -24 24 205 24 minecraft:air
execute in minecraft:overworld run fill -24 206 -24 24 212 24 minecraft:air
execute in minecraft:overworld run fill -24 213 -24 24 219 24 minecraft:air
execute in minecraft:overworld run fill -24 220 -24 24 226 24 minecraft:air
execute in minecraft:overworld run fill -24 199 -24 24 199 24 minecraft:barrier
execute in minecraft:overworld run fill -23 200 -23 23 200 23 minecraft:light_blue_stained_glass
execute in minecraft:overworld run fill -24 200 -24 24 200 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 200 24 24 200 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 200 -24 -24 200 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 200 -24 24 200 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 201 -24 -24 225 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill 24 201 -24 24 225 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -23 201 -24 23 225 -24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -23 201 24 23 225 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -24 226 -24 24 226 24 minecraft:light_blue_stained_glass
execute in minecraft:overworld run fill -24 212 -24 24 212 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 225 -24 24 225 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 212 24 24 212 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 225 24 24 225 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 212 -24 -24 212 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 225 -24 -24 225 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 212 -24 24 212 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 225 -24 24 225 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 201 -24 -24 225 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 201 0 -24 225 0 minecraft:oxidized_copper
execute in minecraft:overworld run fill -24 201 24 -24 225 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 0 201 -24 0 225 -24 minecraft:oxidized_copper
execute in minecraft:overworld run fill 0 201 24 0 225 24 minecraft:oxidized_copper
execute in minecraft:overworld run fill 24 201 -24 24 225 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 201 0 24 225 0 minecraft:oxidized_copper
execute in minecraft:overworld run fill 24 201 24 24 225 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -7 200 -7 7 200 7 minecraft:polished_deepslate
execute in minecraft:overworld run fill -6 200 -6 6 200 6 minecraft:quartz_block outline
execute in minecraft:overworld run fill -5 200 -5 5 200 5 minecraft:polished_deepslate
execute in minecraft:overworld run fill -2 200 -2 2 200 2 minecraft:polished_blackstone_bricks outline
execute in minecraft:overworld run setblock 0 200 0 minecraft:sea_lantern
execute in minecraft:overworld run fill -21 200 -20 21 200 -20 minecraft:polished_deepslate
execute in minecraft:overworld run fill -20 200 -21 -20 200 21 minecraft:polished_deepslate
execute in minecraft:overworld run fill -21 200 20 21 200 20 minecraft:polished_deepslate
execute in minecraft:overworld run fill 20 200 -21 20 200 21 minecraft:polished_deepslate
execute in minecraft:overworld run setblock -20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -12 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 -12 minecraft:sea_lantern
execute in minecraft:overworld run setblock -12 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 -12 minecraft:sea_lantern
execute in minecraft:overworld run setblock -4 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 -4 minecraft:sea_lantern
execute in minecraft:overworld run setblock -4 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 -4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 4 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 4 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 12 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 12 minecraft:sea_lantern
execute in minecraft:overworld run setblock 12 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 12 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 226 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 226 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 226 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 226 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -18 200 18 minecraft:moss_block
execute in minecraft:overworld run setblock -18 201 18 minecraft:flowering_azalea
execute in minecraft:overworld run setblock -18 226 18 minecraft:sea_lantern
execute in minecraft:overworld run setblock 18 200 18 minecraft:moss_block
execute in minecraft:overworld run setblock 18 201 18 minecraft:flowering_azalea
execute in minecraft:overworld run setblock 18 226 18 minecraft:sea_lantern
execute in minecraft:overworld run setblock 18 200 -18 minecraft:moss_block
execute in minecraft:overworld run setblock 18 201 -18 minecraft:flowering_azalea
execute in minecraft:overworld run setblock 18 226 -18 minecraft:sea_lantern
# A continuous, physically reachable course; 1-block maximum ascent between jumps.
execute in minecraft:overworld run fill -19 201 -19 -17 201 -17 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -18 200 -18 minecraft:sea_lantern
execute in minecraft:overworld run fill -15 202 -18 -14 202 -17 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -15 201 -18 minecraft:sea_lantern
execute in minecraft:overworld run fill -12 203 -18 -11 203 -17 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -12 202 -18 minecraft:sea_lantern
execute in minecraft:overworld run fill -9 204 -17 -8 204 -16 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -9 203 -17 minecraft:sea_lantern
execute in minecraft:overworld run fill -7 205 -14 -6 205 -13 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -7 204 -14 minecraft:sea_lantern
execute in minecraft:overworld run fill -6 206 -11 -5 206 -10 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -6 205 -11 minecraft:sea_lantern
execute in minecraft:overworld run fill -8 207 -8 -7 207 -7 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -8 206 -8 minecraft:sea_lantern
execute in minecraft:overworld run fill -11 208 -7 -10 208 -6 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -11 207 -7 minecraft:sea_lantern
execute in minecraft:overworld run fill -14 209 -6 -13 209 -5 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -14 208 -6 minecraft:sea_lantern
execute in minecraft:overworld run fill -16 210 -3 -15 210 -2 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -16 209 -3 minecraft:sea_lantern
execute in minecraft:overworld run fill -14 211 0 -13 211 1 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -14 210 0 minecraft:sea_lantern
execute in minecraft:overworld run fill -11 212 2 -10 212 3 minecraft:cyan_concrete
execute in minecraft:overworld run setblock -11 211 2 minecraft:sea_lantern
execute in minecraft:overworld run fill -9 213 3 -7 213 5 minecraft:gold_block
execute in minecraft:overworld run setblock -8 212 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock -5 213 4 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -5 212 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock -3 214 6 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -3 213 6 minecraft:sea_lantern
execute in minecraft:overworld run setblock -1 214 8 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -1 213 8 minecraft:sea_lantern
execute in minecraft:overworld run setblock 1 215 10 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 1 214 10 minecraft:sea_lantern
execute in minecraft:overworld run setblock 3 215 12 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 3 214 12 minecraft:sea_lantern
execute in minecraft:overworld run setblock 6 216 12 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 6 215 12 minecraft:sea_lantern
execute in minecraft:overworld run setblock 9 216 11 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 9 215 11 minecraft:sea_lantern
execute in minecraft:overworld run setblock 12 217 9 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 12 216 9 minecraft:sea_lantern
execute in minecraft:overworld run setblock 15 217 7 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 15 216 7 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 218 4 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 17 217 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 218 1 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 17 217 1 minecraft:sea_lantern
execute in minecraft:overworld run setblock 15 219 -2 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 15 218 -2 minecraft:sea_lantern
execute in minecraft:overworld run setblock 12 219 -4 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 12 218 -4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 9 220 -6 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 9 219 -6 minecraft:sea_lantern
execute in minecraft:overworld run setblock 6 220 -9 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 6 219 -9 minecraft:sea_lantern
execute in minecraft:overworld run setblock 3 221 -12 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 3 220 -12 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 221 -15 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 0 220 -15 minecraft:sea_lantern
execute in minecraft:overworld run setblock -3 222 -18 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -3 221 -18 minecraft:sea_lantern
execute in minecraft:overworld run fill -8 222 -20 -6 222 -18 minecraft:gold_block
execute in minecraft:overworld run setblock -7 221 -19 minecraft:sea_lantern
# Floating wayfinding uses display entities only; parkour blocks never form an impassable ceiling.
execute in minecraft:overworld run summon minecraft:text_display 0 205 0 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"BRAINMETH  |  GLASS ARENA","color":"aqua","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display 0 203 -7 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"PVP ENABLED  •  FISTS + PARKOUR","color":"yellow","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display -18 205 -19 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"START  →  CYAN COURSE","color":"green","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display -8 216 4 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"CHECKPOINT  →  MAGENTA COURSE","color":"light_purple","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display -7 225 -19 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"FINISH  •  COMPLETE A LAP","color":"gold","bold":true}'}
# Mark ready ONLY if structural witnesses exist. Tick will reconstruct if any disappear.
execute in minecraft:overworld if block 0 200 0 minecraft:sea_lantern if block -24 205 0 minecraft:cyan_stained_glass if block 0 226 0 minecraft:light_blue_stained_glass if block -18 201 -18 minecraft:cyan_concrete if block -7 222 -19 minecraft:sea_lantern run scoreboard players set #layout bm_launch 3
