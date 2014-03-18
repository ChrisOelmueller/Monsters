# Remove some mon-data headers, test spawner, AXED_MON
# cat mon-data.h | python2 newlife.py > newlife.dot
# neato -Tpng newlife.dot > newlife.png (or any other dot algorithm)

import sys
import re

data = sys.stdin.read()

# Settings
indent = 4

# Modes: "print", "dot"
mode = "dot"

# Strip out axed monster
data = re.sub("(?ms)#define AXED.*?Real mon.*?$", "", data)

# Strip out block comments
data = re.sub("(?ms)\/\*.*?\*\/", "", data)

# Strip other comments
data = re.sub('//.*', '', data)
data = re.sub('#.*', '', data)

# Replace energy:
def energy(x):
    #print "Energy:", x.groups()
    return "(%s, %s)" % (x.group(1), x.group(2))
data = re.sub('([A-Z0-9_-]*_ENERGY)\((.*?)\)', energy, data)

# Replace mrd entries (with placeholder for parens)
def mrd(x):
    #print "mrd:", x.groups()
    return "<<{{%s}},%s>>" % (x.group(1), x.group(2))
data = re.sub('(?ms)mrd\((.*?)(\d*)\s*\)', mrd, data)

# Handle lone mrds that must be wrapped as tuples
def tuplify(x):
    #print "Tuplify:", "\n", data, "\n", "Match:", x.group(0)
    return  "%s(%s)," % x.groups()
data = re.sub('(\s*)(<<.*?>>,)', tuplify, data)

# Replace pipes by commas
def pipes(x):
    #print "Pipes:", "\n", data, "\n", "Match:", x.group(0)
    return "(%s)" % re.sub('(?ms)\s*\|\s*', ',', x.group(0))
data = re.sub('(?m)(\(.*\)|<<.*>>|[A-Z0-9_-]*)(\s*\|\s*(\(.*\)|<<.*>>|[A-Z0-9_-]*))+', pipes, data)

# Stringify bare enums:
def stringify(x):
    return "'%s'" % x.group(1)
#data = re.sub("(?<!['\"])([A-Z0-9_-]+)", stringify, data)
data = re.sub("(?<!['\"])([A-Z0-9_-]{2,})", stringify, data)

# Replace placeholders
data = re.sub('(<<|{{)', '(', data)
data = re.sub('(>>|}})', ')', data)

# Replace }s by )s unless they're a monster glyph.
data = re.sub("}(?!['\"]);*", ')', data)
data = re.sub("{", '(', data)

# Last change needed to make it valid Python:
data = re.sub("static monsterentry mondata\[\] = ", "", data)

# Eval it, storing it as a tuple
mondata = eval(data)

# Titles for the fields, in order, indexed from 0
fields = (
    'id',
    'glyph',
    'color',
    'name',
    'flags',
    'resistances',
    'mass',
    'experience modifier',
    'genus',
    'species',
    'holiness',
    'magic resistance',
    'attacks',
    'hit dice',
    'ac',
    'ev',
    'spellbook',
    'corpse type',
    'zombie type',
    'shout type',
    'intelligence',
    'habitat',
    'flight class',
    'speed',
    'energy',
    'item use',
    'eats',
    'size',
)

# Formatting functions
def resist_dots(resist, level=1):
    level = min(level, 3)
    # HACK:
    if re.search('VUL', resist) is not None:
        return "%s%-20s (%s%s)" % (' ' * indent, resist, "x" * level, "."*(3-level))
    else:
        return "%s%-20s (%s%s)" % (' ' * indent, resist, "*" * level, "."*(3-level))

