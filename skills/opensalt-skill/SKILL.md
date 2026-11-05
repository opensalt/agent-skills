---
name: opensalt-skill
description: Use when creating, editing, validating, or exporting CASE 1.1 JSON packages for OpenSALT import — competency frameworks, academic standards, learning objectives, rubrics, or OpenSALT item kinds (course, job, assessment, credential, organization, identifier, public_key) — when uploading a framework to an OpenSALT registry via `/api/v1`, or when reading published frameworks back (CASE catalog, `/uri/` markdown, MCP server). Triggers on CASE, CFDocument, CFItems, CFAssociations, salt:type, CFPackage, competency framework JSON, or distributing/sharing a standards framework.
---

# Creating OpenSALT CASE Frameworks

## Overview

Produce a single CASE 1.1 JSON package (`CFPackage`) that imports cleanly into OpenSALT and is safe to distribute: one `CFDocument`, a flat array of `CFItems`, hierarchy expressed **only** through `isChildOf` associations in `CFAssociations`, plus supporting definitions.

Core principle: **every object must be self-consistent and resolvable** — a lowercase UUID identifier, a URI built from that identifier, a `CFDocumentURI` back-reference, and an ISO 8601 timestamp with timezone. OpenSALT validates writes and rejects invalid packages with a JSON `detail` listing the problems — nothing is silently fixed — and a distributed framework is consumed by other tools too, so validate locally before delivering.

For converting an existing source document (PDF, CSV, prose) into a first-draft package, use the companion **`case-json`** skill in this repository (`../case-json/`); this skill covers validation, OpenSALT item kinds, distribution, and registry publishing.

## Deliverable

One `.json` file with this top-level shape (only `CFDocument` is required):

```json
{
  "CFDocument": { "identifier": "<uuid>", "uri": "https://<host>/ims/case/v1p1/CFDocuments/<uuid>", "caseVersion": "1.1", "creator": "...", "title": "...", "lastChangeDateTime": "2025-01-15T10:30:00+00:00", "CFPackageURI": { "title": "<same title>", "identifier": "<doc uuid>", "uri": "https://<host>/ims/case/v1p1/CFPackages/<doc uuid>" } },
  "CFItems": [ { "identifier": "<uuid>", "uri": "https://<host>/ims/case/v1p1/CFItems/<uuid>", "CFDocumentURI": { "title": "<doc title>", "identifier": "<doc uuid>", "uri": "<doc uri>" }, "fullStatement": "...", "lastChangeDateTime": "..." } ],
  "CFAssociations": [ { "identifier": "<uuid>", "uri": "https://<host>/ims/case/v1p1/CFAssociations/<uuid>", "CFDocumentURI": { "...": "..." }, "lastChangeDateTime": "...", "sequenceNumber": 1, "originNodeURI": { "title": "<child>", "identifier": "<child uuid>", "uri": "<child uri>", "targetType": "CASE" }, "associationType": "isChildOf", "destinationNodeURI": { "title": "<parent>", "identifier": "<parent uuid>", "uri": "<parent uri>", "targetType": "CASE" } } ],
  "CFDefinitions": { "CFSubjects": [], "CFItemTypes": [], "CFLicenses": [], "CFConcepts": [], "CFAssociationGroupings": [] },
  "CFRubrics": []
}
```

`LinkURI` references always carry exactly `title`, `identifier`, `uri`. `LinkGenURI` (association endpoints) adds optional `targetType` (`"CASE"` for in-package objects, `ext:...` for external).

## Workflow

1. **Design the framework.** Decide from the content: title/creator/publisher, subject(s), language, adoption status, the item hierarchy (top-level nodes vs. child statements), item types (e.g. Competency, Standard, Learning Objective), which items are OpenSALT kinds (course/job/credential/organization — see below), any rubrics. Prefer faithful structure over over-modeling; a grouping node is a real CFItem (Domain, Strand, Cluster) with its own statement or label.
2. **Read the format reference** ([references/case-1.1-format.md](references/case-1.1-format.md)) for any object type you have not produced before — it has every field table, required/optional flags, and complete import examples (minimal and full). Do not guess field names from memory.
3. **Generate the package.** Use real UUIDs (`uuidgen` or `uuid.uuid4()`), lowercase. Pick **one URI convention for the whole framework** and use it everywhere: for OpenSALT-published frameworks prefer the registry's own identifier space, `https://{host}/uri/{identifier}` (package document: `/uri/p{identifier}`) — it is what OpenSALT itself mints, it dereferences with content negotiation for every format, and it keeps JSON-LD node identifiers self-resolving. The spec-shaped alternative, `https://{host}/ims/case/v1p1/{ObjectType}/{identifier}` (`ObjectType` = plural segment: `CFDocuments`, `CFItems`, `CFAssociations`, `CFSubjects`, `CFLicenses`, `CFItemTypes`, `CFConcepts`, `CFAssociationGroupings`, `CFRubrics`, `CFRubricCriteria`, `CFRubricCriterionLevels`, `CFPackages`), is for pure-CASE-ecosystem distribution. Embedding the object's identifier as the URI's tail is the convention (matching the spec API and OpenSALT's default scheme), not a technical requirement — any valid URI is allowed, and the validator warns rather than errors on deviations. Set `lastChangeDateTime` to one consistent timestamp for the whole package.
4. **Validate** with the bundled script (below). Fix every error, review warnings, re-run.
5. **Distribute**: deliver the JSON file, and/or upload to an OpenSALT registry via `/api/v1` (below). After upload, verify by fetching the package back and comparing identifiers.

