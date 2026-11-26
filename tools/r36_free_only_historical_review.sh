#!/usr/bin/env bash
set -euo pipefail
umask 077
export GIT_TERMINAL_PROMPT=0 PYTHONDONTWRITEBYTECODE=1

if [[ $# -ne 1 || ! ${1:-} =~ ^[0-9a-f]{40}$ ]]; then
    echo "Usage: $0 <trusted-review-commit-sha>" >&2
    exit 2
fi
audit_commit=$1
python3.12 -c 'import sqlite3, sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Python 3.12 is required")'
timeout --version >/dev/null

work=$(mktemp -d)
work=$(cd "$work" && pwd -P)
echo "Private local evidence directory: $work"
cd "$work"

git init -q repo
git -C repo remote add origin https://github.com/LucasRodrigues013/cronicas.git
git -C repo fetch --no-tags origin "$audit_commit"
test "$(git -C repo rev-parse "$audit_commit^{commit}")" = "$audit_commit"
git -C repo worktree add --detach "$work/audit" "$audit_commit"

request=editorial/codex-staging/r36-native-review-request.json
pins=$(python3.12 - "$work/audit/$request" <<'PY'
import json
import re
import sys
from pathlib import Path

request = json.loads(Path(sys.argv[1]).read_bytes())
if (request.get("schema") != "worldroot-r36-native-review-request-v1"
        or request.get("mode") != "READ_ONLY_CANDIDATE"
        or request.get("production_hold") is not True):
    sys.exit("Invalid native review request or missing production hold")
pins = [request.get(key) for key in ("engine", "archive", "checkpoint")]
if not all(isinstance(pin, str) and re.fullmatch(r"[0-9a-f]{40}", pin) for pin in pins):
    sys.exit("Engine, archive and checkpoint must be pinned to full commit SHAs")
print(*pins)
PY
)
read -r engine_commit archive_commit checkpoint_commit <<< "$pins"
git -C repo fetch --no-tags origin "$engine_commit" "$archive_commit" "$checkpoint_commit"
for pin in "$engine_commit" "$archive_commit" "$checkpoint_commit"; do
    test "$(git -C repo rev-parse "$pin^{commit}")" = "$pin"
done
git -C repo worktree add --detach "$work/engine" "$engine_commit"
git -C repo worktree add --detach "$work/archive" "$archive_commit"
git -C repo worktree add --detach "$work/checkpoint" "$checkpoint_commit"

PYTHONPATH="$work/engine" python3.12 "$work/audit/tools/r36_incremental_historical_review.py" \
    "$work/audit" "$work/archive" "$work/engine" "$work/checkpoint" "$work/candidate" 2>&1 | tee native.log
(
    cd "$work/engine"
    timeout --signal=TERM --kill-after=5s 120s python3.12 -u -m unittest discover -s tests -v
) 2>&1 | tee regression.log

for checkout in audit archive engine checkpoint; do
    status=$(git -C "$checkout" status --porcelain --untracked-files=all)
    if [[ -n $status ]]; then
        echo "Checkout changed: $checkout" >&2
        exit 1
    fi
done
test -s candidate/native-receipt.json
test -s candidate/review-evidence.json

python3.12 - "$audit_commit" "$engine_commit" "$archive_commit" "$checkpoint_commit" "$request" <<'PY'
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path, PurePosixPath

audit_commit, engine_commit, archive_commit, checkpoint_commit, request = sys.argv[1:]
pins = dict(audit=audit_commit, engine=engine_commit, archive=archive_commit, checkpoint=checkpoint_commit)
for name, pin in pins.items():
    if subprocess.check_output(["git", "-C", name, "rev-parse", "HEAD"], text=True).strip() != pin:
        sys.exit(f"Unexpected checkout HEAD: {name}")
native_path = Path("candidate/native-receipt.json")
native = json.loads(native_path.read_bytes())
if (native.get("status") != "NATIVE_CANDIDATE_VALIDATED_NOT_APPROVED"
        or native.get("approval_required") is not True
        or native.get("replay_restore") is not True
        or native.get("production_activated") is not False
        or native.get("canon_changed") is not False
        or any(native.get(key) != pins[name] for key, name in (
            ("engine", "engine"), ("base_archive", "archive"), ("base_checkpoint", "checkpoint")))):
    sys.exit("Unexpected native receipt or candidate state")

evidence_paths = [Path("audit") / request, Path("native.log"), Path("regression.log"),
                  native_path, Path("candidate/review-evidence.json")]
blobs = native["candidate_blobs"]
if len(blobs) != 4:
    sys.exit("Expected four registry blobs")
for original, expected in blobs.items():
    registry_path = PurePosixPath(original)
    if registry_path.parent != PurePosixPath("editorial/registries"):
        sys.exit(f"Unexpected registry path: {original}")
    local_path = Path("candidate/registries") / registry_path.name
    actual = subprocess.check_output(["git", "-C", "repo", "hash-object", "--no-filters",
                                      str(local_path.resolve())], text=True).strip()
    if actual != expected:
        sys.exit(f"Candidate blob mismatch: {original}")
    evidence_paths.append(local_path)

summary = re.search(r"^Ran (\d+) tests? in ([\d.]+)s$", Path("regression.log").read_text(), re.MULTILINE)
if not summary or not int(summary[1]):
    sys.exit("Missing regression test count")
integrity = Path("integrity-receipt.json")
integrity.write_text(json.dumps({
    "worktrees": {name: {"head": pin, "clean": True} for name, pin in pins.items()},
    "python": sys.version.split()[0],
    "sqlite": sqlite3.sqlite_version,
    "native": "PASS",
    "regression": {"status": "PASS", "tests": int(summary[1]), "seconds": float(summary[2])},
    "verified_candidate_blobs": blobs,
    "approval_required": True,
    "production_hold": True,
}, indent=2) + "\n", encoding="utf-8")
evidence_paths.append(integrity)
Path("SHA256SUMS").write_text("".join(
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.as_posix()}\n"
    for path in sorted(evidence_paths)
), encoding="utf-8")
PY
sha256sum --strict --check SHA256SUMS
echo "Native review and full regression passed. Candidate and receipts retained at $work"
