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
# Settings
indent = 4
MAG_IMMUNE = 270

# Read mon-data.h
data = unicode(open(mon_data_path).read())

# Strip out axed monsters
data = re.sub("(?ms)static monsterentry mondata.*"
              "#define AXED_MON[^}]*}[^}]*}[^}]*},",
              "(", data)
# 
data = re.sub("AXED_MON(.*)", "", data)

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

# Write debug data right before trying to parse
output_path = os.path.join(os.getcwd(), "data.py")
with open(output_path, "w") as f:
    f.write(data)

# Eval it, storing it as a tuple
mondata = eval(data)

def resist_dots(resist):
    '''Formatting function for resistance lines.'''
    dot = 'x' if resist.startswith('MR_VUL_') else '+'
    resist = resist[7:].lower()
    level = 1
    maxlevel = 3
    if resist[-1] in '01234':
        level = min(maxlevel, int(resist[-1]))
        resist = resist[:-1]

    if resist in ('asphyx', 'hellfire', 'sticky_flame', 'water'):
        maxlevel = 1

    if level == 0:
        maxlevel = 0

    # Some names are easier to understand or abbreviate
    resist = {
        'asphyx':  'curare',
        'water':   'drown',
        'rotting': 'rot',
        }.get(resist, resist)

    resist = resist[:7-maxlevel]

    return "%-4s %s%s%s" % (
            resist,
            dot * level,
            "." * (maxlevel - level),
            ' ' * (3 - maxlevel - max(0, len(resist) - 4)))


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
        zombie_type,
        shout_type,
        intelligence,
        habitat,
        flight_class,
        speed,
        energy,
        item_use,
        eats,
        size):

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
        if 'MR_RES_HELLFIRE' in self.resistances:
            self.resistances = self.resistances + ('MR_RES_FIRE3', )

        self.mass        = int(mass)
        self.xp_modifier = int(xp_modifier)
        self.genus       = genus
        self.species     = species

        self.holiness    = holiness
        #
        # monster::res_holy_energy via monster::undead_or_demonic
        if self.holiness in ('MH_UNDEAD', 'MH_DEMONIC') or self.genus == 'MONS_DEMONSPAWN':
            self.resistances = self.resistances + ('MR_VUL_HOLY2', )
        # monster::res_holy_energy
        if self.holiness == 'MH_HOLY' or self.id == 'MONS_PROFANE_SERVITOR':
            self.resistances = self.resistances + ('MR_RES_HOLY', )
        # monster::res_negative_energy
        if self.holiness != 'MH_NATURAL':
            self.resistances = self.resistances + ('MR_RES_NEG3', )
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

        self.hp_dice      = hp_dice
        self.ac           = int(ac)
        self.ev           = int(ev)
        self.spellbook    = spellbook
        self.corpse_type  = corpse_type
        self.zombie_type  = zombie_type
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
    def resists(self):
        # Fill up the main resistances with empty lines for alignment
        for res in ('FIRE', 'COLD', 'ACID', 'POISON', 'ELEC', 'NEG', 'HOLY'):
            if not any(r.startswith('MR_RES_'+res) for r in self.resistances) \
            and not any(r.startswith('MR_VUL_'+res) for r in self.resistances):
                self.resistances = self.resistances + ('MR_RES_'+res+'0', )

        return '  '.join(sorted(resist_dots(r) for r in self.resistances))

    def __repr__(self):
        return self.name


def main():
    all_monsters = {}
    for m in mondata:
        mons = Monster(*m)
        all_monsters[mons.id] = mons
    monsters = all_monsters.itervalues

    for m in sorted(all_monsters.values(), key=lambda m: m.id):
        print "%-22.22s  %s" % (m.name, m.resists)

    print
    print 'Monsters by MR (270 == immune)'
    print '------------------------------'
    for m in sorted(all_monsters.values(), key = attrgetter('mr'), reverse=True):
        print "% 5d  %s" % (m.mr, m)

    print
    print 'Monsters by move speed (player: usually 10)'
    print '-------------------------------------------'
    for m in sorted(all_monsters.values(), key = lambda m: m.energy.move, reverse=True):
        print "% 5.4s  %s" % (m.energy.move, m)

    print


def whatever():
    s = ""
    field = attribute = None
    if False:
        pass
    elif field == 'hd':
        die = attribute
        s += "%s" % die[0]
        s += "\n"
        s += "hp calc: %dd%d[%+d]%+d" % (int(die[0]), int(die[2])+1, int(die[1]), int(die[3])-int(die[0]))
        s += "\n"
        s += "average hp: %s" % (int(die[0])*(int(die[1])+(float(die[2])+2)/2)+int(die[3])-int(die[0]))

    fnmap = {
    }

    for (abbr, fn) in fnmap.iteritems():
        if abbr.startswith(sys.argv[1]):
            fn()


if __name__ == '__main__':
    main()
