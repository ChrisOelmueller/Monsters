# Remove some mon-data headers, test spawner, AXED_MON
# cat mon-data.h | python2 newlife.py > newlife.dot
# neato -Tpng newlife.dot > newlife.png (or any other dot algorithm)

import sys
import re

data = sys.stdin.read()

# Settings
indent = 4

# Strip out axed monster
data = re.sub("(?ms)#define AXED.*?Real mon.*?$", "", data)

# Strip out block comments
data = re.sub("(?ms)\/\*.*?\*\/", "", data)

# Strip other comments
data = re.sub('//.*', '', data)
data = re.sub('#.*', '', data)

# Replace energy:
def energy(x):
    return "(%s, %s)" % (x.group(1), x.group(2))
data = re.sub('([A-Z0-9_-]*_ENERGY)\((.*?)\)', energy, data)

# Replace mrd entries (with placeholder for parens)
def mrd(x):
    return "<<{{%s}},%s>>" % (x.group(1), x.group(2))
data = re.sub('(?ms)mrd\((.*?)(\d*)\s*\)', mrd, data)

# Handle lone mrds that must be wrapped as tuples
def tuplify(x):
    return  "%s(%s)," % x.groups()
data = re.sub('(\s*)(<<.*?>>,)', tuplify, data)

# Replace pipes by commas
def pipes(x):
    return "(%s)" % re.sub('(?ms)\s*\|\s*', ',', x.group(0))
data = re.sub('(?m)(\(.*\)|<<.*>>|[A-Z0-9_-]*)(\s*\|\s*(\(.*\)|<<.*>>|[A-Z0-9_-]*))+', pipes, data)

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
    if re.search('VUL', resist) is not None:
        return "%s%-20s (%s%s)" % (' ' * indent, resist, "x" * level, "."*(3-level))
    else:
        return "%s%-20s (%s%s)" % (' ' * indent, resist, "*" * level, "."*(3-level))

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
for type, dict in data.items():
    if type != 'id':
        a = 1
    else:
        for key, monsters in dict.items():
            for monster in monsters:
                if monster['genus'] == monster['species'] and monster['species'] == monster['id']:
                    nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['genus'][0], viz['genus'][1], viz['genus'][2])
                elif monster['species'] == monster['id']:
                    nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['species'][0], viz['species'][1], viz['species'][2])
                    connections += "\n" + 'monster%s -> monster%s [arrowhead="none"];' % (monster['genus'], monster['species'])
                else:
                    if monster.get('unique') is True:
                        nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['unique'][0], viz['unique'][1], viz['unique'][2])
                    else:
                        nodes += "\n" + 'monster%s [label="%s", shape="box", style="filled", fillcolor="%s", fontcolor="%s", fontsize="%s"];' % (monster['id'], monster['name'], viz['id'][0], viz['id'][1], viz['id'][2])
                    connections += "\n" + 'monster%s -> monster%s [arrowhead="none"];' % (monster['species'], monster['id'])
print nodes
print connections
print "overlap=prism;"
print "}"
