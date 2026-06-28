#!/usr/bin/env python3
"""
snapshot_lock.py - guards the known-good Christa Dalmazio site.

This protects the launch-ready version so future edits (in any session) can be
checked and rolled back to an exact, byte-for-byte copy.

  python3 snapshot_lock.py save      record SHA256 of every site file -> .site_lock.json
  python3 snapshot_lock.py verify     compare current files to the lock; report any drift
  python3 snapshot_lock.py restore    restore the exact locked files from the git tag

The restore point is the immutable git tag below. A git tag cannot be overwritten
by a normal push, so the locked version is always recoverable from GitHub.
"""
import hashlib, json, os, subprocess, sys, datetime

TAG  = "v1.0-pre-cms-snapshot"
LOCK = ".site_lock.json"
SKIP_DIRS  = {".git", "__pycache__"}
SKIP_FILES = {LOCK, "snapshot_lock.py"}   # watch the SITE, not the tooling


def site_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    files = []
    for f in out.splitlines():
        if f in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in f.split("/")):
            continue
        if os.path.exists(f):
            files.append(f)
    return sorted(files)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def head_commit():
    return subprocess.run(["git", "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def save():
    files = site_files()
    data = {
        "tag": TAG,
        "commit": head_commit(),
        "saved_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "file_count": len(files),
        "files": {f: sha(f) for f in files},
    }
    json.dump(data, open(LOCK, "w"), indent=2, sort_keys=True)
    print(f"Locked {len(files)} site files -> {LOCK}")
    print(f"  tag:    {TAG}")
    print(f"  commit: {data['commit'][:10]}")
    return 0


def verify():
    if not os.path.exists(LOCK):
        print(f"No {LOCK} found. Run: python3 snapshot_lock.py save")
        return 2
    data = json.load(open(LOCK))
    locked = data["files"]
    current = {f: sha(f) for f in site_files()}
    changed = [f for f in locked if f in current and current[f] != locked[f]]
    missing = [f for f in locked if f not in current]
    added   = [f for f in current if f not in locked]
    if not (changed or missing or added):
        print(f"OK - all {len(locked)} site files match the locked snapshot "
              f"(saved {data['saved_utc']}).")
        return 0
    print("DRIFT DETECTED vs the locked snapshot:")
    for f in changed: print("  CHANGED ", f)
    for f in missing: print("  MISSING ", f)
    for f in added:   print("  ADDED   ", f)
    print("\nTo restore the locked version exactly:  python3 snapshot_lock.py restore")
    return 1


def restore():
    subprocess.run(["git", "fetch", "--tags", "-q"])
    r = subprocess.run(["git", "checkout", TAG, "--", "."])
    if r.returncode != 0:
        print("Restore failed. Confirm the tag exists with: git tag -l")
        return 1
    print(f"Restored all files from tag {TAG}.")
    print("Files added AFTER the snapshot are left in place; review 'git status',")
    print("then commit if you want the restored version on this branch.")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    fn = {"save": save, "verify": verify, "restore": restore}.get(cmd)
    if not fn:
        print("usage: python3 snapshot_lock.py [save|verify|restore]")
        sys.exit(2)
    sys.exit(fn())
