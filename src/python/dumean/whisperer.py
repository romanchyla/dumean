import os
import glob
import sys
import dumean
import traceback
import time
from lucene import WildcardQuery, Term, IndexSearcher, FSDirectory, Field,\
                   RAMDirectory, File

dumeanj = None


class LuceneWhisperer():
    """
    Provides an easy wrapper for the Lucene whisperer - the service that does the: "Did you mean..?
    """
    def __init__(self):
        """When instantiated, it does nothing besides loading the java VM
        @see: self.open()
        """

        global dumeanj
        self.opened = False
        self.indexer = None
        self.worker = None
        self.searcher = None
        self.index_dir = None

        if not dumeanj:
            dumeanj = dumean.get_java_module()

        dumean.start_jvm()


    def __del__(self):
        self.close()


    def open(self, index_dir, fields=('key', 'mode', 'value'),
             reindex=None,
             ramdir=False):
        """ Opens a index for writing
        @param index_dir: path to the folder where Lucene index is (or should be created)
        @keyword fields: list of fields that we want to get from Lucene for a given match,
                if empty, the default fields will be returned
        @keyword reindex: list of glob patterns to find files which should be indexed
                (use this argument if the index is empty or if you want to reindex data
                before starting to use the dictioanry)
        """

        if fields and isinstance(fields, list):
            raise Exception("The fields argument must be a tuple")

        self.indexer = dumeanj.IndexDictionary
        if reindex:
            self.reindex(index_dir, reindex)

        if not os.path.isdir(index_dir):
            raise Exception("The index_dir does not exist : %s" % index_dir)
        try:
            if fields:
                self.worker = dumeanj.LuceneWhisperer(index_dir, fields)
            else:
                self.worker = dumeanj.LuceneWhisperer(index_dir)
        except Exception, msg:
            if 'FileNotFoundException' in str(msg):
                traceback.print_exc()
                raise Exception(msg, 'The index is missing or broken, you may want to use reindex argument.')
            else:
                traceback.print_exc()
                raise Exception(msg)

        self.index_dir = index_dir

        if ramdir:
            self.directory = RAMDirectory(index_dir)
        else:
            self.directory = FSDirectory.open(File(index_dir))
        self.searcher = IndexSearcher(self.directory, True) #readonly
        self.fields = fields
        self.opened = True


    def close(self):
        if self.opened:
            self.worker.close()
            self.searcher.close()
            self.opened = False


    def getSuggestions(self, term, max=8, enrich=True, pythonic=True):
        """Finds terms similar to the supplied term
        @param term: string
        @keyword max: int, how many terms should lucene return
        @keyword enrich: boolean, whether to harvest information
            for the discovered candidates, default is True
        @keyword pythonic: boolean, whether to convert java object
            automatically to the python obj, default is True
        @return: Java object as returned from Lucene, use
            convertToPython() if you want to get its python
            version. The java object will be empty if nothing
            similar was found"""


        # this will be a java HashMap
        suggestions = self.worker.getSuggestions(term, max)

        # harvest fields
        if enrich:
            self.addInfoToLabels(suggestions)

        if pythonic:
            return self.convertToPython(suggestions)

        return suggestions


    def addInfoToLabels(self, java_obj):
        """Enriches the java_obj with information about the terms
        Typically, java_obj is
            {'term1':{'#pos':1}, 'term2':...}
        and after this call, the java obj is enriched to:
            {'term1':{'#pos':1, info:[{'key': 'term1', 'mode': 'hqs', value: 'abd dcd'},
                                      {'key': 'term1' ....}]},
             'term2':...}
        Note that there may be more definitons of the same term, therefore
        info is a list. Also, this call does not return anything, the changes
        are made directly to the java_obj
        """
        # TODO - error handling/type checking
        self.worker.addInfoToLabels(java_obj)


    def getSimilarBySem(self, semes, max, pythonic=True):
        """Finds entries that share at least one of the semes
        @param semes: list of semes to search for
        @param max: int, how many similar items max to return
        @keyword pythonic: boolean, whether to automatically convert
            the results into python structure, default=True
        @return: records as retrieved by Lucene (possibly converted to
            python list)"""

        if not isinstance(semes, list):
            raise Exception("Semes argument must be a list")
        results = self.worker.getSimilarBySem(semes, max)

        if pythonic:
            results = self.convertToPython(results)
        return results

    def findSimilarByWord(self, word, max, pythonic=True):
        """
        Asks LuceneWhisperer to find entries that are semantically
        similar to this word - the word should exist (ie. you are
        sure it is there - if you are not, then use the getSuggestions
        first. Java originally returns a list of results - it is
        in a format: [info, sims, info, sims, info, sims...]
        The info is a list that contains information about the requested
        word, sims are entries that are similar based on their semes.

        And because there may be more than 1 definition of the word in
        the dictionary, the results may be more than 1 pair

        @param word: string, term to find in the key-raw index
        @param max: how many items to return for the similarity search
        @keyword pythonic: boolean, whether to convert the structure to
                the pythonic form, default=True
        @return: either original java struct, or list [info, sims, info...]
                if nothing was found and pythonic was requested, it will
                return [{}, []] -- note, that pythonic result has on the
                first position dictionary, whilst java struct will contain
                [ArrayList, ArrayList...]
        """

        results = self.worker.findSimilarByWord(word, max)

        if pythonic:
            py_results = []
            if not results.isEmpty():
                size = results.size()
                i = 0
                while size > i:
                    # because we have a conversion from this structure, I use it as it is
                    r = self.convertToPython(dumeanj.ArrayList.cast_(results.get(i)))
                    # but to make it easier, I will place the dictionary on the first position
                    py_results.append(r[0])
                    py_results.append(self.convertToPython(dumeanj.ArrayList.cast_(results.get(i+1))))
                    i += 2
                return py_results
            else:
                return [{},[]]
        return results


    def convertToPython(self, java_results):
        """converts the java_obj returned from the lucene into a pythonic structure"""
        if 'HashMap' in java_results.class_.name:
            out = {}
            for key in java_results.keySet():
                out[key] = {}
                #print "key, ", key
                #print "value, ", java_results.get(key)
                record = dumeanj.HashMap.cast_(java_results.get(key))
                for field in record.keySet():
                    if field == 'info':
                        out[key]['info'] = []
                        info = dumeanj.ArrayList.cast_(record.get(field))
                        for item in info:
                            rec = {}
                            ind_info = dumeanj.HashMap.cast_(item)
                            for i_info in ind_info.keySet():
                                rec[i_info] = self._getValue(ind_info.get(i_info))
                            out[key]['info'].append(rec)
                    else:
                        #print key, record.get(field)
                        out[key][field] = self._getValue(record.get(field))
            return out
        elif 'Array' in java_results.class_.name:
            out = []
            for x in java_results:
                x = dumeanj.HashMap.cast_(x)
                rec = {}
                for field in x.keySet():
                    rec[field] = self._getValue(x.get(field))
                out.append(rec)
            return out
        else:
            raise Exception("Wrong java arg passed in: %s" % java_results)

    def _getValue(self, java_obj):
        s = None
        try:
            s = dumeanj.Integer.cast_(java_obj)
            s = int(s.toString())
        except TypeError:
            try:
                s = dumeanj.Float.cast_(java_obj)
                s = float(s.toString())
            except TypeError:
                s = java_obj.toString()
        return s

    def getTree(self, name):
        hash = ''

    def reindex(self, index_dir, glob_pattern):
        """Re-builds the spellchecking/did-you-mean
        dictionary.
        @var glob_pattern: list of patterns to search for files
        @var index_dir: path to folder where dictionary will be
            saved, if empty the current datadir will be used
        @return: number of files, that were added to the index
        """
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)

        files = []
        if isinstance(glob_pattern, basestring):
            glob_pattern = [glob_pattern]
        for patt in glob_pattern:
            for f in glob.glob(patt):
                files.append(os.path.abspath(f))
        files = tuple(files)
        files_indexed = self.indexer.reindexFiles(files, index_dir)
        return files_indexed

    def setAccuracy(self, acc):
        if acc <0 or acc > 1:
            raise Exception('Accuracy may be between 0 and 1')
        if self.worker:
            self.worker.setAccuracy(acc)


    def findWildcard(self, word, field='key', max=10):
        query = WildcardQuery(Term(field, word))
        searcher = self.searcher
        hits = searcher.search(query, None, max)
        recs = []
        fields = self.fields

        for hit in hits.scoreDocs:
            # i can't figure out how to deal with ScoreDocs instance
            # does it already hold doc object?
            doc = searcher.doc(hit.doc)
            recs.append(doc)

        out = []
        if fields:
            for doc in recs:
                r = {}
                for f in fields:
                    r[f] = doc.get(f)
                out.append(r)
        else:
            for doc in recs:
                r = {}
                for f in doc.fields():
                    f = Field.cast_(f)
                    r[f.name()] = f.stringValue()
                out.append(r)
        return out





