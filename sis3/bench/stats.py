import glob, sys, json
label = sys.argv[1]
names = {"read": ["list", "overdue", "tag", "report"], "write": ["insert", "update"]}
def pct(a, p):
    k = (len(a) - 1) * p / 100.0
    f = int(k); c = min(f + 1, len(a) - 1)
    return a[f] + (a[c] - a[f]) * (k - f)
out = {}
for kind in ("read", "write"):
    lat = []; per = {}; tmin = None; tmax = None
    for fn in glob.glob(f"results/{label}_{kind}.[0-9]*"):
        for line in open(fn):
            p = line.split()
            ms = float(p[2]) / 1000.0
            lat.append(ms); per.setdefault(int(p[3]), []).append(ms)
            t = int(p[4]); tmin = t if tmin is None else min(tmin, t); tmax = t if tmax is None else max(tmax, t)
    lat.sort()
    dur = max(tmax - tmin, 1)
    r = {"n": len(lat), "tps": round(len(lat) / dur, 1), "mean": round(sum(lat) / len(lat), 2),
         "p50": round(pct(lat, 50), 2), "p95": round(pct(lat, 95), 2), "p99": round(pct(lat, 99), 2), "per_query": {}}
    for s, a in per.items():
        a.sort(); r["per_query"][names[kind][s]] = {"n": len(a), "p50": round(pct(a, 50), 2), "p95": round(pct(a, 95), 2), "p99": round(pct(a, 99), 2)}
    out[kind] = r
json.dump(out, open(f"results/{label}.json", "w"), indent=1)
for k in out:
    r = out[k]; print(f"[{label}] {k:5s} tps={r['tps']:8} mean={r['mean']:8} p50={r['p50']:8} p95={r['p95']:8} p99={r['p99']:8} ms (n={r['n']})")
