#!/usr/bin/env python3
"""Validate a CASE 1.1 JSON package (CFPackage) for OpenSALT import.

Usage:
    python3 validate_case_package.py PACKAGE.json [--strict] [--summary]

Exit codes:
    0  no errors (warnings are allowed unless --strict)
    1  validation errors found
    2  input could not be read or parsed

Checks performed:
  - required fields on every object type
  - lowercase UUID identifiers (8-4-4-4-12 hex)
  - URI construction: https://{host}/ims/case/v1p1/{ObjectType}/{identifier}
  - ISO 8601 lastChangeDateTime with timezone; YYYY-MM-DD status dates
  - LinkURI (title/identifier/uri) and LinkGenURI (+targetType) shape
  - associationType is a base type or ext: extension
  - referential integrity of association endpoints (dangling internal refs)
  - globally unique identifiers across the whole package
  - salt:type item kinds, incl. `ob3` credential payload parsing
  - CFItemType label-only usage (item type not declared / not referenced)
  - humanCodingScheme quality (duplicates, whitespace, machine-ID-shaped values)
  - adoptionStatus values (warns on non-recommended or legacy spellings)
  - rubric criterion/level structure

Messages use the location of the problem, e.g. `CFItems[3].identifier`.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from urllib.parse import urlsplit

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXT_ASSOC_RE = re.compile(r"^ext:[a-zA-Z0-9._-]+$")
CASE_URI_RE = re.compile(r"/ims/case/v1p1/([A-Za-z]+)/([^/]+)$")
MACHINE_ID_SCHEME_RE = re.compile(r"^[a-z]{1,6}_[0-9A-Za-z_-]{6,}$")

SALT_KINDS = {"job", "course", "assessment", "credential",
              "organization", "identifier", "public_key"}
ASSOC_TYPES = {"isChildOf", "exactMatchOf", "isRelatedTo", "isPartOf",
               "replacedBy", "precedes", "hasSkillLevel", "isPeerOf",
               "exemplar", "isTranslationOf"}
RECOMMENDED_ADOPTION = {"Draft", "Pending Implementation", "Implemented", "Retired", "Private Draft"}
LEGACY_ADOPTION = {"Adopted", "Deprecated"}  # CASE 1.0 spellings, still accepted
RECOGNIZED_ADOPTION = {v.lower(): v for v in RECOMMENDED_ADOPTION | LEGACY_ADOPTION}
LEGACY_SUCCESSOR = {"Adopted": "Implemented", "Deprecated": "Retired"}
URI_SEGMENTS = {"CFDocuments", "CFItems", "CFAssociations", "CFSubjects",
                "CFLicenses", "CFItemTypes", "CFConcepts",
                "CFAssociationGroupings", "CFRubrics", "CFRubricCriteria",
                "CFRubricCriterionLevels", "CFPackages"}
NO_NETLOC_SCHEMES = {"local", "urn", "mailto", "tag"}

errors = []
warnings = []


def err(loc, msg):
    errors.append(f"[ERROR] {loc}: {msg}")


def warn(loc, msg):
    warnings.append(f"[WARN]  {loc}: {msg}")


def is_uuid(v):
    return isinstance(v, str) and bool(UUID_RE.match(v))


def is_datetime(v):
    """ISO 8601 datetime with an explicit timezone offset."""
    if not isinstance(v, str) or not v:
        return False
    s = v.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return False
    return dt.tzinfo is not None


def is_date(v):
    if not isinstance(v, str) or not DATE_RE.match(v):
        return False
    try:
        date.fromisoformat(v)
        return True
    except ValueError:
        return False


def is_uri(v):
    if not isinstance(v, str) or not v:
        return False
    try:
        parts = urlsplit(v)
    except ValueError:
        return False
    if not parts.scheme:
        return False
    return bool(parts.netloc) or parts.scheme.lower() in NO_NETLOC_SCHEMES


def is_str_or_str_array(v):
    return isinstance(v, str) or (isinstance(v, list) and v
                                  and all(isinstance(x, str) for x in v))


def check_uri_shape(obj, field, expected_segment, loc):
    """URI must be valid; if it follows the CASE pattern, segment and
    identifier suffix must match the object. The server stores URIs as
    sent, so mismatches are warnings — but they break external consumers
    that dereference links, so they should be fixed in distributed packages."""
    uri = obj.get(field)
    if not is_uri(uri):
        err(f"{loc}.{field}", f"not a valid URI: {uri!r}")
        return
    m = CASE_URI_RE.search(urlsplit(uri).path)
    if not m:
        warn(f"{loc}.{field}", f"URI does not follow the CASE pattern "
                               f"https://{{host}}/ims/case/v1p1/{{ObjectType}}/{{identifier}}: {uri} "
                               f"(the URI is stored as sent, but following the pattern keeps external consumers working)")
        return
    segment, suffix = m.group(1), m.group(2)
    if segment not in URI_SEGMENTS:
        warn(f"{loc}.{field}", f"unknown ObjectType segment {segment!r} in {uri}")
    elif segment != expected_segment:
        warn(f"{loc}.{field}", f"URI segment {segment!r} does not match "
                               f"expected {expected_segment!r} in {uri}")
    if suffix != obj.get("identifier"):
        warn(f"{loc}.{field}", f"URI identifier suffix {suffix!r} does not match "
                               f"object identifier {obj.get('identifier')!r}")


def check_link(obj, field, loc, gen=False, required=False):
    """Validate a LinkURI (title/identifier/uri) or LinkGenURI (+targetType).
    Returns the link dict, or None."""
    link = obj.get(field)
    if link is None:
        if required:
            err(f"{loc}.{field}", f"required field is missing")
        return None
    if not isinstance(link, dict):
        err(f"{loc}.{field}", f"must be a LinkURI object, got {type(link).__name__}")
        return None
    ok = True
    for f in ("title", "identifier", "uri"):
        if not isinstance(link.get(f), str) or not link.get(f):
            err(f"{loc}.{field}.{f}", f"LinkURI {f} is required and must be a non-empty string")
            ok = False
    if "uri" in link and link.get("uri") and not is_uri(link.get("uri")):
        err(f"{loc}.{field}.uri", f"not a valid URI: {link.get('uri')!r}")
        ok = False
    ident = link.get("identifier")
    if isinstance(ident, str) and not is_uuid(ident):
        if gen and link.get("targetType") not in (None, "CASE"):
            pass  # ext targets may use non-UUID identifiers
        else:
            warn(f"{loc}.{field}.identifier",
                 f"expected a lowercase UUID for a CASE object reference: {ident!r}")
    if gen:
        tt = link.get("targetType")
        if tt is not None and tt != "CASE" and not (isinstance(tt, str) and EXT_ASSOC_RE.match(tt)):
            warn(f"{loc}.{field}.targetType",
                 f"expected \"CASE\" or an ext: value, got {tt!r} — omit targetType for in-package links")
    return link if ok else None


def check_datetime(obj, field, loc, required=True):
    v = obj.get(field)
    if v is None:
        if required:
            err(f"{loc}.{field}", f"required field is missing")
        return
    if not is_datetime(v):
        err(f"{loc}.{field}", f"must be ISO 8601 with timezone "
                              f"(e.g. 2025-01-15T10:30:00+00:00), got {v!r}")


def check_date(obj, field, loc):
    v = obj.get(field)
    if v is None:
        return
    if not is_date(v):
        err(f"{loc}.{field}", f"must be YYYY-MM-DD, got {v!r}")


def check_str_or_array(obj, field, loc, array_only=False):
    v = obj.get(field)
    if v is None:
        return
    if array_only:
        if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            err(f"{loc}.{field}", f"must be an array of strings, got {v!r}")
    elif not is_str_or_str_array(v):
        err(f"{loc}.{field}", f"must be a string or array of strings, got {v!r}")


# ----------------------------------------------------------------- document

def check_document(doc):
    if not isinstance(doc, dict):
        err("CFDocument", "must be an object")
        return None
    loc = "CFDocument"
    ident = doc.get("identifier")
    if not is_uuid(ident):
        err(f"{loc}.identifier", f"must be a lowercase UUID, got {ident!r}")
    check_uri_shape(doc, "uri", "CFDocuments", loc)
    if doc.get("caseVersion") != "1.1":
        err(f"{loc}.caseVersion", f'must be "1.1", got {doc.get("caseVersion")!r}')
    for f in ("creator", "title"):
        if not isinstance(doc.get(f), str) or not doc.get(f):
            err(f"{loc}.{f}", "required field is missing or empty")
    check_datetime(doc, "lastChangeDateTime", loc)
    status = doc.get("adoptionStatus")
    if status is not None:
        if not isinstance(status, str):
            err(f"{loc}.adoptionStatus", f"must be a string, got {status!r}")
        elif status.strip() == "":
            warn(f"{loc}.adoptionStatus",
                 "empty — the framework is listed publicly with no status; "
                 "set a CASE 1.1 recommended value")
        elif status.lower() not in RECOGNIZED_ADOPTION:
            warn(f"{loc}.adoptionStatus",
                 f"{status!r} is stored as sent — not a CASE 1.1 recommended value "
                 f"(Draft, Pending Implementation, Implemented, Retired; OpenSALT adds Private Draft)")
        elif status.lower() in {v.lower() for v in LEGACY_ADOPTION}:
            warn(f"{loc}.adoptionStatus",
                 f"legacy CASE 1.0 value {status!r} — prefer {LEGACY_SUCCESSOR[RECOGNIZED_ADOPTION[status.lower()]]} "
                 f"(kept for compatibility and follows its replacement's rules)")
    check_date(doc, "statusStartDate", loc)
    check_date(doc, "statusEndDate", loc)
    check_link(doc, "licenseURI", loc)
    check_link(doc, "CFPackageURI", loc)
    for f in ("subjectURI",):
        arr = doc.get(f)
        if isinstance(arr, list):
            for i, link in enumerate(arr):
                check_link({f: link}, f, f"{loc}.{f}[{i}]")
    if "CFPackageURI" not in doc:
        warn(f"{loc}", "CFPackageURI is missing — recommended for OpenSALT compatibility")
    return ident


# -------------------------------------------------------------------- items

def check_item(item, doc_ident, doc_title, index, declared_types):
    loc = f"CFItems[{index}]"
    if not isinstance(item, dict):
        err(loc, "must be an object")
        return
    if not is_uuid(item.get("identifier")):
        err(f"{loc}.identifier", f"must be a lowercase UUID, got {item.get('identifier')!r}")
    check_uri_shape(item, "uri", "CFItems", loc)
    link = check_link(item, "CFDocumentURI", loc, required=True)
    if link and doc_ident:
        if link.get("identifier") != doc_ident:
            err(f"{loc}.CFDocumentURI.identifier",
                f"does not reference this package's CFDocument ({doc_ident})")
        elif link.get("title") != doc_title:
            warn(f"{loc}.CFDocumentURI.title",
                 f"does not match the document title {doc_title!r}")
    if not isinstance(item.get("fullStatement"), str) or not item.get("fullStatement"):
        err(f"{loc}.fullStatement", "required field is missing or empty")
    check_datetime(item, "lastChangeDateTime", loc)
    check_str_or_array(item, "subject", loc)
    check_str_or_array(item, "educationLevel", loc)
    check_str_or_array(item, "conceptKeywords", loc, array_only=True)
    for f in ("CFItemTypeURI", "licenseURI", "conceptKeywordsURI"):
        check_link(item, f, loc)
    if isinstance(item.get("subjectURI"), list):
        for i, l in enumerate(item["subjectURI"]):
            check_link({"subjectURI": l}, "subjectURI", f"{loc}.subjectURI[{i}]")

    # ---- CFItemType is a label only (kept for the editor, not preserved on export)
    itype = item.get("CFItemType")
    itype_uri = item.get("CFItemTypeURI")
    if itype is not None and itype_uri is None:
        warn(f"{loc}.CFItemTypeURI",
             "CFItemType is a label kept for the editor only — it is NOT preserved as the "
             "item type on export. Declare the type in CFDefinitions.CFItemTypes and set CFItemTypeURI")
    if isinstance(itype_uri, dict) and itype_uri.get("identifier"):
        decl = declared_types.get(itype_uri["identifier"])
        if decl is None:
            warn(f"{loc}.CFItemTypeURI",
                 f"references item type {itype_uri['identifier']!r} not declared in "
                 f"CFDefinitions.CFItemTypes")
        elif isinstance(itype, str) and itype and decl.get("title") != itype:
            warn(f"{loc}.CFItemTypeURI",
                 f"declared title {decl.get('title')!r} does not match the item's CFItemType {itype!r}")

    # ---- humanCodingScheme quality
    scheme = item.get("humanCodingScheme")
    if isinstance(scheme, str) and scheme:
        if any(ch.isspace() for ch in scheme):
            warn(f"{loc}.humanCodingScheme",
                 f"contains whitespace — coding schemes are normally space-free ({scheme!r})")
        elif MACHINE_ID_SCHEME_RE.match(scheme):
            warn(f"{loc}.humanCodingScheme",
                 f"looks like an opaque machine ID, not a human-readable code ({scheme!r}) — "
                 f"keep machine IDs in extensions and synthesize a hierarchical scheme "
                 f"(e.g. CMP.D01.A05.T03, indexes from sibling order)")

    # ---- OpenSALT item kinds
    ext = item.get("extensions")
    if ext is None:
        return
    if not isinstance(ext, dict):
        err(f"{loc}.extensions", f"must be an object, got {type(ext).__name__}")
        return
    kind = ext.get("salt:type")
    if kind is None:
        return
    if kind not in SALT_KINDS:
        err(f"{loc}.extensions.'salt:type'",
            f"unknown kind {kind!r} — must be one of {sorted(SALT_KINDS)} "
            f"(unrecognized values silently become standard items on import)")
        return
    if kind == "credential":
        ob3 = ext.get("ob3")
        if ob3 is None:
            err(f"{loc}.extensions.ob3", f"required for salt:type credential")
        elif not isinstance(ob3, str):
            err(f"{loc}.extensions.ob3",
                f"must be a STRING containing JSON (escape inner quotes), "
                f"got {type(ob3).__name__}")
        else:
            try:
                parsed = json.loads(ob3)
                if not isinstance(parsed, dict):
                    err(f"{loc}.extensions.ob3", "payload must be a JSON object")
            except json.JSONDecodeError as e:
                err(f"{loc}.extensions.ob3", f"payload is not valid JSON: {e}")
    elif kind == "public_key":
        if not isinstance(ext.get("salt:kid"), str):
            warn(f"{loc}.extensions.'salt:kid'", "missing — defaults to 'jwk' on import")
        stmt = item.get("fullStatement", "")
        if isinstance(stmt, str) and stmt and not stmt.startswith("{"):
            try:
                json.loads(stmt)
            except json.JSONDecodeError:
                warn(f"{loc}.fullStatement",
                     "public_key items normally carry the JWK as a JSON string")
    elif kind == "identifier":
        stmt = item.get("abbreviatedStatement", "")
        if isinstance(stmt, str) and stmt and not is_uri(stmt):
            warn(f"{loc}.abbreviatedStatement",
                 "identifier items normally carry the identifier URI here")


# ------------------------------------------------------------- associations

def check_association(a, doc_ident, known, index):
    loc = f"CFAssociations[{index}]"
    if not isinstance(a, dict):
        err(loc, "must be an object")
        return
    if not is_uuid(a.get("identifier")):
        err(f"{loc}.identifier", f"must be a lowercase UUID, got {a.get('identifier')!r}")
    check_uri_shape(a, "uri", "CFAssociations", loc)
    link = check_link(a, "CFDocumentURI", loc, required=True)
    if link and doc_ident and link.get("identifier") != doc_ident:
        err(f"{loc}.CFDocumentURI.identifier",
            f"does not reference this package's CFDocument ({doc_ident})")
    check_datetime(a, "lastChangeDateTime", loc)
    atype = a.get("associationType")
    if atype not in ASSOC_TYPES and not (isinstance(atype, str) and EXT_ASSOC_RE.match(atype)):
        err(f"{loc}.associationType",
            f"must be a base type {sorted(ASSOC_TYPES)} or match ext:[a-zA-Z0-9._-]+, "
            f"got {atype!r}")
    if "sequenceNumber" in a and not isinstance(a["sequenceNumber"], int):
        err(f"{loc}.sequenceNumber", f"must be an integer, got {a['sequenceNumber']!r}")
    if atype == "isChildOf" and "sequenceNumber" not in a:
        warn(f"{loc}.sequenceNumber",
             "missing on isChildOf — sibling order is not preserved on import")

    endpoints = {}
    for f in ("originNodeURI", "destinationNodeURI"):
        endpoints[f] = check_link(a, f, loc, gen=True, required=True)

    o, d = endpoints.get("originNodeURI"), endpoints.get("destinationNodeURI")
    if o and d and o.get("identifier") == d.get("identifier"):
        err(loc, f"self-referential association ({o.get('identifier')})")
    for f, e in endpoints.items():
        if not e:
            continue
        ident = e.get("identifier")
        if ident in known:
            continue
        uri = e.get("uri", "")
        if isinstance(uri, str) and "/ims/case/" in uri:
            err(f"{loc}.{f}.identifier",
                f"dangling internal reference — identifier {ident!r} not found in this package")
        else:
            warn(f"{loc}.{f}",
                 f"references an external target not in this package ({ident!r})")


# -------------------------------------------------------------- definitions

DEFINITION_REQUIRED = {
    "CFSubjects": ("title", "hierarchyCode"),
    "CFLicenses": ("title", "licenseText"),
    "CFItemTypes": ("title", "description", "hierarchyCode"),
    "CFConcepts": ("title", "hierarchyCode"),
    "CFAssociationGroupings": ("title",),
}


def check_definitions(defs):
    if not isinstance(defs, dict):
        err("CFDefinitions", f"must be an object, got {type(defs).__name__}")
        return
    for key, required_fields in DEFINITION_REQUIRED.items():
        arr = defs.get(key)
        if arr is None:
            continue
        if not isinstance(arr, list):
            err(f"CFDefinitions.{key}", f"must be an array, got {type(arr).__name__}")
            continue
        segment = {"CFSubjects": "CFSubjects", "CFLicenses": "CFLicenses",
                   "CFItemTypes": "CFItemTypes", "CFConcepts": "CFConcepts",
                   "CFAssociationGroupings": "CFAssociationGroupings"}[key]
        for i, obj in enumerate(arr):
            loc = f"CFDefinitions.{key}[{i}]"
            if not isinstance(obj, dict):
                err(loc, "must be an object")
                continue
            if not is_uuid(obj.get("identifier")):
                err(f"{loc}.identifier", f"must be a lowercase UUID, got {obj.get('identifier')!r}")
            check_uri_shape(obj, "uri", segment, loc)
            check_datetime(obj, "lastChangeDateTime", loc)
            for f in required_fields:
                if not isinstance(obj.get(f), str) or not obj.get(f):
                    err(f"{loc}.{f}", "required field is missing or empty")


# ------------------------------------------------------------------ rubrics

def check_rubrics(rubrics):
    if not isinstance(rubrics, list):
        err("CFRubrics", f"must be an array, got {type(rubrics).__name__}")
        return
    for i, r in enumerate(rubrics):
        loc = f"CFRubrics[{i}]"
        if not isinstance(r, dict):
            err(loc, "must be an object")
            continue
        if not is_uuid(r.get("identifier")):
            err(f"{loc}.identifier", f"must be a lowercase UUID, got {r.get('identifier')!r}")
        check_uri_shape(r, "uri", "CFRubrics", loc)
        check_datetime(r, "lastChangeDateTime", loc)
        if not isinstance(r.get("title"), str) or not r.get("title"):
            warn(f"{loc}.title", "missing — rubrics are hard to navigate without a title")
        criteria = r.get("CFRubricCriteria", [])
        if not isinstance(criteria, list):
            err(f"{loc}.CFRubricCriteria", f"must be an array, got {type(criteria).__name__}")
            continue
        for j, c in enumerate(criteria):
            cloc = f"{loc}.CFRubricCriteria[{j}]"
            if not isinstance(c, dict):
                err(cloc, "must be an object")
                continue
            if not is_uuid(c.get("identifier")):
                err(f"{cloc}.identifier", f"must be a lowercase UUID, got {c.get('identifier')!r}")
            check_uri_shape(c, "uri", "CFRubricCriteria", cloc)
            check_datetime(c, "lastChangeDateTime", cloc)
            if "CFItemURI" in c:
                check_link(c, "CFItemURI", cloc)
            if "rubricId" not in c:
                warn(f"{cloc}.rubricId", "missing — parent rubric link not explicit")
            if not isinstance(c.get("position"), int):
                warn(f"{cloc}.position", "missing — criterion order not explicit")
            levels = c.get("CFRubricCriterionLevels", [])
            if not isinstance(levels, list):
                err(f"{cloc}.CFRubricCriterionLevels",
                    f"must be an array, got {type(levels).__name__}")
                continue
            for k, lvl in enumerate(levels):
                lloc = f"{cloc}.CFRubricCriterionLevels[{k}]"
                if not isinstance(lvl, dict):
                    err(lloc, "must be an object")
                    continue
                if not is_uuid(lvl.get("identifier")):
                    err(f"{lloc}.identifier",
                        f"must be a lowercase UUID, got {lvl.get('identifier')!r}")
                check_uri_shape(lvl, "uri", "CFRubricCriterionLevels", lloc)
                check_datetime(lvl, "lastChangeDateTime", lloc)
                if "rubricCriterionId" not in lvl:
                    warn(f"{lloc}.rubricCriterionId", "missing — parent criterion link not explicit")
                if not isinstance(lvl.get("position"), int):
                    warn(f"{lloc}.position", "missing — level order not explicit")


# --------------------------------------------------------------------- main

def collect_known(doc, data):
    """Map identifier -> location label for referential-integrity checks."""
    known = {}
    if isinstance(doc, dict) and doc.get("identifier"):
        known[doc["identifier"]] = "CFDocument"
    for label, arr in (("CFItems", data.get("CFItems")),
                       ("CFAssociations", data.get("CFAssociations")),
                       ("CFRubrics", data.get("CFRubrics"))):
        if isinstance(arr, list):
            for i, o in enumerate(arr):
                if isinstance(o, dict) and o.get("identifier"):
                    known[o["identifier"]] = f"{label}[{i}]"
    defs = data.get("CFDefinitions")
    if isinstance(defs, dict):
        for key, arr in defs.items():
            if isinstance(arr, list):
                for i, o in enumerate(arr):
                    if isinstance(o, dict) and o.get("identifier"):
                        known[o["identifier"]] = f"CFDefinitions.{key}[{i}]"
    return known


def check_duplicates(data, doc):
    seen = {}
    entries = []
    if isinstance(doc, dict) and doc.get("identifier"):
        entries.append(("CFDocument", doc["identifier"]))
    for label, arr in (("CFItems", data.get("CFItems")),
                       ("CFAssociations", data.get("CFAssociations")),
                       ("CFRubrics", data.get("CFRubrics"))):
        if isinstance(arr, list):
            for i, o in enumerate(arr):
                if isinstance(o, dict) and o.get("identifier"):
                    entries.append((f"{label}[{i}]", o["identifier"]))
                if label == "CFRubrics" and isinstance(o, dict):
                    for j, c in enumerate(o.get("CFRubricCriteria") or []):
                        if isinstance(c, dict) and c.get("identifier"):
                            entries.append((f"{label}[{i}].CFRubricCriteria[{j}]",
                                            c["identifier"]))
                        if isinstance(c, dict):
                            for k, l in enumerate(c.get("CFRubricCriterionLevels") or []):
                                if isinstance(l, dict) and l.get("identifier"):
                                    entries.append(
                                        (f"{label}[{i}].CFRubricCriteria[{j}]"
                                         f".CFRubricCriterionLevels[{k}]", l["identifier"]))
    defs = data.get("CFDefinitions")
    if isinstance(defs, dict):
        for key, arr in defs.items():
            if isinstance(arr, list):
                for i, o in enumerate(arr):
                    if isinstance(o, dict) and o.get("identifier"):
                        entries.append((f"CFDefinitions.{key}[{i}]", o["identifier"]))
    for loc, ident in entries:
        if ident in seen:
            err(loc, f"duplicate identifier {ident!r} (first used at {seen[ident]})")
        else:
            seen[ident] = loc


def print_summary(data, known):
    items = data.get("CFItems") or []
    kinds = {}
    for it in items:
        if isinstance(it, dict):
            ext = it.get("extensions")
            kind = ext.get("salt:type", "standard") if isinstance(ext, dict) else "standard"
            kinds[kind] = kinds.get(kind, 0) + 1
    assoc = data.get("CFAssociations") or []
    types = {}
    external = 0
    for a in assoc:
        if not isinstance(a, dict):
            continue
        t = a.get("associationType", "?")
        types[t] = types.get(t, 0) + 1
        for f in ("originNodeURI", "destinationNodeURI"):
            e = a.get(f) or {}
            if isinstance(e, dict) and e.get("identifier") and e["identifier"] not in known:
                external += 1
    print("--- package summary ---")
    print(f"items: {len(items)}  by kind: {json.dumps(kinds, sort_keys=True)}")
    print(f"associations: {len(assoc)}  by type: {json.dumps(types, sort_keys=True)}")
    if external:
        print(f"association endpoints referencing external targets: {external}")
    defs = data.get("CFDefinitions") or {}
    counts = {k: len(v) for k, v in defs.items() if isinstance(v, list)}
    print(f"definitions: {json.dumps(counts, sort_keys=True)}  "
          f"rubrics: {len(data.get('CFRubrics') or [])}")


def validate(data):
    doc = data.get("CFDocument")
    if doc is None:
        err("package", "CFDocument is required")
    doc_ident = check_document(doc) if isinstance(doc, dict) else None
    doc_title = doc.get("title") if isinstance(doc, dict) else None

    declared_types = {}
    defs = data.get("CFDefinitions")
    if isinstance(defs, dict) and isinstance(defs.get("CFItemTypes"), list):
        for o in defs["CFItemTypes"]:
            if isinstance(o, dict) and o.get("identifier"):
                declared_types[o["identifier"]] = o

    items = data.get("CFItems")
    if items is not None:
        if not isinstance(items, list):
            err("CFItems", f"must be an array, got {type(items).__name__}")
        else:
            seen_schemes = {}
            for i, item in enumerate(items):
                check_item(item, doc_ident, doc_title, i, declared_types)
                if isinstance(item, dict):
                    scheme = item.get("humanCodingScheme")
                    if isinstance(scheme, str) and scheme:
                        if scheme in seen_schemes:
                            warn(f"CFItems[{i}].humanCodingScheme",
                                 f"duplicate coding scheme {scheme!r} (first used at "
                                 f"CFItems[{seen_schemes[scheme]}]) — schemes should be unique "
                                 f"within the framework")
                        else:
                            seen_schemes[scheme] = i

    known = collect_known(doc, data)
    assoc = data.get("CFAssociations")
    if assoc is not None:
        if not isinstance(assoc, list):
            err("CFAssociations", f"must be an array, got {type(assoc).__name__}")
        else:
            for i, a in enumerate(assoc):
                check_association(a, doc_ident, known, i)

    if data.get("CFDefinitions") is not None:
        check_definitions(data["CFDefinitions"])
    if data.get("CFRubrics") is not None:
        check_rubrics(data["CFRubrics"])

    check_duplicates(data, doc)
    return known


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("package", help="path to the CFPackage JSON file")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as errors (recommended before distribution)")
    ap.add_argument("--summary", action="store_true",
                    help="print item/association counts after validation")
    args = ap.parse_args()

    try:
        with open(args.package, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        print(f"error: cannot read {args.package}: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("error: package root must be a JSON object", file=sys.stderr)
        return 2

    known = validate(data)

    for msg in errors:
        print(msg)
    for msg in warnings:
        print(msg)
    print(f"{'OK' if not errors else 'FAILED'}: "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")

    if args.summary:
        print_summary(data, known)

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
