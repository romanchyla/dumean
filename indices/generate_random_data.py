
import sys
import string
import random
from dumean.libs import optionparse



def run(output_file,
        max=600000,
        min_len=3,
        max_len=12,
        groups=None):
    '''
Program to generate dictionary of random tokens (both single as well as coumpounds)
To be used for indexing.

Example: %prog
         %prog demo #will start demo with default arguments

usage: %prog output_file [options]
    -m, --max= MAX: how many rows to generate
    -i, --min_len = MINL: minimum length of the generated entries
    -l, --max_len = MAXL: maximum length of the generated entries
    -g, --groups = G: comma separated list of integerers which says how many tokens to generate for each group [1:50,2:50]
    '''

    fo = open(output_file, 'w')

    max,max_len,min_len = int(max),int(max_len),int(min_len)
    groups = [map(int, x.split(':')) for x in groups]

    i = 0

    for token_len, token_max in groups:
        ii = 0
        while i < max and ii<token_max:
            fo.write(make_one(token_len, min_len, max_len))
            i += 1
            ii += 1

    while i < max:
        fo.write(make_one(1, min_len, max_len))
        i += 1

    fo.close()
    
    print 'Generated: %s [length=%s]' % (output_file, max)

def make_one(len, minl, maxl):
    this_len = random.choice(range(minl+1, maxl))

    if len == 1:
        x = "".join([random.choice(string.letters+string.digits) for x in range(1, this_len)])
    else:
        x = ' '.join(["".join([random.choice(string.letters+string.digits) for x in range(1, this_len)]) for x in range(len)])
    return 'hqs %s= %s\n' % (x, 0)

def main():
    options, args=optionparse.parse(run.__doc__)
    if (not len(args) or not options): optionparse.exit()
    run(args[0], **options.__dict__)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        sys.argv[1:] = ('random.seman -m 600000 -l 12 -i 3 -g2:500000,3:500000').split()
    main()