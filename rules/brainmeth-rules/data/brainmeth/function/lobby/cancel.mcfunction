# Cancel any scheduled countdown without releasing players.
scoreboard players set #countdown bm_launch 0
tellraw @a {"text":"Launch countdown cancelled.","color":"yellow"}