## Hard invariants

These are the rules OpenSALT validates or silently mangles when violated:

| Rule | Why |
|---|---|
| `caseVersion` is exactly `"1.1"` | Schema-level requirement |
| All identifiers: lowercase UUIDs, 8-4-4-4-12 hex | Uppercase or malformed UUIDs fail validation |
| `uri`: pick one convention framework-wide — OpenSALT-native `https://{host}/uri/{identifier}` (package doc `/uri/p{identifier}`) or spec-shaped `https://{host}/ims/case/v1p1/{ObjectType}/{identifier}`. Ending the URI with the object's identifier is a convention (from the spec API and OpenSALT's default scheme), **not** a requirement — linked data allows any valid URI | The convention keeps URIs dereferenceable with negotiation (`/uri/`) and lets consumers relate a URI to its object without a lookup; the validator warns (does not error) on mismatches |
| Every CFItem and CFAssociation carries `CFDocumentURI` | Required; also how OpenSALT groups content on import |
| Every CFItem, CFAssociation, definition, rubric (and criterion/level) carries `lastChangeDateTime` in ISO 8601 **with timezone** (`+00:00`, not bare `Z`-less local time) | Required field; format is validated |
| `statusStartDate`/`statusEndDate` are `YYYY-MM-DD` | Different format from `lastChangeDateTime` |
| Hierarchy is flat arrays + `isChildOf` associations — never nested JSON | CASE has no nesting |
| `isChildOf`: **origin = child, destination = parent** | Reversing it inverts the whole tree |
| `sequenceNumber` on every `isChildOf`, starting at 1 per parent | Preserves source ordering of siblings |
| `subject`/`educationLevel`: string **or** array of strings; `conceptKeywords`: **always an array** of strings | Type-validated |
| Every `LinkURI` has non-empty `title`, UUID `identifier`, valid `uri` | Required for `CFItemTypeURI`, `licenseURI`, `subjectURI`, `conceptKeywordsURI`, `CFDocumentURI`, `CFPackageURI` |
| Every identifier used in any association endpoint exists in the package (or is an intentional external URI) | Dangling internal references import as broken links |
| `associationType` is a base type (`isChildOf`, `exactMatchOf`, `isRelatedTo`, `isPartOf`, `replacedBy`, `precedes`, `hasSkillLevel`, `isPeerOf`, `exemplar`, `isTranslationOf`) or matches `ext:[a-zA-Z0-9._-]+` | Anything else is rejected |
| All identifiers unique across the entire package | Duplicates collide on import |

## Hierarchy and ordering

- Items with no incoming `isChildOf` render as top-level nodes; every other item needs exactly one `isChildOf` (multiple parents is valid CASE but complicates the tree — use only for intentional cross-listing).
- Give every item a `humanCodingScheme`: preserve source codes (e.g. `MATH-7.ALG.1`); when the source has none, synthesize a hierarchical, space-free one from tree position (`CMP.D01.A05.T03`, indexes derived from sibling order) — never an opaque machine ID (those belong in namespaced `extensions`). Use `listEnumeration` for verbatim source numbering.
- `CFItemType` is a **label only** — OpenSALT keeps it for the editor but does **not** preserve it as the item type on export. To keep a type, declare it once in `CFDefinitions.CFItemTypes` (each needs `identifier`, `uri`, `title`, `hierarchyCode`, `lastChangeDateTime`) and point the item's `CFItemTypeURI` at that declaration. Use this for levels like "Strand"/"Competency"/"Standard".
- OpenSALT **item kinds** (`extensions.salt:type`) and CASE **item types** (`CFItemType`) are independent — a `course` item may also carry a `CFItemType`, but they don't have to correspond.

## OpenSALT item kinds

Set `extensions.salt:type` on a CFItem to specialize it (omit for a standard competency item; unrecognized values silently fall back to standard items, so spelling matters):

