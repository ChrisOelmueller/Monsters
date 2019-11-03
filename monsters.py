# See bottom of file for a list of possible arguments.
# As an example,
#   monsters.py re
# calls print_resists.

import os
import os.path
import sys
import re

from operator import attrgetter


mon_data_path = os.path.join(os.path.expanduser('~'),
                             "crawl/crawl-ref/source/mon-data.h")
old_data_path = os.path.join(os.path.expanduser('~'),
                             "crawl/crawl-ref/source/old-mon-data.h")
# Constants
MAG_IMMUNE = 270
BINARY_RESISTS = set(('curare', 'drown', 'hellfire', 'sticky'))

def read_mon_data(h=mon_data_path, debug=False):
    """Read mon-data.h"""
    data = str(open(h).read())

# Join preprocessor lines so they are stripped together later
    data = re.sub(r"\\"+r"\n", "", data)
# Strip out axed monsters
    data = re.sub("(?ms)static monsterentry mondata.*"
                  "#define AXED_MON[^}]*}[^}]*}[^}]*},",
                  "(", data)
#
    data = re.sub("AXED_MON(.*)", "", data)
    data = re.sub(r"(?ms)DUMMY\(.*?\)", "", data)

# Strip out block comments
    data = re.sub("(?ms)\/\*.*?\*\/", "", data)

# Strip other comments
    data = re.sub('//.*', '', data)
    data = re.sub('#.*', '', data)

# mrd(MR_X | MR_Y, 2) => MR_X2 | MR_Y2
    def mrd_convert(x):
        level = x.group(2)
        if int(level) == 1:
            level = ''
        resists = x.group(1).split('|')
        return ' | '.join("%s%s" % (res.strip(), level) for res in resists)
    data = re.sub('(?ms)mrd\((MR_[A-Z_\s|]+)+, (\d)\)', mrd_convert, data)

# Replace energy:
    def energy(x):
        return "(%s, %s)" % (x.group(1), x.group(2))
    data = re.sub('([A-Z0-9_-]*_ENERGY)\((.*?)\)', energy, data)

# Replace pipes by commas
    def pipes(x):
        return "(%s)" % re.sub('(?ms)\s*\|\s*', ',', x.group(0))
    data = re.sub('(?m)(\(.*\)|<<.*>>|[A-Z0-9_-]*)'
                  '(\s*\|\s*(\(.*\)|<<.*>>|[A-Z0-9_-]*))+', pipes, data)

# Stringify bare enums:
    def stringify(x):
        return "'%s'" % x.group(1)
    data = re.sub("(?<!['\"])([A-Z0-9_-]{2,})", stringify, data)

# Replace placeholders
    data = re.sub('(<<|{{)', '(', data)
    data = re.sub('(>>|}})', ')', data)

# Replace }s by )s unless they're a monster glyph.
    data = re.sub("}(?!['\"]);*", ')', data)
    data = re.sub("{", '(', data)

    if debug:
    # Write debug data right before trying to parse
        output_path = os.path.join(os.getcwd(), "data.py")
        with open(output_path, "w") as f:
            f.write(data)

    # Eval it, storing it as a tuple
    return eval(data)

mondata = read_mon_data()
olddata = mondata
#olddata = read_mon_data(old_data_path)


class Resistance(object):
    '''Store the four main resistances to always display.

    Additional resists are then added where necessary.
    Convert vulnerability to negative resistance.
    '''
    def __init__(self, resists):
        '''[maxlevel, level]'''
        self.fire = 0
        self.cold = 0
        self.pois = 0
        self.elec = 0

        for r in resists:
            level = -1 if r.startswith('MR_VUL_') else 1
            r = r[7:].lower()
            if r[-1] in '01234':
                level = level * min(3, int(r[-1]))
                r = r[:-1]
            # Some names that are easier to understand or abbreviate
            r = {
                'poison':       'pois',
                'rotting':      'rot',
                'asphyx':       'curare',
                'water':        'drown',
                'sticky_flame': 'sticky',
                }.get(r, r)
            setattr(self, r, level)

        if getattr(self, 'hellfire', None):
            self.fire = 3

    def __repr__(self):
        s = ''
        for resist in [
                'fire', 'cold', 'pois', 'elec',
                'neg', 'holy', 'rot', 'acid', 'steam',
                'curare', 'drown ', 'sticky', 'hellfire']:
            resist = resist.strip()
            level = getattr(self, resist, None)
            maxlevel = 1 if resist in BINARY_RESISTS else 3

            if level is None:
                # Optional and not present
                continue
            dot = 'x' if level < 0 else '+'
            level = abs(level)
            # Should only affect `hellfire`
            resist = resist[:6]
            s += "%-4s %s%s%s  " % (
                resist,
                dot * level,
                '.' * (maxlevel - level),
                ' ' * (3 - maxlevel - max(0, len(resist) - 4)))
        return s.strip()


