#!/usr/bin/env python3
"""Pre-commit check: passport claim changes must carry recompute provenance.

Reads the STAGED version of each quality_reports/passports/*.yaml, compares it to HEAD,
and FAILS (exit 1) if any claim whose value/status/claim text changed has a
`last_verified_by` that does not name a recompute source. Text substitution can then no
longer masquerade as verification (origin: a batch-substituted passport in a production project left 5 wrong claim
texts marked PASS; the freshness requirement closes the stale-provenance hole found
while testing the gate itself).

Recompute provenance = last_verified_by matching (case-insensitive):
  recomput | audit-reproducibility | claim-verifier | verifier agent | scripts/

Exit 0 = clean or nothing staged; exit 1 = violation (block commit); any crash = exit 0
(fail-open, matching the quality gate's philosophy).
"""

import re
import subprocess
import sys

import yaml

PROVENANCE = re.compile(r"recomput|audit-reproducibility|claim-verifier|verifier agent|scripts/",
                        re.IGNORECASE)
FIELDS = ("claim", "status", "output_field", "notes")


def staged_passports() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                         capture_output=True, text=True).stdout.split()
    return [f for f in out if f.startswith("quality_reports/passports/") and f.endswith(".yaml")]


def load(rev: str, path: str) -> dict:
    if rev == ":staged":
        blob = subprocess.run(["git", "show", f":{path}"], capture_output=True, text=True).stdout
    else:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True).stdout
    return yaml.safe_load(blob) or {}


def main() -> int:
    bad = []
    for path in staged_passports():
        try:
            new = {c["id"]: c for c in load(":staged", path).get("claims", [])}
            old = {c["id"]: c for c in load("HEAD", path).get("claims", [])}
        except Exception:
            continue  # unparseable -> let the YAML validity die elsewhere
        for cid, c in new.items():
            o = old.get(cid)
            changed = o is None or any(str(c.get(f)) != str(o.get(f)) for f in FIELDS)
            if not changed:
                continue
            by_ok = bool(PROVENANCE.search(str(c.get("last_verified_by", ""))))
            # provenance must also be FRESH: a stale verifier string from an earlier
            # pass must not whitelist new value changes (hole found by the negative
            # test on 2026-08-03: a tampered claim passed because its untouched
            # last_verified_by still said "claim-verifier")
            fresh = o is None or (str(c.get("last_verified_on")) != str(o.get("last_verified_on"))
                                  or str(c.get("last_verified_by")) != str(o.get("last_verified_by")))
            if not (by_ok and fresh):
                why = "no recompute source" if not by_ok else "provenance not refreshed with the change"
                bad.append((path, cid, f"{why}; last_verified_by={str(c.get('last_verified_by',''))[:50]!r}"))
    if bad:
        print("✗ passport provenance check FAILED — changed claims lack a recompute source:",
              file=sys.stderr)
        for path, cid, why in bad:
            print(f"    {path} :: {cid}  {why}", file=sys.stderr)
        print("  A claim's value/status changes only via recomputation "
              "(.claude/rules/stop-and-ask.md trigger 6). Re-verify with "
              "/audit-reproducibility or the claim-verifier, record it in "
              "last_verified_by, then commit.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # fail-open like the quality gate
        print(f"⚠ passport provenance check crashed ({e}) — allowing commit (fail-open).",
              file=sys.stderr)
        sys.exit(0)
