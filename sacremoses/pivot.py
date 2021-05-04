
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
    # Iterate through the first lang pair, populate `hash_to_src_pivot1`.
    with open(src) as sfin, open(pivot1) as tfin:
        hash_to_src_pivot1 = {hash:(s.strip(), t.strip()) for s, t, hash
            in tqdm(zip(sfin, tfin, pivot1_hashes)) if hash in overlaps}
    # Iterate through the second lang pair, print aligned output to file.
    with open(pivot2) as sfin, open(trg) as tfin, open(outputfile, 'w') as fout:
        print('\t'.join(['hash', 'src', 'pivot', 'trg']), end='\n', file=fout)
        for s, t, hash in tqdm(zip(sfin, tfin, pivot2_hashes)):
            s, t = s.strip(), t.strip()
            if hash in overlaps:
                src, pivot1 = hash_to_src_pivot1[hash]
                if pivot1 == s:  # Check that there's no collison.
                    print('\t'.join([str(hash), src, s, t]), end='\n', file=fout)
