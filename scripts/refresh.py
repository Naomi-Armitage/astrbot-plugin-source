"""Refresh `version` field for each plugin from its repo's metadata.yaml,
then rewrite plugins.json (sorted) and recompute plugins-md5.json.

Run from repo root. Designed to be idempotent: if nothing changed, the
files are byte-for-byte identical so the workflow's git-diff check
short-circuits the commit.

External deps: stdlib only — uses urllib + a tiny YAML subset extractor
(only needs the `version:` line) to avoid pulling PyYAML.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_JSON = ROOT / "plugins.json"
MD5_JSON = ROOT / "plugins-md5.json"

# Branches to try in order; metadata.yaml lives at repo root.
BRANCHES = ("main", "master")
RAW = "https://raw.githubusercontent.com/{owner}/{name}/{branch}/metadata.yaml"
TIMEOUT = 15

VERSION_RE = re.compile(r"^\s*version\s*:\s*['\"]?([^\s'\"#]+)", re.MULTILINE)


def _parse_repo(url: str) -> tuple[str, str] | None:
    """Pull (owner, name) out of a github.com URL. Tolerates trailing
    .git, #anchor, /tree/branch, and a stray '#' the official registry
    sometimes appends."""
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    if not m:
        return None
    owner, name = m.group(1), m.group(2)
    name = name.removesuffix(".git")
    return owner, name


def _fetch(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "astrbot-plugin-source-refresh"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def fetch_version(repo_url: str) -> str | None:
    parsed = _parse_repo(repo_url)
    if not parsed:
        return None
    owner, name = parsed
    for branch in BRANCHES:
        body = _fetch(RAW.format(owner=owner, name=name, branch=branch))
        if not body:
            continue
        m = VERSION_RE.search(body)
        if m:
            return m.group(1)
    return None


def main() -> int:
    data = json.loads(PLUGINS_JSON.read_text(encoding="utf-8"))
    changed = False
    for key, entry in data.items():
        repo = entry.get("repo", "")
        if not repo:
            print(f"skip {key}: no repo")
            continue
        v = fetch_version(repo)
        if not v:
            print(f"warn {key}: could not read metadata.yaml")
            continue
        if entry.get("version") != v:
            print(f"update {key}: {entry.get('version')!r} -> {v!r}")
            entry["version"] = v
            changed = True
        else:
            print(f"ok    {key}: {v}")

    # Re-serialize with stable key order so git diffs stay clean.
    serialized = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    PLUGINS_JSON.write_text(serialized, encoding="utf-8")
    md5 = hashlib.md5(serialized.encode("utf-8")).hexdigest()
    MD5_JSON.write_text(json.dumps({"md5": md5}) + "\n", encoding="utf-8")

    print(f"\nplugins.json md5: {md5}")
    print(f"changed: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
