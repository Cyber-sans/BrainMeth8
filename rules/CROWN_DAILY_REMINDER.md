# Crown of Brainmeth: daily reminder

Brainmeth Core broadcasts one randomly chosen reminder per **real-world calendar
day in Europe/London**, at a randomly selected second throughout that day.
The selected time and whether it fired are saved in the world at
`brainmeth-crown-daily-taunt.json`, so restarts cannot trigger duplicates.

When starting mid-day, the first message is randomly scheduled in the time
remaining that day. On subsequent days, the time can fall anywhere between
local midnight and the next midnight (including DST changes).

The format is `<current holder> still holds the Crown of Brainmeth. <taunt>`.
The taunt is selected with equal probability among **14** entries:

1. The rest of you, bend the knee.
2. You are below them.
3. They stand above all.
4. Everybody else smells of poo.
5. Lower your heads.
6. Try and take it back.
7. ...for now
8. `<random online non-holder> is not.` (rerolled if nobody qualifies)
9. Stillwater, Iranian Giggle.
10. `More like <holder>-meth.`
11. Learn his name.
12. Say his name.
13. Remember his name.
14. Inferior lower citizens.

Only players online at the chosen second receive the broadcast.
There is **no replay**, catch-up, or notification history for daily taunts.
If nobody is online, or nobody owns the crown, that day's reminder is skipped.
If the server was offline at the scheduled instant, the missed taunt is skipped
on restart rather than being delivered late.
The daily reminder does not modify crown acquisition/theft announcements,
which continue to be stored for offline catch-up.
