
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

def pivot_bitext(src, pivot1, pivot2, trg):
    # Run the hash on the files.
    with open(pivot1) as fin:
        pivot1_hashes = [xxh64(line) for line in tqdm(fin)]
        pivot2_hashes = [xxh64(line) for line in tqdm(fin)]
    # Find the overlaps.
    overlaps = set(pivot1_hashes).intersection(pivot2_hashes)
    # Dictionary to keep the pivoted result.
    data = defaultdict(lambda: defaultdict(set))
    # Iterate through the first lang pair, populate `data`.
    with open(src) as sfin, open(pivot1) as tfin:
        for s, t, hash in tqdm(zip(sfin, tfin, pivot1_hashes)):
            if hash in overlaps:
                data[t]['p1'].add(s)
    # Iterate through the second lang pair, populate `data`.
    with open(pivot1) as sfin, open(trg) as tfin:
        for s, t, hash in tqdm(zip(sfin, tfin, pivot2_hashes)):
            if hash in overlaps:
                data[s]['p2'].add(s)
