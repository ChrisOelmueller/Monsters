Monsters Manual
---------------

Discover things about Crawl monsters as a whole!
For individual monsters, best refer to the bots in ##crawl on Freenode.
You can use `%?? yak` in there and be greeted with all the data, like so:
```
yak (Y) | Spd: 10 | HD: 7 | HP: 26-52 | AC/EV: 4/7 | Dam: 18
        | Res: magic(28) | XP: 205 | Sz: Large | Int: animal.
```

Example question to ask Monsters: "Which monsters have more than 20 AC?"

`python2 ./monsters.py ac`

results in a huge list starting like this:

```
Monsters by AC
--------------
127  test spawner
 40  Dispater
 30  Asmodeus
 30  Cerebov
 30  Murray
 30  Tiamat
 28  Antaeus
 25  animated tree
 25  curse skull
 25  curse toe
 25  Hell Sentinel
 22  crystal guardian
 22  war gargoyle
 ...
```

Possible queries
----------------
As of now, the following arguments to `monsters.py` are supported:

 - [`ac`](ac)
 - [`defenses` (AC + EV)](defenses)
 - [`attacks`](attacks)
 - [`dragons` (dragons + draconians by HD)](dragons)
 - [`hp`](hp)
 - [`mr`](mr)
 - [`resists`](resists)
 - [`speed` (movement speed)](speed)

Additionally, `everything` prints most of the above if you simply want to
discover new things or forgot what to look for. To find out what is skipped,
refer to [monsters.py:print_everything](monsters.py#L458).
