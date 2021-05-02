
import xxhash
from tqdm import tqdm
from collections import defaultdict

def xxh64(s, seed=42, digest='int'):
    if digest == 'int':
        return xxhash.xxh64(s, seed=seed).intdigest()
    elif digest == 'hex':
        return xxhash.xxh64(s, seed=seed).hexdigest()
    else:
        return xxhash.xxh64(s, seed=seed)

def pivot_bitext(src, pivot1, pivot2, trg, outputfile='pivoted.tsv'):
    # Run the hash on the files.
    with open(pivot1) as fin:
        pivot1_hashes = [xxh64(line) for line in tqdm(fin)]
    with open(pivot2) as fin:
        pivot2_hashes = [xxh64(line) for line in tqdm(fin)]
    # Find the overlaps.
    overlaps = set(pivot1_hashes).intersection(pivot2_hashes)
    # Keep tracks on one src_pivot1.
    hash2src = {}
    hash2pivot1 = {}
    # Iterate through the first lang pair, populate `data`.
    with open(src) as sfin, open(pivot1) as tfin, open('src_pivot1.tsv', 'w') as fout:
        print('\t'.join(['hash', 'src', 'pivot1']), end='\n', file=fout)
        for s, t, hash in tqdm(zip(sfin, tfin, pivot1_hashes)):
            if hash in overlaps:
                hash2src[hash] = s.strip()
                hash2pivot1[hash] = t.strip()
                print('\t'.join([hash, s.strip(), t.strip()]), end='\n', file=fout)
    # Iterate through the second lang pair, populate `data`.
    with open(pivot2) as sfin, open(trg) as tfin, \
    open('pivot2_trg.tsv', 'w') as fout, open(outputfile, 'w') as fout_pivot:
        print('\t'.join(['hash', 'pivot2', 'trg']), end='\n', file=fout)
        print('\t'.join(['hash', 'src', 'pivot', 'trg']), end='\n', file=fout)
        for s, t, hash in tqdm(zip(sfin, tfin, pivot2_hashes)):
            if hash in overlaps and hash2src[hash] == pivot2:
                print('\t'.join([hash, s.strip(), t.strip()]), end='\n', file=fout)
                print('\t'.join([hash, hash2pivot1[hash], s.strip(), t.strip()]), end='\n', file=fout_pivot)
