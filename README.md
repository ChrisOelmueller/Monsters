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

`python ./monsters.py ac`

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
 - [`hd`](hd)
 - [`hp`](hp)
 - [`mr`](mr)
 - [`resists`](resists)
 - [`speed` (movement speed)](speed)

Additionally, `everything` prints all of the above if you simply want to
discover new things or forgot what to look for.

To regenerate the list of local output for every function defined above,
simply run `monsters.py` without any command-line arguments. It will
produce one output file named `ac`, one named `defenses` and so on.

Still to be done: guess file location of mon-data.h and allow passing its
path as command-line argument. But for that, a proper parser has to happen!