| `salt:type` | Represents | Extra extension keys | Standard-field mapping |
|---|---|---|---|
| `job` | Occupation | `ceterms:subjectWebpage` | abbrev=job title, full=description |
| `course` | Course | `ceterms:subjectWebpage`, `ceterms:deliveryType` | abbrev=name, full=description |
| `assessment` | Assessment | `ceterms:subjectWebpage`, `ceterms:deliveryType` | abbrev=name, full=description |
| `credential` | Open Badges 3.x credential | `ob3` | abbrev=ob3.name, full=ob3.description |
| `organization` | Organization | `ceterms:agentType`, `ceterms:subjectWebpage`, `ceterms:image`, `ceterms:jurisdiction`, `sdo:legalName`, `ceterms:ctid`, `salt:rorId` | abbrev=name, full=description |
| `identifier` | External URI identifier | `salt:idType` | abbrev=the URI |
| `public_key` | JWK public key | `salt:kid` | abbrev=key id, full=serialized JWK |

**Credential gotcha:** `ob3` is a *string containing JSON*, not a JSON object — escape the inner quotes: `"ob3": "{\"name\":\"...\"}"`. On import OpenSALT copies `ob3.name`/`description`/`humanCode`/`inLanguage`/`tag` into the standard fields.

See [references/case-1.1-format.md](references/case-1.1-format.md) § "OpenSALT Item Kinds" for a complete example of each kind.

## Distribution checklist

A framework intended for distribution/shared import needs:

- **License**: a `CFLicense` in `CFDefinitions` (with full `licenseText`) and `licenseURI` on the document (and items, if they differ).
- **Provenance**: `creator`, `publisher`, `officialSourceURL`, `version`, `adoptionStatus` + `statusStartDate` on the document. Status values: CASE 1.1 recommends `Draft`, `Pending Implementation`, `Implemented`, `Retired`; OpenSALT adds `Private Draft` (the only status hidden from the public catalog). Keep frameworks in `Draft` while still editing — `Implemented` locks item edits, `Retired` locks all edits. Legacy `Adopted`/`Deprecated` are accepted but follow those lock rules.
- **Stable identifiers**: use deterministic UUIDs (e.g. `uuid5(NAMESPACE_URL, <stable key>)` keyed on the framework's canonical URI or the item's `humanCodingScheme`) so a republished version keeps the same item URIs — cross-framework `exactMatchOf`/`isRelatedTo` associations from other frameworks stay valid. Random UUID v4 per generation makes every republish a different framework. This is also OpenSALT's documented pattern for idempotent imports: `POST` creates, `PUT` with the same identifiers replaces.
- **Version updates**: keep the document `identifier` and item identifiers stable across versions; bump `version` and `lastChangeDateTime`; items removed from the framework get a `replacedBy` association rather than silent deletion when a successor exists.
- **Subjects and item types defined**, not just referenced: every `subjectURI`/`CFItemTypeURI`/`conceptKeywordsURI`/`licenseURI` must resolve to an object in `CFDefinitions`.

## Validation

Before delivering anything, run the bundled validator (stdlib-only Python):

```bash
python3 <skill-dir>/scripts/validate_case_package.py package.json
# options: --strict (warnings fail) · --summary (counts by kind and association type)
```

Exit 0 = no errors; exit 1 = errors listed with location (`CFItems[3]`, field, reason). It checks the invariants table above end-to-end: required fields, UUID/URI/datetime formats, `LinkURI` shape, association types, referential integrity of association endpoints, duplicate identifiers, kind-specific requirements (`ob3` must parse as JSON), label-only `CFItemType` usage (type not declared or not referenced), `adoptionStatus` spellings, `humanCodingScheme` quality (duplicates, whitespace, machine-ID-shaped values), and rubric structure. Treat warnings as review items, not noise — a warning is usually a real defect in a distributed package.

## Uploading to OpenSALT

Writes go through the authenticated `/api/v1` API (OpenAPI spec: `/api/v1/doc.json`; security scheme `Bearer`). The CASE routes are read-only; there is no publish endpoint — status ships in the package.

**Auth**: a person creates a token in the browser at `/account/tokens`; send `Authorization: Bearer <token>` on every write. Agents never scrape `/login`, and `/framework/editor/…` is not an integration API. Creating or importing frameworks needs the **Editor** role, and the framework must not be a mirrored copy. `401` = invalid token, `403` = account/token not allowed, `404` = unknown identifier.

| Method | Endpoint | Effect |
|---|---|---|
| `POST` | `/api/v1/packages` | Import a CFPackage — creates the framework |
| `PUT` | `/api/v1/packages/{documentIdentifier}` | Replace a framework (send the same identifiers) |
| `DELETE` | `/api/v1/packages/{documentIdentifier}` | Delete the framework |
| `POST`/`PUT` | `/api/v1/documents[/{documentIdentifier}]` | Create / replace document metadata |
| `POST` | `/api/v1/packages/{documentIdentifier}/items` and `.../associations` | Create a single item/association (may omit `identifier`/`uri` — server assigns) |
| `GET`/`PUT`/`DELETE` | `.../items/{itemIdentifier}` · `.../associations/{associationIdentifier}` | Manage a single object |
| `GET` | `/api/v1/token` | Describe the presented token |

