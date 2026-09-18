from pathlib import Path
import re

import boto3
from botocore.client import Config

BASE = Path(__file__).resolve().parents[1]
SALES_DIR = BASE / "data" / "sales"

BUCKET = "annapurna"

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="admin12345",
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

pattern = re.compile(
    r"SALES_(S\d+)_(\d{8})(?:__R\d+)?\.(csv|parquet)$",
    re.IGNORECASE,
)

uploaded = 0
skipped = 0

for path in SALES_DIR.iterdir():
    if not path.is_file():
        continue

    match = pattern.match(path.name)

    if not match:
        print("SKIPPED:", path.name)
        skipped += 1
        continue

    store = match.group(1)
    date = match.group(2)

    year = date[:4]
    month = date[4:6]

    object_key = (
        f"raw/sales/"
        f"store={store}/"
        f"year={year}/"
        f"month={month}/"
        f"{path.name}"
    )

    print(f"Uploading {path.name} -> {object_key}")

    s3.upload_file(str(path), BUCKET, object_key)
    uploaded += 1

print("\n========== PART A: MINIO LANDING ==========")
print("Uploaded:", uploaded)
print("Skipped :", skipped)
print("============================================")
