#!python -u

import sys
import os
_d = os.path.dirname(__file__)
if _d not in sys.path:
    sys.path.append(_d)




MAX_AUTOCOMPLETE = 10
MAX_SIMILAR = 10
INDEX = os.path.join(_d, 'indices/hepnet')

from whisper import app, test, Whisperer

class TaggingWhisper(Whisperer):
    def get_suggestions(self, word):
        recs = self.whisperer.findWildcard('%s*' % word)
        out = []
        seen = {}
        for r in recs:
            seen[r['key']] = 1
            out.append({'label': r['key'], 'value': r['key'], 'data': r['value']})

        if len(out) < self.max_autocomplete:
            others = Whisperer.get_suggestions(self, word)
            i = 0
            while len(out) < self.max_autocomplete and i < len(others):
                x = others[i]
                if x['label'] not in seen:
                    out.append(x)
                i += 1
        return out

    def format_value(self, entry):
        return entry.pop()

#test(INDEX, 'scalar', [('particle', None)], cls=TaggingWhisper)

application = app(INDEX, MAX_AUTOCOMPLETE, MAX_SIMILAR, TaggingWhisper)