class Energy(object):
    '''How quickly the energy granted by speed is used up.

    Most monsters should just use DEFAULT_ENERGY, where all the different
    types of actions use 10 energy units.

    #define MOVE_ENERGY(x)     { x,  x, 10, 10, 10, 10, 10, 100}
    #define ACTION_ENERGY(x)   {10, 10,  x,  x,  x,  x,  x, x * 10}
    #define ATTACK_ENERGY(x)   {10, 10,  x, 10, 10, 10, 10, 100}
    #define MISSILE_ENERGY(x)  {10, 10, 10,  x, 10, 10, 10, 100}
    #define SPELL_ENERGY(x)    {10, 10, 10, 10,  x, 10, 10, 100}
    #define SWIM_ENERGY(x)     {10,  x, 10, 10, 10, 10, 10, 100}
    '''
    def __init__(self,
        move = 10,
        swim = 10,
        attack = 10,
        missile = 10,
        spell = 10,
        mysteryA = 10,
        mysteryB = 10,
        mysteryC = 10 * 10
        ):

        self.move     = move
        self.swim     = swim
        self.attack   = attack
        self.missile  = missile
        self.spell    = spell
        self.mysteryA = mysteryA
        self.mysteryB = mysteryB
        self.mysteryC = mysteryC

    def move_speed(self, speed):
        self.move = speed
        self.swim = speed

    def move_energy(self, move):
        self.move = 100./move
        self.swim = 100./move

    def action_energy(self, action):
        self.attack   = action
        self.missile  = action
        self.spell    = action
        self.mysteryA = action
        self.mysteryB = action
        self.mysteryC = action * 10

    def attack_energy(self, attack):
        self.attack = attack

    def missile_energy(self, missile):
        self.missile = missile

    def spell_energy(self, spell):
        self.spell = spell

    def swim_energy(self, swim):
        self.swim = swim

    def __repr__(self):
        return ''.join('%-3d' % getattr(self, e)
            for e in [
                'move',
                'swim',
                'attack',
                'missile',
                'spell',
                'mysteryA',
                'mysteryB',
                'mysteryC',
            ])


class HP(object):
    def __init__(self, hp_dice):
        '''
        example: the Iron Golem, hpdice={15,7,4,0}
            15*7 < hp < 15*(7+4),
            105 < hp < 165
        hp will be around 135 each time.
        '''
        self.hp_dice = hp_dice
        (self.hd, self.min_hp, self.rand_hp, self.add_hp) = hp_dice
        self.min = self.add_hp + self.hd * self.min_hp
        self.max = self.add_hp + self.hd * (self.min_hp + self.rand_hp)
        self.avg = self.add_hp + self.hd * (self.min_hp + int(self.rand_hp / 2.))

    @property
    def fixed(self):
        return self.min == self.max

    def __repr__(self):
        return "(%3s..[%3s]..%3s)   %2dd%-2d[%+d]%+4d" % (
                self.min, self.avg, self.max,
                self.hd, self.min_hp, self.rand_hp, self.add_hp)


