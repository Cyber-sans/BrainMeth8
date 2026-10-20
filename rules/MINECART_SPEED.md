# Brainmeth minecart speed (NeoForge 1.21.1)

Brainmeth Core retains a 4x vanilla maximum rail speed (1.6 blocks/tick,
32 blocks/second) on dry vanilla rails. Water and modded rails are unchanged.

At speeds above vanilla's 0.4 blocks/tick, movement is subdivided into up
to eight short moves per tick (target 0.30 blocks per substep). Each step uses
vanilla's `getPosOffs` track projection to choose the forward point on the
rail underneath the cart, including rail shape changes at corners and slopes.
Each short move uses ordinary collision handling.

Only movement is subdivided: the enclosing `moveAlongTrack` executes once,
so acceleration, friction, rail callbacks, and powered-rail effects remain
once per game tick. After it finishes, horizontal momentum is aligned to the
last travelled track segment while retaining the computed speed.

No extra entity ticks, entity searches, or global scanning. Slow carts use
the unchanged vanilla movement path. The older Minecart Speed mod remains
disabled.

## Required before production

The substep implementation needs a rebuilt Brainmeth Core JAR and live
testing on the isolated test server. Static verification and successful
compilation alone **do not** prove corner or slope handling.

Test high-speed straight-to-curve and repeated curves in both directions,
ascending and descending rails, powered/detector/activator rails, passengers,
collisions, track ends, chunk boundaries and concurrent carts. Confirm
32 blocks/s on a sufficiently long powered straight and check TPS/MSPT.
If carts still derail, do not deploy to production.

```bash
cd /srv/minecraft/brainmeth/server-1211
git pull --ff-only origin migration/neoforge-1.21.1
bash ./scripts/deploy.sh test
```
