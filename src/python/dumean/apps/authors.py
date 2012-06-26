#!python -u

import sys
import os
_d = os.path.dirname(__file__)
if _d not in sys.path:
    sys.path.append(_d)




MAX_AUTOCOMPLETE = 10
MAX_SIMILAR = 10
INDEX = os.path.join(_d, 'indices/authors')

from whisper import app, test, Whisperer

class AuthorWhisper(Whisperer):
    def __init__(self, *args, **kwargs):
        Whisperer.__init__(self, *args, **kwargs)
        self.whisperer.setAccuracy(0.5)

    def format_data(self, data):
        return '|'.join(data)

    def format_value(self, entry):
        if len(entry) > 1:
            entry = 'author:(%s)' % ' OR '.join(entry)
        else:
            entry = 'author:%s' % entry.pop()
        return entry
    def get_similar(self, word, data):

        # for authors, we don't have any information so we'll search
        # for similar names
        if not data or (len(data) > 1 and not data[0]):
            return self.get_suggestions(word)
        recs = []
        for n in data[0].split('|'):
            recs.append({'label': n, 'value': n})
        return recs


    def prepare_entry(self, info):
        """Info Entry is actually array of possible records
        becaue every word may have many meanings"""
        score,entry,data = 0.0,set(),[]
        key = '%s (%d)' % (info[0]['key'], len(info))
        for x in info:
            if ' ' in x['key']:
                entry.add('"%s"' % x['key'])
            else:
                entry.add(x['key'])
            data.append(x['value'])
            score += x['score']
        return {'label':key, 'value':self.format_value(entry),
                'data':self.format_data(data)}


test(INDEX, 'Ellis', [('Ellis', ['Ellis J', 'Ellis J.R'])],
     cls=AuthorWhisper)

application = app(INDEX, MAX_AUTOCOMPLETE, MAX_SIMILAR, AuthorWhisper)