# Iterate over monsters, building a string as we go.
if mode == 'print':
    str = ""
    for monster in mondata:
        index = 0
        # Ignore these guys. Pointless.
        if monster[0] == 'MONS_TEST_SPAWNER':
            continue
        str += "===%s (%s)===\n" % (monster[3], monster[0])
        for attribute in monster:
            field = fields[index]
            str += "%s: " % field
            if field == 'flags' and isinstance(attribute, tuple):
                    for flag in attribute:
                        str += flag + ", "
            elif field == 'resistances':
                str += "\n"
                # Single resist, single level.
                if not isinstance(attribute, tuple):
                    str += resist_dots(attribute)
                else:
                    # Multiple resists
                    for resistance in attribute:
                        # Single level
                        if not isinstance(resistance, tuple):
                            str += resist_dots(resistance) + "\n"
                        # Multiple levels (possibly for multiple resists)
                        else:
                            # HACK: Cope with extraneous tuples
                            if len(resistance) == 1:
                                resistance = resistance[0]
                            resists, level = resistance
                            for resist in resists:
                                if not isinstance(resist, tuple): # Again, hack.
                                    str += resist_dots(resist, level) + "\n"
                                else:
                                    for r in resist:
                                        str += resist_dots(r, level) + "\n"
            elif field == 'attacks':
                str += "\n"
                for attack in attribute:
                    if isinstance(attack, tuple):
                        str += "%s%s (%s, %s)\n" % (' ' * indent, attack[2], attack[0], attack[1])
            elif field == 'hit dice':
                die = attribute
                str += "%s" % die[0]
                str += "\n"
                str += "hp calc: %dd%d[%+d]%+d" % (int(die[0]), int(die[2])+1, int(die[1]), int(die[3])-int(die[0]))
                str += "\n"
                str += "average hp: %s" % (int(die[0])*(int(die[1])+(float(die[2])+2)/2)+int(die[3])-int(die[0]))
            elif field == 'energy' and isinstance(attribute, tuple):
                    if len(attribute) == 2:
                        str += "%s, %s" % attribute
                    else:
                        str += "It's Complicated"
            else:
                str += "%s" % attribute

            str += "\n"
            index += 1
        str += "\n"
    print str
elif mode == 'dot':
    i = {}
    for x in range(len(fields)):
        i[fields[x]] = x

    data = {'id' : {}, 'name' : {}, 'genus' : {}, 'species' : {}, 'holiness' : {}}
    viz = {
        'id': ("lightblue", "white", "12"),
        'genus' : ("dodgerblue4", "white", "14"),
        'species' : ("steelblue3", "white", "14"),
        'holiness' : ("navy", "white", "18"),
        'unique' : ("seagreen", "white", "18")
    }
    for m in mondata:

        attr = {
            'id' : m[i['id']],
            'name' : m[i['name']],
            'genus' : m[i['genus']],
            'species' : m[i['species']],
            #'holiness' : m[i['holiness']],
        }

        flags = m[i['flags']]
        if not isinstance(flags, tuple):
            flags = (flags,)
        attr['unique'] = ('M_UNIQUE' in flags)

        for k, v in attr.items():
            if k == 'name' or k == 'unique':
                continue
            if data[k].get(v) is None:
                data[k][v] = [attr]
            else:
                data[k][v].append(attr)


    nodes = ""
    connections = ""

    print "digraph Crawl {"
    #print 'CENTER [label="DUNGEON CRAWL", shape="box", style="filled", fillcolor="navy", fontcolor="white", fontsize="40"]'
    for type, dict in data.items():
        if type != 'id':
            a = 1
            #for key, monsters in dict.items():
        # Set up each genus, species, and holiness.
                #print '%s%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (type, key, key, viz[type][0], viz[type][1], viz[type][2])
                #if type == 'genus':
                    #print 'CENTER -> %s%s;' % (type, key)
        else:
            for key, monsters in dict.items():
                for monster in monsters:
                    if monster['genus'] == monster['species'] and monster['species'] == monster['id']:
                        nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['genus'][0], viz['genus'][1], viz['genus'][2])
                        #connections += 'species%s -> monster%s [arrowhead=".2"];' % (monster['species'], monster['id'])
                    elif monster['species'] == monster['id']:
                        nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['species'][0], viz['species'][1], viz['species'][2])
                        #nodes += "\n" + 'species%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['species'][0], viz['species'][1], viz['species'][2])
                        connections += "\n" + 'monster%s -> monster%s [arrowhead="none"];' % (monster['genus'], monster['species'])
                    else:
                        if monster.get('unique') is True:
                            nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['unique'][0], viz['unique'][1], viz['unique'][2])
                        else:
                            nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['id'][0], viz['id'][1], viz['id'][2])
                        connections += "\n" + 'monster%s -> monster%s [arrowhead="none"];' % (monster['species'], monster['id'])
                        #print 'holiness%s -> monster%s [arrowhead=".2"];' % (monster['holiness'], monster['id'])
            #print '%s [label="%s"]' % (id, name)
            #print '%s [fontsize="%s"]' % (id, name)
    print nodes
    print connections
    print "overlap=prism;"
    print "}"


 #   str = 
  #  str = "}"
   # print str