def jaccard_similarity(set1, set2):
    shared = set1.intersection(set2)
    all_unique = set1.union(set2)
    res = float(len(shared)) / len(all_unique)
    if len(set1) > len(set2): # for broader terms
        return -res
    else:
        return res            # for more specific terms

class BinaryTree:
    def __init__(self):
        self.tree = EmptyNode()
    def __repr__(self):
        return str(self.tree)
    def lookup(self, key):
        return self.tree.lookup(key)
    def insert(self, key, val):
        self.tree = self.tree.insert(key, val)
    def broader(self, level):
        return self.tree.left.show(level)
    def narrower(self, level):
        return self.tree.right.show(level)

class EmptyNode:
    def __repr__(self):
        return '*'
    def lookup(self, key):                               # fail at the bottom
        return None
    def insert(self, key, val):
        return BinaryNode(self, key, val, self)          # add node at bottom
    def show(self, level):
        return None

class BinaryNode:
    similarity = jaccard_similarity
    def __init__(self, left, key, val, right):
        self.key,  self.val   = key, val
        self.left, self.right = left, right
    def lookup(self, val):
        sim = jaccard_similarity(self.val, val)
        if sim == 1.0:
            return self.key
        elif sim < 0:
            return self.left.lookup(val)                 # look in left
        else:
            return self.right.lookup(val)                # look in right
    def insert(self, key, val):
        sim = jaccard_similarity(self.val, val)
        if sim == 1.0:
            self.key += ',%s' % key
        elif sim < 0:
            self.left = self.left.insert(key, val)       # grow in left, broader terms
        else:
            self.right = self.right.insert(key, val)     # grow in right, narrower terms
        return self

    def __str__(self):
        return '[%s:%s]' % (self.key, ','.join(self.val))
    def __repr__(self):
        s = ('( %s, <- %s=%s ->, %s )' %
                 (self.left, self.key, ','.join(self.val), self.right))
        return s

    def show(self, level):
        if level:
            return ('( %s, <- %s=%s ->, %s )' %
                 (self.left.show(level-1), self.key, ','.join(self.val), self.right.show(level-1)))