class Monster(object):
    def __init__(self,
        id,
        glyph,
        color,
        name,
        flags,
        resistances,
        mass,
        xp_modifier,
        genus,
        species,
        holiness,
        mr_modifier,
        attacks,
        hp_dice,
        ac,
        ev,
        spellbook,
        corpse_type,
        shout_type,
        intelligence,
        habitat,
        flight_class,
        speed,
        energy,
        item_use,
        eats,
        size,
        shape=None,
        *args, **kwargs):

        self.id          = id
        self.glyph       = glyph
        self.color       = color
        self.name        = name

        if isinstance(flags, tuple):
            self.flags   = ', '.join(f for f in sorted(flags))
        else:
            self.flags   = flags

        if resistances == 'MR_NO_FLAGS':
            self.resistances = tuple()
        elif isinstance(resistances, tuple):
            self.resistances = resistances
        else:
            self.resistances = (resistances, )

        self.resists = Resistance(self.resistances)

        self.mass        = int(mass)
        self.xp_modifier = int(xp_modifier)
        self.genus       = genus
        self.species     = species

        self.holiness    = holiness
        #
        # monster::res_holy_energy via monster::undead_or_demonic
        if ((self.holiness in ('MH_UNDEAD', 'MH_DEMONIC')
               and self.id != 'MONS_PROFANE_SERVITOR')
            or self.genus == 'MONS_DEMONSPAWN'):
            setattr(self.resists, 'holy', -2)
        # monster::res_holy_energy
        elif self.holiness == 'MH_HOLY' or self.id == 'MONS_PROFANE_SERVITOR':
            setattr(self.resists, 'holy', 1)
        # monster::res_negative_energy
        if self.holiness != 'MH_NATURAL':
            setattr(self.resists, 'neg', 3)
        # Missing but feasible:
        # monster::res_torment
        # rPois for e.g. abominations and other undead
        # monster::res_rotting
        # one/three level distinction?

        if mr_modifier == 'MAG_IMMUNE':
            self.mr_modifier = MAG_IMMUNE
        else:
            self.mr_modifier = int(mr_modifier)

        self.attacks     = []
        for attack in attacks:
            if attack == 'AT_NO_ATK':
                continue
            at_type, at_flavor, damage = attack
            # [3:] gets rid of AT_ and AF_ prefixes
            at_flavor = at_flavor[3:].lower()
            if at_flavor == 'plain':
                at_flavor = ''
            self.attacks.append((int(damage), at_type[3:], at_flavor))

        self.hp_dice      = list(map(int, hp_dice))
        self.hp           = HP(self.hp_dice)
        self.ac           = int(ac)
        self.ev           = int(ev)
        self.spellbook    = spellbook
        self.corpse_type  = corpse_type
        self.shout_type   = shout_type
        self.intelligence = intelligence
        self.habitat      = habitat
        self.flight_class = flight_class
        self.speed        = int(speed)

        self.energy       = Energy()
        if energy == 'DEFAULT_ENERGY':
            self.energy.move_speed(self.speed)
        elif len(energy) == 2:
            # E.g. ('SWIM_ENERGY', 6) or ('SPELL_ENERGY', '20')
            # => call  swim_energy(6)  or  spell_energy(20)
            getattr(self.energy, energy[0].lower())(int(energy[1]))
        else:
            # E.g. ('10', 6, 8, 8, 8, 8, 8, '80')
            e_int = (int(e) for e in energy)
            self.energy = Energy(*e_int)

        self.item_use     = item_use
        self.eats         = eats
        self.size         = size
        self.shape        = shape

    @property
    def hd(self):
        return int(self.hp_dice[0])

    @property
    def mr(self):
        '''monster.cc: monster::res_magic

        int u = (get_monster_data(base_type))->resist_magic;
        // Negative values get multiplied with monster hit dice.
        if (u < 0)
            u = hit_dice * -u * 4 / 3;

        Note that we indicate magic immunity by python-side MAG_IMMUNE = 270.
        '''
        if self.mr_modifier < 0:
            return int(self.hd * -self.mr_modifier * 4. / 3)
        else:
            return self.mr_modifier

    @property
    def mr_immune(self):
        return self.mr == MAG_IMMUNE

    def __repr__(self):
        return self.name


def title(heading, x='-'):
    print(('\n' + heading + '\n' + x * len(heading)))


