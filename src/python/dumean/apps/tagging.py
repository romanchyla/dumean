#!python -u

import sys
import os
import dumean

_d = os.path.abspath(os.path.join(os.path.dirname(dumean.__file__), '../../..'))
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
    
    def get_similar(self, word, data):
        if not data:
            try:
                data = self.whisperer.findSimilarByWord(word,
                                                    max=self.max_similar+10)
                data = data[0]['value']
            except:
                # error, the word was not found
                data = self.get_suggestions(word)
                data.append('<2nd lookup, %s not found>' % word)
                return data
        semes = data.split(' ')
        
        data = self.whisperer.getSimilarBySem(semes, 10, True)
            
        if len(data) < 2:
            return []
        records = []
        for info in data:
            if info['key'] != word:
                records.append(self.prepare_entry([info]))
        return records[0:self.max_similar]

#test(INDEX, 'scalar', [('particle', None)], cls=TaggingWhisper)
#test(INDEX, 'scalar', [('boson', '0012v _rel194 _rel195')], cls=TaggingWhisper)

get_worker, application = app(INDEX, MAX_AUTOCOMPLETE, MAX_SIMILAR, TaggingWhisper)