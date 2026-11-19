import ast, hashlib, os, sys, time, re, statistics
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bench

NAME = re.compile(r"(id|attr|arg)='[^']*'|value=[^,)]+")
def fast_norm(node):
    return hashlib.blake2b(NAME.sub("_", ast.dump(node)).encode(), digest_size=8).digest()

def fast_file(p):
    src = open(p, encoding="utf-8", errors="replace").read()
    bench.norm = fast_norm
    return bench.analyse_file(p, src)

def parse_only(p):
    return ast.parse(open(p, encoding="utf-8", errors="replace").read())

def t(fn):
    ts=[]
    for _ in range(3):
        s=time.perf_counter(); fn(); ts.append(time.perf_counter()-s)
    return statistics.median(ts)*1000

paths = bench.discover(sys.argv[2:])
print(f"## {sys.argv[1]} ({len(paths)} files)")
print(f"read+parse only:            {t(lambda: [parse_only(p) for p in paths]):9.0f} ms")
print(f"read+parse+checks, 1-pass:  {t(lambda: [fast_file(p) for p in paths]):9.0f} ms")
with ProcessPoolExecutor(8) as ex:
    list(ex.map(fast_file, paths[:8]))
    print(f"same, 8 processes (warm):   {t(lambda: list(ex.map(fast_file, paths, chunksize=8))):9.0f} ms")