def print_tree(T, sep=3, tree_size=30):
    """Print dendrogram of a binary tree.  Each tree node is represented by a length-2 tuple."""

    def is_pair(T):
        try:
            return T.left is not '*' or T.right is not '*'
        except:
            pass

    def max_height(T):
        if isinstance(T, EmptyNode):
            return 1
        h = max(len(str(T)), len(str(T.left)), len(str(T.right)))
        return h + sep + tree_size

    active_levels = {}

    def traverse(T, h, isFirst, toprn=''):
        if is_pair(T):
            traverse(T.left, h-sep, 1, toprn=str(T))
            #s = list(str(T)) + [' ']*(h-sep-len(str(T)))
            s = [' ']*(h-sep)
            s.append('|')
        else:
            s = list(toprn or str(T))
            s.append(' ')


        while len(s) < h:
            s.append('-')

        if (isFirst >= 0):
            s.append('+')
            if isFirst:
                active_levels[h] = 1
            else:
                del active_levels[h]

        A = list(active_levels)
        A.sort()
        for L in A:
            if len(s) < L:
                while len(s) < L:
                    s.append(' ')
                s.append('|')

        if hasattr(T, 'root'):
            s += str(T)
        print ''.join(s)

        if is_pair(T):
            traverse(T.right, h-sep, 0)

    if not hasattr(T, 'left'):
        T = T.tree
    T.root = True
    traverse(T, max_height(T), -1)


def test():
    worker = LuceneWhisperer('/tmp/whisper/')
    input = "article"
    suggestions = worker.getSuggestions(input, max=8)
    print suggestions

    if suggestions:
        # sort terms by their position (similarity in labels)
        terms = suggestions.keys()
        terms.sort(key=lambda x: suggestions[x]['#pos'])

        #now should be the question: Did you mean?
        selected_term = terms[4] # H-particle

        info = suggestions[selected_term]['info']

        tt = worker.findSimilarByWord(selected_term, 1000)

        tree = BinaryTree()

        for term_definition in info:
            #find the similar terms (by semes)
            semes = term_definition['value'].split()
            similar = worker.getSimilarBySem(semes, 1000)

            tree.insert(selected_term, set(semes))
            tree_size = len(selected_term)
            for sim in similar:
                tree_size += len(sim['key'])
                tree.insert(sim['key'], set(sim['value'].split()))
                #print sim

        print tree.narrower(1)
        print tree.broader(2)
        print_tree(tree, tree_size=200)



