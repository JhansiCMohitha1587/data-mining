import csv
import glob
import re
from collections import Counter, defaultdict

DATA = "notices"
PAIRS = "labelled_pairs.csv"

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def word3(text):
    words = normalize(text).split()
    return set(tuple(words[i:i+3]) for i in range(len(words)-2))

# Load notices
notices = {}

for f in glob.glob(DATA + "/*.csv"):
    with open(f, encoding="utf-8-sig", errors="ignore") as fh:
        for row in csv.DictReader(fh):
            notices[row["notice_id"]] = (
                row.get("title", "") + " " + row.get("body", "")
            )

print("Notices loaded:", len(notices))

# Build shingles
shingles = {}
df = Counter()

for nid, text in notices.items():
    s = word3(text)
    shingles[nid] = s
    for x in s:
        df[x] += 1

# Ignore very common shingles.
# They generate huge posting lists and are mostly boilerplate.
MAX_DF = 10

index = defaultdict(set)

for nid, ss in shingles.items():
    rare = [x for x in ss if df[x] <= MAX_DF]

    # Keep the 64 rarest shingles for the candidate lookup.
    rare.sort(key=lambda x: df[x])

    for x in rare[:64]:
        index[x].add(nid)

print("Indexed rare shingles:", len(index))

# Load labelled pairs
pairs = []

with open(PAIRS, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        pairs.append(row)

# Candidate function
def candidates(nid):
    result = set()

    for x in shingles[nid]:
        if df[x] <= MAX_DF:
            result.update(index.get(x, set()))

    result.discard(nid)
    return result

# Exact Jaccard
def jaccard(a, b):
    A = shingles[a]
    B = shingles[b]

    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0

    return len(A & B) / len(A | B)

# Measure labelled-pair survival
survived = 0
same_total = 0

bins = defaultdict(lambda: [0, 0])

for p in pairs:
    a = p["notice_id_a"]
    b = p["notice_id_b"]

    if a not in shingles or b not in shingles:
        continue

    sim = jaccard(a, b)
    c = candidates(a)

    survived_pair = b in c

    if p["label"].lower() == "same":
        same_total += 1
        if survived_pair:
            survived += 1

    bin_start = int(sim * 10) / 10
    bins[bin_start][1] += 1

    if survived_pair:
        bins[bin_start][0] += 1

print()
print("======================================")
print("CANDIDATE RETRIEVAL RESULTS")
print("======================================")
print("Labelled pairs tested:", len(pairs))
print("Same pairs:", same_total)
print("Same pairs surviving:", survived)
print("Recall / survival:", round(survived / same_total, 4))

print()
print("True similarity   Survival probability")
print("--------------------------------------")

for b in sorted(bins):
    survived_b, total_b = bins[b]
    print(
        f"{b:.1f}-{b+0.1:.1f}             "
        f"{survived_b}/{total_b} = "
        f"{survived_b/total_b:.4f}"
    )

# Candidate workload over complete corpus
counts = []

for i, nid in enumerate(shingles):
    counts.append(len(candidates(nid)))

print()
print("======================================")
print("FULL CORPUS CANDIDATE WORK")
print("======================================")
print("Total candidate references:", sum(counts))
print("Mean candidates/notice:", round(sum(counts)/len(counts), 2))

s = sorted(counts)

def percentile(values, p):
    k = int((len(values)-1) * p)
    return values[k]

print("Median:", percentile(s, 0.50))
print("P95:", percentile(s, 0.95))
print("P99:", percentile(s, 0.99))
print("Maximum:", max(s))

# Candidate pairs
unique_pairs = set()

for a in shingles:
    for b in candidates(a):
        pair = tuple(sorted((a, b)))
        unique_pairs.add(pair)

print("Unique candidate pairs:", len(unique_pairs))
print("All-pairs comparisons:", len(shingles)*(len(shingles)-1)//2)

with open("shingle_index.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["shingle", "notice_id"])

    for nid, ss in shingles.items():
        rare = [x for x in ss if df[x] <= MAX_DF]
        rare.sort(key=lambda x: df[x])

        for x in rare[:64]:
            w.writerow([" ".join(x), nid])

print("shingle_index.csv created")