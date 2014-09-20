# See bottom of file for a list of possible arguments.
# As an example,
#   monsters.py re
# calls print_resists.

import os
import os.path
import sys
import re

from collections import defaultdict
from operator import attrgetter
from pprint import pprint

pprint = pprint

spl_data_path = os.path.join(os.path.expanduser('~'),
                             "crawl/crawl-ref/source/spl-data.h")
book_data_path = os.path.join(os.path.expanduser('~'),
                              "crawl/crawl-ref/source/book-data.h")

def read_spl_data(h=spl_data_path, debug=False):
    """Read spl-data.h"""
    data = unicode(open(h).read())

    data = re.sub("(?ms).*static const struct spell_desc spelldata.. =",
                  "", data)

# Strip other comments
    data = re.sub('//.*', '', data)
    data = re.sub('#.*', '', data)

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

    data = re.sub(r"\bfalse\b", 'False', data)
    data = re.sub(r"\btrue\b", 'True', data)

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

def read_book_data(h=book_data_path, debug=True):
    """Read spl-data.h"""
    data = unicode(open(h).read())

    data = re.sub("(?ms).*static spell_type spellbook_template_array.."
                        ".SPELLBOOK_SIZE. =",
                  "", data)

# Convert commented book/rod names into strings
    data = re.sub('{   // (.*)', r'{ "\1",', data)
    #data = re.sub('// Rods.*', '("__rods_start", ),', data)

# Strip other comments
    data = re.sub('//.*', '', data)
    data = re.sub('#.*', '', data)

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

    data = re.sub(r"\bfalse\b", 'False', data)
    data = re.sub(r"\btrue\b", 'True', data)

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


spldata = read_spl_data()
bookdata = read_book_data()


class Book(object):
    def __init__(self,
        id,
        *spells,
        **kwargs):
        self.id     = id
        self.spells = [s for s in spells if s != 'SPELL_NO_SPELL']
        self.rod    = self.id.startswith('Rod ') or self.id.endswith(' rod')


class Spell(object):

    def __init__(self,
        id,
        name,
        schools,
        flags,
        level,
        power_cap,
        min_range,
        max_range,
        noise_mod,
        target_prompt,
        needs_tracer,
        utility_spell,
        *args, **kwargs):

        self.id          = id
        self.name        = name
        if isinstance(schools, tuple):
            self.schools   = schools
        elif schools == 0:
            self.schools   = ('SPTYP_NO_SCHOOL', )
        else:
            self.schools   = (schools, )
        self.level       = level
        self.power_cap     = power_cap
        self.min_range     = min_range
        self.max_range     = max_range
        self.noise_mod     = noise_mod
        self.target_prompt = target_prompt
        self.needs_tracer  = needs_tracer
        self.utility_spell = utility_spell

        if isinstance(flags, tuple):
            self.flags     = ', '.join(f for f in sorted(flags))
        else:
            self.flags     = flags

    def __repr__(self):
        return ' L%s %s' % (self.level, self.name)


def title(heading, x='-'):
    print '\n' + heading + '\n' + x * len(heading)


def main():
    all_spells = dict()
    school_spells = defaultdict(list)
    for s in spldata:
        spell = Spell(*s)
        all_spells[spell.id] = spell
        for school in spell.schools:
            school_spells[school].append(spell)

    all_books = dict()
    all_rods = dict()
    for b in bookdata:
        book = Book(*b)
        if book.rod:
            all_rods[book.id] = book.spells
        else:
            all_books[book.id] = book.spells

    def print_spellbooks():
        for thing in (all_rods, all_books):
            for (name, spells) in thing.iteritems():
                if not spells:
                    continue
                title(name)
                for s in spells:
                    print all_spells[s]

    def print_everything():
        for school, spells in school_spells.items():
            title(school)
            for s in sorted(spells, key=attrgetter('level'), reverse=True):
                print s

    fnmap = {
        'everything': print_everything,

        'books': print_spellbooks,
        'rods': print_spellbooks,
        'spellbooks': print_spellbooks,
    }

    for (abbr, fn) in fnmap.iteritems():
        if abbr.startswith(sys.argv[1]):
            fn()


if __name__ == '__main__':
    main()