def main():
    all_monsters = {}
    old_monsters = {}
    for m in mondata:
        mons = Monster(*m)
        all_monsters[mons.id] = mons
    for m in olddata:
        mons = Monster(*m)
        old_monsters[mons.id] = mons
    monsters = sorted(all_monsters.values(), key=attrgetter('id'))

    def print_attacks():
        title('Monster attacks')
        for m in sorted(monsters, key=attrgetter('id')):
            s = ''
            for (dam, at, af) in m.attacks:
                s += '%d' % dam
                if af:
                    if af == 'crush' and at == 'CONSTRICT':
                        af = 'hold' if dam == 0 else 'constrict'
                    s += '(%s)' % af.replace('_', ' ')
                s += ','
            print((" %-22.22s  %s" % (m, s.strip(','))))

    def print_hp():
        title('Monsters by Average HP, [*]: fixed')
        for m in sorted(monsters, key=attrgetter('hp.avg'), reverse=True):
            if m.hp.fixed:
                dot = '[*]'
                mhp = ''
            else:
                dot = '   '
                mhp = m.hp
            print(("%s%4d  %-22.22s  %s" % (dot, m.hp.avg, m, mhp)))

    def print_dragons():
        title('Dragons by HD')
        for m in sorted(monsters, key=attrgetter('hd'), reverse=True):
            if 'DRAGON' not in m.genus or 'M_CANT_SPAWN' in m.flags:
                continue
            print(("%2d  %s" % (m.hd, m)))
        title('Draconians by HD')
        for m in sorted(monsters, key=attrgetter('hd'), reverse=True):
            if 'DRACONIAN' not in m.genus or 'M_CANT_SPAWN' in m.flags:
                continue
            print(("%2d  %s" % (m.hd, m)))

    def print_hd():
        title('Dragons and not-dragons by HD')
        for m in sorted(monsters, key=attrgetter('hd'), reverse=True):
            if 'M_CANT_SPAWN' in m.flags:
                continue
            print(("%2d  %s" % (m.hd, m)))

    def print_ac():
        title('Monsters by AC')
        for m in sorted(monsters, key=attrgetter('ac'), reverse=True):
            print(("%4d  %s" % (m.ac, m)))

    def print_defenses():
        title('Monsters by AC and EV')
        for m in sorted(monsters, key=lambda m: m.ac + m.ev, reverse=True):
            print(("%3d|%3d  %s" % (m.ac, m.ev, m)))

    def print_resists():
        title('Monster resistances (not nearly complete!)')
        for m in sorted(monsters, key=attrgetter('id')):
            print((" %-22.22s %s" % (m, m.resists)))

    def print_mr(diff=False):
        title('Monsters by MR, [*]: immune')
        for m in sorted(monsters, key = attrgetter('mr'), reverse=True):
            if diff:
                try:
                    old_mr = old_monsters[m.id].mr
                except KeyError:
                    continue  # Monster removed since
            if m.mr_immune:
                mr = '[*]'
            else:
                mr = '%3d' % m.mr
            if diff:
                if old_mr == MAG_IMMUNE:
                    old_mr = '[*]'
                else:
                    old_mr = '%3d' % old_mr
                print(("  %s  %s  %s" % (mr, old_mr, m)))
            else:
                print(("  %s  %s" % (mr, m)))

    def print_speed():
        title('Monsters by move speed (player: usually 10)')
        for m in sorted(monsters, key = lambda m: m.energy.move, reverse=True):
            print(("% 5.4s  %s" % (m.energy.move, m)))

    def print_everything():
        print_mr()
        print_hp()
        print_attacks()
        print_resists()
        print_ac()
        # defenses
        # dragons
        print_speed()

    fnmap = {
        'ac': print_ac,
        'defenses': print_defenses,
        'attacks': print_attacks,
        'dragons': print_dragons,
        'everything': print_everything,
        'hd': print_hd,
        'hp': print_hp,
        'mr': print_mr,
        'resists': print_resists,
        'speed': print_speed,
    }

    for (abbr, fn) in fnmap.items():
        if abbr.startswith(sys.argv[1]):
            fn()


if __name__ == '__main__':
    main()