Mechanics that matter:

- Send `Accept: application/json` on writes. `POST`/`PUT` on packages answer **`201` with an empty body**; the `Location` header carries the package URL.
- Validation failures return JSON whose `detail` lists the problems (missing required properties listed together) — fix and resend; nothing is silently fixed.
- Imports are **idempotent by design**: identifiers are client-generated (see Distribution checklist); `POST` creates, `PUT` with the same identifiers replaces, and other packages may reference those identifiers.
- Publication status semantics: `Private Draft` hides the framework from the public catalog (everything else, including empty, is listed); `Implemented` locks item edits (associations still editable); `Retired` locks all edits. Set status in the package or via `PUT /api/v1/documents/{documentIdentifier}`.

Full details — token scopes (`read`/`crosswalk`/write modes), the articulation API, and error semantics — are in [references/registry-api.md](references/registry-api.md).

## Reading published content

Prefer CASE and `/uri/` for reads — both public, token-free, and CORS-enabled. The CASE paths are the spec endpoints (JSON only, per the CASE specification); `/uri/{identifier}` resolves the same object with content negotiation (`.md`, `.jsonld`, `.csv` via `Accept` or suffix). The stored `uri` is the object's permanent published identity (echoed verbatim on every export) and is what JSON-LD consumers see as the node identifier — which is why OpenSALT-native frameworks author `uri` values in the `/uri/` space.

- Catalog: `GET /ims/case/v1p1/CFDocuments` (`limit`/`offset`/`sort`/`orderBy`, `X-Total-Count` header). Full export: `GET /ims/case/v1p1/CFPackages/{documentIdentifier}` (`?download=1` for an attachment). Single objects: `/CFItems/{id}`, `/CFAssociations/{id}`, `/CFItemAssociations/{id}`, etc.
- Markdown for agents: `GET /uri/p{documentIdentifier}.md` (whole framework) or `/uri/{itemIdentifier}.md` — always send `Accept` or a path suffix, or the server answers `300 Multiple Choices`. Front matter carries `kind` (the item kind) and `itemType` (the framework's label). Packages run ~1–2 MB per 1,000 items; fetch single items when possible.
- MCP (read-only, no auth): point an MCP client at `/_mcp` for `opensalt_list_documents`, `opensalt_get_document`, `opensalt_get_item`, and related-item search.
- Successful GETs send `ETag`/`Last-Modified` with a 60 s cache max-age; repeat with `If-None-Match` for `304`.

## Common mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Nesting children inside parent items | Import drops or flattens them | Flat `CFItems` + `isChildOf` |
| `originNodeURI` = parent in `isChildOf` | Tree renders inverted | origin = child |
| Uppercase UUIDs | Validation failure | lowercase everywhere |
| `lastChangeDateTime` without timezone | Validation failure | `2025-01-15T10:30:00+00:00` |
| Missing `CFDocumentURI` on an item/association | Import failure | add to every one |
| `ob3` as a JSON object | Import failure | string containing escaped JSON |
| `conceptKeywords` as a plain string | Validation failure | array of strings |
| URI path segment ≠ object type or ≠ identifier | Broken references for consumers | follow the URI pattern exactly |
| `salt:type` typo (e.g. `courses`) | Item silently becomes a standard competency | use the exact kind names |
| Relying on `CFItemType` without `CFItemTypeURI` | Item type lost on export | declare in `CFItemTypes` + point `CFItemTypeURI` |
| Setting `Implemented`/`Retired` while still editing | Item (or all) edits locked by the server | keep `Draft` until final |
| Identifiers reused across objects | Collision on import | one UUID per object |
| Placeholder/dummy UUIDs | Broken links after import | generate real UUIDs |

## Reference map

Read [references/case-1.1-format.md](references/case-1.1-format.md) when you need:

- Field tables (required/optional, types) for any object → § CFDocument, CFItems, CFAssociations, CFDefinitions, CFRubrics
- OpenSALT item kinds with complete per-kind examples → § OpenSALT Item Kinds
- `LinkURI` vs `LinkGenURI` → § LinkURI and LinkGenURI
- URI construction and `local:` URIs → § Identifiers and URIs
- Complete import examples to copy shape from → § Complete Import Examples (minimal and full)

Read [references/registry-api.md](references/registry-api.md) when you need:

- Endpoints, request/response mechanics, error semantics for `/api/v1` writes → § Writing frameworks
- Token creation, scopes, and who may change what → § Tokens and roles
- Publication-status rules and catalog visibility → § Publication status
- Reading content via CASE routes, `/uri/` markdown, or MCP → § Reading published content
