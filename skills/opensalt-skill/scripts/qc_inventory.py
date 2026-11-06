#!/usr/bin/env python3
"""Inventory report for a CASE 1.1 package — the mechanical half of a QC pass.

Usage:
    python3 qc_inventory.py PACKAGE.json

Reports shape and content statistics that validate_case_package.py cannot judge:
item counts by type, tree depth, roots/orphans/multi-parent items, childless
grouping nodes, duplicate statements and coding schemes, field coverage, and
definition usage. Read the report end to end; findings feed the QC report.

This is a report, not a gate: it always exits 0 (2 on unreadable input).
Pair it with validate_case_package.py, which is the gate.
"""

import argparse
import collections
import json
import sys


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, dict):
        print("error: package root must be a JSON object", file=sys.stderr)
        sys.exit(2)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("package", help="path to the CFPackage JSON file")
    args = ap.parse_args()
    data = load(args.package)

    doc = data.get("CFDocument") or {}
    items = [i for i in (data.get("CFItems") or []) if isinstance(i, dict)]
    by_id = {i.get("identifier"): i for i in items if i.get("identifier")}
    assoc = [a for a in (data.get("CFAssociations") or []) if isinstance(a, dict)]

    doc_id = doc.get("identifier")
    parent = {}   # item -> destination(s) of its isChildOf
    for a in assoc:
        if a.get("associationType") == "isChildOf":
            origin = (a.get("originNodeURI") or {}).get("identifier")
            dest = (a.get("destinationNodeURI") or {}).get("identifier")
            if origin:
                parent.setdefault(origin, []).append(dest)

    def depth(iid):
        d, seen = 0, {iid}
        cur = iid
        while cur in parent and parent[cur][0] not in seen:
            cur = parent[cur][0]
            seen.add(cur)
            d += 1
        return d

    children = collections.Counter()
    for dests in parent.values():
        for dest in dests:
            children[dest] += 1

    print("--- document ---")
    print(f"title: {doc.get('title')!r}  creator: {doc.get('creator')!r}  "
          f"version: {doc.get('version')!r}  status: {doc.get('adoptionStatus')!r}  "
          f"language: {doc.get('language')!r}")
    print(f"notes present: {bool(doc.get('notes'))}  "
          f"description present: {bool(doc.get('description'))}")

    print("\n--- shape ---")
    types = collections.Counter(i.get("CFItemType", "(no type)") for i in items)
    print(f"items: {len(items)}  by type: {dict(types.most_common())}")
    print(f"associations: {len(assoc)}  "
          f"by type: {dict(collections.Counter(a.get('associationType', '?') for a in assoc).most_common())}")
    depths = collections.Counter(depth(i["identifier"]) for i in items if i.get("identifier"))
    print(f"depth histogram: {dict(sorted(depths.items()))}")

    def is_top(iid):
        ps = parent.get(iid)
        return not ps or (doc_id and doc_id in ps)

    roots = [i for i in items if is_top(i.get("identifier"))]
    multi = [i for i in items if len(parent.get(i.get("identifier"), [])) > 1]
    print(f"top-level (no isChildOf, or parent = document): {len(roots)}  "
          f"multi-parent: {len(multi)}")
    if multi[:5]:
        for i in multi[:5]:
            print(f"  multi-parent: {i.get('humanCodingScheme') or i.get('identifier')} "
                  f"({len(parent[i['identifier']])} parents)")

    childless = collections.Counter(
        i.get("CFItemType", "(no type)") for i in items if children.get(i.get("identifier"), 0) == 0)
    print(f"childless items by type: {dict(childless.most_common())}")

    print("\n--- duplicates ---")
    stmts = collections.defaultdict(list)
    for n, i in enumerate(items):
        if i.get("fullStatement"):
            stmts[i["fullStatement"]].append(n)
    dup_stmts = {k: v for k, v in stmts.items() if len(v) > 1}
    print(f"duplicate fullStatement values: {len(dup_stmts)}")
    for k, v in list(dup_stmts.items())[:5]:
        print(f"  CFItems{v}: {k[:80]!r}")
    schemes = collections.defaultdict(list)
    for n, i in enumerate(items):
        if i.get("humanCodingScheme"):
            schemes[i["humanCodingScheme"]].append(n)
    dup_schemes = {k: v for k, v in schemes.items() if len(v) > 1}
    print(f"duplicate humanCodingScheme values: {len(dup_schemes)}")
    for k, v in list(dup_schemes.items())[:5]:
        print(f"  CFItems{v}: {k!r}")

    print("\n--- field coverage (of", len(items), "items) ---")
    fields = ["humanCodingScheme", "abbreviatedStatement", "educationLevel",
              "subject", "subjectURI", "conceptKeywords", "notes", "extensions"]
    for f in fields:
        n = sum(1 for i in items if i.get(f))
        print(f"  {f}: {n} ({100 * n // len(items)}%)" if items else f"  {f}: 0")

    print("\n--- definitions usage ---")
    defs = data.get("CFDefinitions") or {}
    declared_types = {t.get("title") for t in (defs.get("CFItemTypes") or []) if isinstance(t, dict)}
    used_types = set(types) - {"(no type)"}
    print(f"CFItemTypes declared: {len(declared_types)}  used by items: {sorted(used_types)}")
    undeclared = used_types - declared_types
    if undeclared:
        print(f"  types used but NOT declared: {sorted(undeclared)}")
    unused = declared_types - used_types
    if unused:
        print(f"  types declared but never used: {sorted(unused)}")
    declared_subjects = {s.get("title") for s in (defs.get("CFSubjects") or []) if isinstance(s, dict)}
    n_subject_refs = sum(1 for i in items if i.get("subjectURI"))
    print(f"CFSubjects declared: {len(declared_subjects)} {sorted(declared_subjects)}  "
          f"items with subjectURI: {n_subject_refs}")

    print("\n--- identifier conventions ---")
    uris = collections.Counter()
    for i in items:
        u = i.get("uri") or ""
        if "/uri/" in u:
            uris["/uri/ space"] += 1
        elif "/ims/case/" in u:
            uris["CASE spec space"] += 1
        else:
            uris["other/unrecognized"] += 1
    print(f"item uri spaces: {dict(uris.most_common())} — one convention expected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
