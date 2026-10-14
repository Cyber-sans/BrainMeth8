# Small sealed staging room at overworld (0,200,0); completely reversible.
execute in minecraft:overworld run fill -10 199 -10 10 199 10 minecraft:bedrock
execute in minecraft:overworld run fill -10 200 -10 10 207 10 minecraft:barrier hollow
execute in minecraft:overworld run fill -9 200 -9 9 206 9 minecraft:air
execute in minecraft:overworld run fill -9 200 -9 9 200 9 minecraft:polished_deepslate
execute in minecraft:overworld run fill -10 207 -10 10 207 10 minecraft:barrier
execute in minecraft:overworld run setblock 0 201 0 minecraft:sea_lantern
scoreboard players set #built bm_launch 1
