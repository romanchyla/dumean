#!python -u

import sys
import os
import dumean

_d = os.path.abspath(os.path.join(os.path.dirname(dumean.__file__), '../../..'))
if _d not in sys.path:
    sys.path.append(_d)




MAX_AUTOCOMPLETE = 10
MAX_SIMILAR = 10
INDEX = os.path.join(_d, 'indices/random')

from whisper import app, test, Whisperer
from dumean import whisperer

class RandomWhisper(Whisperer):
    def __init__(self, index_dir, max_autocomplete, max_similar):
        self.whisperer = whisperer.LuceneWhisperer()
        self.whisperer.open(index_dir, ramdir=False)
        self.max_autocomplete = max_autocomplete
        self.max_similar = max_similar
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

#test(INDEX, 'xA', [('xA9Pv YRLVs', None)], cls=RandomWhisper)

get_worker, application = app(INDEX, MAX_AUTOCOMPLETE, MAX_SIMILAR, RandomWhisper)

def run_wsgi():
    port = 8080
    from wsgiref.util import setup_testing_defaults
    from wsgiref.simple_server import make_server
    httpd = make_server('', port, application)
    print "Serving on port %s..." % port
    httpd.serve_forever()


if __name__ == "__main__":
    run_wsgi()