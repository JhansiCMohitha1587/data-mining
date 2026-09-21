import csv
import glob
import re
import statistics
import hashlib

notices = {}

for fn in glob.glob("notices/*.csv"):
    with open(fn, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            notices[row["notice_id"]] = row

with open("labelled_pairs.csv", encoding="utf-8", newline="") as f:
    pairs = list(csv.DictReader(f))


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def word3(text):
    words = normalize(text).split()
    return set(
        " ".join(words[i:i+3])
        for i in range(len(words)-2)
    )


def exact_jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def minhash_signature(shingles, k):
    sig = []

    for seed in range(k):
        minimum = None

        for shingle in shingles:
            h = hashlib.blake2b(
                f"{seed}:{shingle}".encode(),
                digest_size=8
            ).digest()

            value = int.from_bytes(h, "big")

            if minimum is None or value < minimum:
                minimum = value

        sig.append(minimum)

    return sig


def minhash_similarity(sig_a, sig_b):
    return sum(
        x == y for x, y in zip(sig_a, sig_b)
    ) / len(sig_a)


shingles = {}

for nid, row in notices.items():
    shingles[nid] = word3(
        row["title"] + " " + row["body"]
    )


sizes = [64, 128, 256, 512]

for k in sizes:

    errors = []
    failures = 0

    for p in pairs:

        try:
            a = shingles[p["notice_id_a"]]
            b = shingles[p["notice_id_b"]]

            exact = exact_jaccard(a, b)

            sig_a = minhash_signature(a, k)
            sig_b = minhash_signature(b, k)

            estimated = minhash_similarity(sig_a, sig_b)

            errors.append(abs(exact - estimated))

        except Exception:
            failures += 1

    errors.sort()

    mean_error = statistics.mean(errors)
    median_error = statistics.median(errors)
    p95 = errors[int(0.95 * len(errors)) - 1]
    maximum = max(errors)

    print()
    print("==============================")
    print("MinHash size:", k)
    print("==============================")
    print("Pairs tested :", len(errors))
    print("Failures     :", failures)
    print("Mean error   :", round(mean_error, 5))
    print("Median error :", round(median_error, 5))
    print("95% error    :", round(p95, 5))
    print("Maximum error:", round(maximum, 5))