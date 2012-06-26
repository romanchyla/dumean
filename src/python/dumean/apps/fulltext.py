#!python -u

import sys
import os
_d = os.path.dirname(__file__)
if _d not in sys.path:
    sys.path.append(_d)




MAX_AUTOCOMPLETE = 10
MAX_SIMILAR = 10
INDEX = os.path.join(_d, 'indices/wordnet')

from whisper import app, test, Whisperer

class FulltextWhisper(Whisperer):
    def format_value(self, entry):
        if len(entry) > 1:
            entry = 'fulltext:(%s)' % ' OR '.join(entry)
        else:
            entry = 'fulltext:%s' % entry.pop()
        return entry

#test(INDEX, 'schoolz', [('school', None)])

application = app(INDEX, MAX_AUTOCOMPLETE, MAX_SIMILAR, FulltextWhisper)