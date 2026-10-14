# Brainmeth launch atrium v2. Sky-high, 49 x 49 glass parkour lounge.
# Clear both the previous compact room and this layout's exact footprint.
# Minecraft /fill has a 32768 block cap: each half is <= 31213.
execute in minecraft:overworld run kill @e[type=minecraft:text_display,tag=bm_lobby_decor]
execute in minecraft:overworld run fill -24 199 -24 24 211 24 minecraft:air
execute in minecraft:overworld run fill -24 212 -24 24 224 24 minecraft:air
# Invisible safety underfloor; stained-glass observation deck above it.
execute in minecraft:overworld run fill -24 199 -24 24 199 24 minecraft:barrier
execute in minecraft:overworld run fill -23 200 -23 23 200 23 minecraft:light_blue_stained_glass
execute in minecraft:overworld run fill -24 200 -24 24 200 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 200 24 24 200 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 200 -24 -24 200 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 200 -24 24 200 24 minecraft:polished_blackstone_bricks
# Tall teal glass walls, dark frame and starlight ceiling.
execute in minecraft:overworld run fill -24 201 -24 -24 223 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill 24 201 -24 24 223 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -23 201 -24 23 223 -24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -23 201 24 23 223 24 minecraft:cyan_stained_glass
execute in minecraft:overworld run fill -24 224 -24 24 224 24 minecraft:light_blue_stained_glass
execute in minecraft:overworld run fill -24 223 -24 24 223 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 223 24 24 223 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 223 -23 -24 223 23 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 223 -23 24 223 23 minecraft:polished_blackstone_bricks
# Suspended skybridges built into the high glass canopy.
execute in minecraft:overworld run fill -24 212 -24 24 212 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 212 24 24 212 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 212 -23 -24 212 23 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 212 -23 24 212 23 minecraft:polished_blackstone_bricks
# Blackstone corner ribs every twelve blocks.
execute in minecraft:overworld run fill -24 201 -24 -24 223 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill -24 201 24 -24 223 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 201 -24 24 223 -24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run fill 24 201 24 24 223 24 minecraft:polished_blackstone_bricks
execute in minecraft:overworld run setblock -23 201 -23 minecraft:sea_lantern
execute in minecraft:overworld run setblock 23 201 -23 minecraft:sea_lantern
execute in minecraft:overworld run setblock -23 201 23 minecraft:sea_lantern
execute in minecraft:overworld run setblock 23 201 23 minecraft:sea_lantern
# Floor lighting pattern, central launch beacon and visitor lounge.
execute in minecraft:overworld run fill -4 200 -4 4 200 4 minecraft:polished_deepslate
execute in minecraft:overworld run fill -2 200 -2 2 200 2 minecraft:quartz_block
execute in minecraft:overworld run setblock 0 200 0 minecraft:sea_lantern
execute in minecraft:overworld run fill -21 200 -21 -15 200 -21 minecraft:polished_deepslate
execute in minecraft:overworld run fill -21 200 -20 -21 200 -15 minecraft:polished_deepslate
execute in minecraft:overworld run fill -21 200 -15 -15 200 -15 minecraft:polished_deepslate
execute in minecraft:overworld run fill -15 200 -21 -15 200 -15 minecraft:polished_deepslate
execute in minecraft:overworld run setblock -18 200 -18 minecraft:emerald_block
execute in minecraft:overworld run fill -4 200 19 4 200 21 minecraft:polished_deepslate
execute in minecraft:overworld run fill -4 200 -21 4 200 -19 minecraft:polished_deepslate
execute in minecraft:overworld run fill 19 200 -4 21 200 4 minecraft:polished_deepslate
execute in minecraft:overworld run fill -21 200 -4 -19 200 4 minecraft:polished_deepslate
# Four aquarium-like accent planters beside perimeter seating.
execute in minecraft:overworld run setblock -19 200 19 minecraft:moss_block
execute in minecraft:overworld run setblock -19 201 19 minecraft:flowering_azalea
execute in minecraft:overworld run setblock 19 200 19 minecraft:moss_block
execute in minecraft:overworld run setblock 19 201 19 minecraft:flowering_azalea
execute in minecraft:overworld run setblock -19 200 -19 minecraft:moss_block
execute in minecraft:overworld run setblock -19 201 -19 minecraft:flowering_azalea
execute in minecraft:overworld run setblock 19 200 -19 minecraft:moss_block
execute in minecraft:overworld run setblock 19 201 -19 minecraft:flowering_azalea
execute in minecraft:overworld run setblock -20 223 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 223 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 0 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 223 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 223 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 0 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 223 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 223 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 -20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 223 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock -20 200 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 223 20 minecraft:sea_lantern
execute in minecraft:overworld run setblock 20 200 20 minecraft:sea_lantern
# Beginner route: wide two-block platforms, rising gently above the glass floor.
execute in minecraft:overworld run fill -18 202 -15 -17 202 -14 minecraft:cyan_concrete
execute in minecraft:overworld run fill -14 203 -15 -13 203 -14 minecraft:cyan_concrete
execute in minecraft:overworld run fill -10 204 -15 -9 204 -14 minecraft:cyan_concrete
execute in minecraft:overworld run fill -7 204 -12 -6 204 -11 minecraft:cyan_concrete
execute in minecraft:overworld run fill -7 205 -8 -6 205 -7 minecraft:cyan_concrete
execute in minecraft:overworld run fill -10 206 -5 -9 206 -4 minecraft:cyan_concrete
execute in minecraft:overworld run fill -14 207 -5 -13 207 -4 minecraft:cyan_concrete
execute in minecraft:overworld run fill -18 208 -5 -17 208 -4 minecraft:cyan_concrete
execute in minecraft:overworld run fill -18 209 -1 -17 209 0 minecraft:cyan_concrete
execute in minecraft:overworld run fill -15 209 2 -14 209 3 minecraft:cyan_concrete
execute in minecraft:overworld run fill -12 210 2 -11 210 3 minecraft:cyan_concrete
execute in minecraft:overworld run fill -9 210 2 -8 210 3 minecraft:cyan_concrete
# Midway landing: a 3x3 reinforced pad and climbable scaffold lift from the floor.
execute in minecraft:overworld run fill -10 210 1 -8 210 3 minecraft:polished_deepslate
execute in minecraft:overworld run setblock -9 210 2 minecraft:gold_block
execute in minecraft:overworld run fill -11 201 2 -11 210 2 minecraft:scaffolding
execute in minecraft:overworld run setblock -11 200 2 minecraft:emerald_block
# Advanced route: precise single-block diagonal jumps with a gold finish.
execute in minecraft:overworld run setblock -6 210 5 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -4 211 7 minecraft:magenta_concrete
execute in minecraft:overworld run setblock -2 211 9 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 0 212 11 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 2 212 13 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 4 213 11 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 6 213 9 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 8 214 7 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 10 214 5 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 12 215 3 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 14 215 1 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 16 216 -1 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 18 216 -3 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 18 217 -6 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 16 217 -8 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 14 218 -10 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 12 218 -12 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 10 219 -14 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 8 219 -16 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 6 220 -18 minecraft:magenta_concrete
execute in minecraft:overworld run setblock 4 220 -20 minecraft:magenta_concrete
execute in minecraft:overworld run fill 1 220 -21 3 220 -19 minecraft:gold_block
execute in minecraft:overworld run setblock 2 220 -20 minecraft:sea_lantern
# Floating holographic signage; tagged so the launch cleanup removes it.
execute in minecraft:overworld run summon minecraft:text_display 0 205 0 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"BRAINMETH  •  LAUNCH LOUNGE","color":"aqua","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display -18 205 -18 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"PARKOUR START  →","color":"green","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display -10 214 2 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"HALFWAY • SCAFFOLD LIFT BELOW","color":"yellow","bold":true}'}
execute in minecraft:overworld run summon minecraft:text_display 2 223 -20 {Tags:["bm_lobby_decor"],billboard:"center",background:0,see_through:1b,text:'{"text":"FINISH • REPLAY FOR A BETTER SCORE","color":"gold","bold":true}'}
scoreboard players set #layout bm_launch 2
scoreboard players set #built bm_launch 1