def testtree():
    t = BinaryTree()
    for (key, val) in [('h-particle', 'A B C D'), ('particle', 'A B'), ('h-boson', 'D C B A')]:
        print (key, val)
        t.insert(key, set(val.split()))
        print t
    print t
    print t.lookup(set(['dde', 'eee'])), t.lookup(set(['abc', 'dde']))
    t.insert('related', set('X Y D'.split()))
    t.insert('narrower', set('A B C D E'.split()))                       # changes key's value
    t.insert('narrower-but-different', set('A B C D E F H'.split()))
    t.insert('narrowest', set('A B C D E F H I'.split()))
    print t

    print '---------'
    print t.broader(1)
    print t.narrower(2)

    print print_tree(t.tree)


def console_app():
    basedir = os.path.abspath(os.path.join(os.path.dirname(dumean.__file__), '../../..'))
    _dict = {'max': 1000,
             'options' : 8,
             'basedir' : basedir,
             'index' : '%s/indices/whisper' % basedir,
             'blimit': 20,
             'glob': '%s/indices/names.seman*' % basedir,
             }
    worker = LuceneWhisperer()
    if not os.path.exists(_dict['index']):
        print 'Building the index %s from %s' % (_dict['index'], _dict['glob'])
        worker.open(_dict['index'], reindex=_dict['glob'])
        worker.close()
    worker.open(_dict['index'])

    def print_help():
        testtree()
        print "suggest   - proposes terms from the taxonomy\n" \
              "btree     - shows binary tree (blimit sets limit of nodes)\n" \
              "broader   - shows broader terms\n" \
              "narrower  - shows narrower terms\n" \
              "reindex   - rebuilds dictionary\n"
        print "----\n"
        print ":h - gives help\n" \
              ":set variable=value\n" \
              "    currently: %s\n" % str(_dict).replace(", '", ",\n    '")

    btree = similar = suggestions = None

    while True:
        var = raw_input("You command master? ")
        var = var.lstrip()
        if var:
            var = var.lower()
            if ":h" in var:
                print_help()
            elif ':set' in var:
                try:
                    k,v = var.split()[-1].split('=')
                    if v.isdigit():
                        _dict[k] = int(v)
                    else:
                        _dict[k] = v
                except Exception, e:
                    print "Error parsing : %s" % var
                    print str(e)
                    print 'The correct format is: ":set var=val"'
            elif var.find('suggest') == 0:
                var = raw_input("Please type word(s):")

                while var:
                    start = time.time()
                    suggestions = worker.getSuggestions(var, max=_dict['max'])
                    end = time.time() - start
                    print 'retrieved in: %0.5f s' % end
                    if suggestions:

                        names = suggestions.keys()
                        def show_names():
                            i = 0
                            for s in names:
                                if i > _dict['options']:
                                    break
                                print "%d : %s" % (i, s)
                                i += 1
                        show_names()

                        var = raw_input("Your choice? ")
                        while var.isdigit():
                            v = int(var)
                            similar = worker.findSimilarByWord(names[v], _dict['max'])
                            if similar:
                                info = similar[0]
                                def build_tree():
                                    print "key: %s" % info['key']
                                    print "value: %s" % info['value']
                                    print "mode: %s\n\n" % info['mode']
                                    tree = BinaryTree()
                                    for t in similar[1][:_dict['blimit']]:
                                        tree.insert(t['key'], set(t['value'].split()))
                                    print "tree: ", print_tree(tree)
                                    print
                                    print "total entries: %d - blimit is: %d" % (len(similar[1]), _dict['blimit'])
                                    print
                                    return tree

                                btree = build_tree()
                                show_names()
                            else:
                                print "Nothing found for: %s" % names[v]
                            var = raw_input("Not enough? ")

            elif var.find("btree") == 0:
                if not similar:
                    print "Please run 'suggest' command to build the tree"
                else:
                    build_tree()
            elif var.find("broader") == 0:
                if not btree:
                    print "Please run 'suggest' command to build the tree"
                else:
                    var = raw_input("How many levels up, sir? ")
                    if var.isdigit():
                        btree.broader(int(var))
                    else:
                        print "Wrong argument, srrrr"
            elif var.find("narrower") == 0:
                if not btree:
                    print "Please run 'suggest' command to build the tree"
                else:
                    var = raw_input("How many levels deep, sir? ")
                    if var.isdigit():
                        btree.narrower(int(var))
                    else:
                        print "Wrong argument, srrr"
            elif var.find("reindex") == 0:
                worker.reindex(_dict['index'], _dict['glob'])
                worker.close()
                worker = LuceneWhisperer()
                worker.open(_dict['index'])
            elif var == "quit":
                break
            else:
                print_help()



if __name__ == "__main__":
    #testtree()
    #test()
    console_app()

