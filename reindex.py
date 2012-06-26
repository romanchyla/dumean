from dumean import whisperer
import sys
import os
import time

if __name__ == "__main__":
    if len(sys.argv) > 1:
        what = sys.argv[1]
    else:
        print "usage %s [hepnet|wordnet|authors|random]" % sys.argv[0]
        sys.exit(0)

    _d = os.path.dirname(__file__)
    worker = whisperer.LuceneWhisperer()

    print 'Building the index: ' + what
    start = time.time()
    if what == 'hepnet':
        worker.open(os.path.join(_d, 'indices/hepnet'),
                    reindex=os.path.join(_d, 'indices/hep.seman'))
    elif what == 'wordnet':
        worker.open(os.path.join(_d, 'indices/wordnet'),
                    reindex=os.path.join(_d, 'indices/wordnet.seman'))
    elif what == 'authors':
        worker.open(os.path.join(_d, 'indices/authors'),
                    reindex=os.path.join(_d, 'indices/names.seman'))
    elif what == 'random':
        worker.open(os.path.join(_d, 'indices/random'),
                    reindex=os.path.join(_d, 'indices/random.seman'))
    elif what == 'all':
        worker.open(os.path.join(_d, 'indices/hepnet'),
                    reindex=os.path.join(_d, 'indices/hep.seman'))
        worker.close()
        worker.open(os.path.join(_d, 'indices/wordnet'),
                    reindex=os.path.join(_d, 'indices/wordnet.seman'))
        worker.close()
        worker.open(os.path.join(_d, 'indices/authors'),
                    reindex=os.path.join(_d, 'indices/names.seman'))
        worker.close()
        os.system('%s indices/generate_random_data.py demo' % sys.executable)
        os.rename('random.seman', 'indices/random.seman')
        worker.open(os.path.join(_d, 'indices/random'),
                    reindex=os.path.join(_d, 'indices/random.seman'))
    else:
        print 'Unknown index: ' + what
    worker.close()
    print 'Finished in: %.3f s' % (time.time()-start,)