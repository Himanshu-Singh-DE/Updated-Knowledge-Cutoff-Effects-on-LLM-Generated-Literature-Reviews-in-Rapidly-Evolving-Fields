#!/usr/bin/env bash
# Clone the ACL Anthology metadata and the 34 curated lists at the pinned commits.
# Usage: bash scripts/fetch_data.sh [DEST]   (default DEST=../data_raw)
set -euo pipefail
DEST=${1:-../data_raw}
mkdir -p "$DEST/lists"
python3 - "$DEST" <<'PY'
import json, subprocess, sys, os
dest = sys.argv[1]
cfg = json.load(open("configs/lists.json"))
def get(repo, commit, path, sparse=None):
    if not os.path.isdir(path):
        args = ["git", "clone", "-q", "--filter=blob:none"] + (["--sparse"] if sparse else []) + [repo, path]
        subprocess.run(args, check=True)
    if sparse:
        subprocess.run(["git", "-C", path, "sparse-checkout", "set", sparse], check=True)
    subprocess.run(["git", "-C", path, "checkout", "-q", commit], check=True)
    print("ok", repo, commit[:10])
a = cfg["anthology"]
get(a["repo"], a["commit"], os.path.join(dest, "acl"), sparse=a["path"])
for l in cfg["lists"]:
    get(l["repo"], l["commit"], os.path.join(dest, "lists", l["dir"]))
PY
