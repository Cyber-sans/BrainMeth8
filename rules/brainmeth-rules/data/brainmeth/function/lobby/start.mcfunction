# Run as OP: /function brainmeth:lobby/start (10-second countdown).
execute if score #state bm_launch matches 0 unless score #countdown bm_launch matches 1 run function brainmeth:lobby/countdown_begin
