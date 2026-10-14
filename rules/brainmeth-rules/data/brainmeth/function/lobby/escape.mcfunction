# OP-only manual testing bypass: release just the command executor.
# The staff tag prevents locked.mcfunction from dragging this player back.
tag @s add bm_staff
tag @s remove bm_lobby
gamemode survival @s
execute in minecraft:overworld run spreadplayers 0 0 4 35 false @s
tellraw @s {"text":"You have left the waiting room. Other players remain locked until launch.","color":"green"}
