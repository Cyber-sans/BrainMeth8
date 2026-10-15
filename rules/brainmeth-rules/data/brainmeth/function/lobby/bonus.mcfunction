# Optional expert parkour finale: 21 narrow precision jumps above the glass floor.
# Starts from the old gold finish at (-7,222,-19) and ends at the emerald pad.
# Use only individual blocks, avoiding ceiling and central arena; safe to apply to an existing lobby.
execute in minecraft:overworld run setblock -4 223 -19 minecraft:orange_concrete
execute in minecraft:overworld run setblock -4 222 -19 minecraft:sea_lantern
execute in minecraft:overworld run setblock -1 223 -18 minecraft:orange_concrete
execute in minecraft:overworld run setblock -1 222 -18 minecraft:sea_lantern
execute in minecraft:overworld run setblock 2 223 -19 minecraft:orange_concrete
execute in minecraft:overworld run setblock 2 222 -19 minecraft:sea_lantern
execute in minecraft:overworld run setblock 5 222 -17 minecraft:red_concrete
execute in minecraft:overworld run setblock 5 221 -17 minecraft:sea_lantern
execute in minecraft:overworld run setblock 8 223 -18 minecraft:orange_concrete
execute in minecraft:overworld run setblock 8 222 -18 minecraft:sea_lantern
execute in minecraft:overworld run setblock 11 223 -17 minecraft:orange_concrete
execute in minecraft:overworld run setblock 11 222 -17 minecraft:sea_lantern
execute in minecraft:overworld run setblock 14 223 -19 minecraft:orange_concrete
execute in minecraft:overworld run setblock 14 222 -19 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 222 -17 minecraft:red_concrete
execute in minecraft:overworld run setblock 17 221 -17 minecraft:sea_lantern
execute in minecraft:overworld run setblock 18 223 -14 minecraft:orange_concrete
execute in minecraft:overworld run setblock 18 222 -14 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 223 -11 minecraft:orange_concrete
execute in minecraft:overworld run setblock 17 222 -11 minecraft:sea_lantern
execute in minecraft:overworld run setblock 19 223 -8 minecraft:orange_concrete
execute in minecraft:overworld run setblock 19 222 -8 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 222 -5 minecraft:red_concrete
execute in minecraft:overworld run setblock 17 221 -5 minecraft:sea_lantern
execute in minecraft:overworld run setblock 18 223 -2 minecraft:orange_concrete
execute in minecraft:overworld run setblock 18 222 -2 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 223 1 minecraft:orange_concrete
execute in minecraft:overworld run setblock 17 222 1 minecraft:sea_lantern
execute in minecraft:overworld run setblock 19 223 4 minecraft:orange_concrete
execute in minecraft:overworld run setblock 19 222 4 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 222 7 minecraft:red_concrete
execute in minecraft:overworld run setblock 17 221 7 minecraft:sea_lantern
execute in minecraft:overworld run setblock 18 223 10 minecraft:orange_concrete
execute in minecraft:overworld run setblock 18 222 10 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 223 13 minecraft:orange_concrete
execute in minecraft:overworld run setblock 17 222 13 minecraft:sea_lantern
execute in minecraft:overworld run setblock 19 223 16 minecraft:orange_concrete
execute in minecraft:overworld run setblock 19 222 16 minecraft:sea_lantern
execute in minecraft:overworld run setblock 17 223 19 minecraft:red_concrete
execute in minecraft:overworld run setblock 17 222 19 minecraft:sea_lantern
execute in minecraft:overworld run setblock 14 223 19 minecraft:orange_concrete
execute in minecraft:overworld run setblock 14 222 19 minecraft:sea_lantern
execute in minecraft:overworld run fill 11 223 18 12 223 19 minecraft:emerald_block
execute in minecraft:overworld run setblock 11 222 18 minecraft:sea_lantern
# Set the completion flag only after the emerald finish is present.
execute in minecraft:overworld if block 11 223 18 minecraft:emerald_block if block -4 223 -19 minecraft:orange_concrete run scoreboard players set #bonus bm_launch 1
