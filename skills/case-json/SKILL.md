---
name: case-json
description: Convert source documents and other raw inputs into a valid CASE 1.1 CFPackage JSON document. Use when asked to create CASE JSON, convert a standards or competency document to CASE, or generate a competency framework from a document.
argument-hint: [paste text, file path, or describe the source]
allowed-tools: Read, Write, Grep, Glob, Bash(uuidgen), Bash(cat *), Bash(file *), Bash(wc *)
---

# CASE 1.1 Document-to-Framework Generator

You are a CASE 1.1 expert generating a `CFPackage` from source material such as standards documents, competency frameworks, curricula, policies, rubrics, PDFs, spreadsheets, CSVs, or copied text.

Your job is not just to "convert text to JSON." Your job is to:

1. extract the framework structure from the source,
2. preserve the source's hierarchy and ordering,
3. represent that structure in valid CASE 1.1 package JSON,
4. avoid inventing semantics that the source does not support.

Prefer faithful structure over over-modeling.

## Input

$ARGUMENTS

## Operating Rules

- Treat the source document as authoritative.
- Preserve the source wording for statements whenever possible.
- Preserve the source hierarchy whenever it is visible or strongly implied.
- Preserve source ordering with `sequenceNumber` on `isChildOf` associations.
- Do not invent extra relationships unless the source clearly states them.
- Do not use placeholder UUIDs. Generate real UUID v4 values with `uuidgen`.
- Do not leave `fullStatement` empty. If the source only gives a short label, use that label as the `fullStatement`.
- Prefer arrays for repeatable fields such as `subject`, `subjectURI`, `educationLevel`, and `conceptKeywords`.
- Include `CFPackageURI` on `CFDocument`, and include `CFDocumentURI` on each item and association for compatibility with OpenSALT exports/imports.

## Phase 1: Load and Understand the Source

First determine what kind of source you were given:

| Source Type | What To Do |
|---|---|
| Raw pasted text | Parse the text directly |
| Local file path | Read the file first |
| PDF / image | Extract visible headings, numbering, tables, and statements |
| CSV / spreadsheet | Detect columns, row types, and parent-child hints |
| JSON / XML / HTML | Parse structure first, then map fields to CASE |
| Existing framework in another format | Preserve the original hierarchy and identifiers where possible |

Then build a short internal source map:

- framework title
- creator / publisher / issuing body
- source URL if present
- language
- version / publication date / adoption status
- the document outline
- every extractable competency / standard / objective / skill
- any explicit cross-links, prerequisites, replacement statements, or rubric levels

If the source is ambiguous, make the narrowest reasonable assumptions and record them in `CFDocument.notes`.

## Phase 2: Decide What Becomes a CFItem

A `CFItem` should represent either:

- a real statement the framework expects someone to use, or
- a meaningful grouping node such as Domain, Strand, Cluster, Topic, or Section when that grouping organizes child statements.

Do not create CFItems for:

- cover pages
- table of contents entries
- decorative headings
- page numbers
- boilerplate copyright text
- explanatory prose that is not part of the framework itself

### Heuristics for document parsing

| Source Pattern | CASE Modeling Choice |
|---|---|
| Numbered heading with child standards beneath it | Create a parent CFItem for the heading |
| Bullet list of discrete standards | One CFItem per bullet |
| Statement with sub-bullets that refine it | Parent CFItem plus child CFItems |
| A heading that is only layout furniture | Do not model as a CFItem |
| Table row with code + statement | One CFItem per row |
| A rubric attached to an item | Model rubric separately in `CFRubrics` |
| Cross-reference like "see also X" | Add `isRelatedTo` only if the target can be identified |

When a section title is both a heading and a meaningful framework concept, keep it as a CFItem even if it is short.

## Phase 3: Build the Hierarchy

Every extracted item must have exactly one parent in the package hierarchy.

- Top-level items are children of the `CFDocument`.
- Nested items are children of their containing CFItem.
- Use one `isChildOf` association per item.
- Set `originNodeURI` to the child.
- Set `destinationNodeURI` to the parent.

For each parent, assign `sequenceNumber` values starting at `1` and increasing in source order.

If the source has no clear hierarchy, attach all extracted items directly to the `CFDocument`.

## Phase 4: Map Source Data to CASE Fields

### Document metadata

Map source metadata to `CFDocument`:

- title -> `title`
- authoring organization -> `creator`
- publisher -> `publisher`
- summary / abstract -> `description`
- version label -> `version`
- publication / adoption language -> `adoptionStatus`
- source URL -> `officialSourceURL`
- language -> `language`
- subjects / disciplines -> `subject`

Use these safe defaults when the source does not say otherwise:

- `caseVersion`: `"1.1"`
- `language`: `"en-US"` for English-language sources
- `adoptionStatus`: `"Draft"` if you are synthesizing a framework from a source document and no official status is stated

### Item mapping

Map each extracted statement or grouping node to a `CFItem`:

- statement text -> `fullStatement`
- short code / standard number -> `humanCodingScheme`
- list marker like `a`, `i`, `1` -> `listEnumeration` if useful
- short label -> `abbreviatedStatement` or `alternativeLabel`
- level / grade band -> `educationLevel`
- keywords -> `conceptKeywords`
- notes / commentary / caveats -> `notes`
- local type label such as Domain, Cluster, Strand, Standard, Skill -> `CFItemType`

Preserve original wording in `fullStatement`. Do not rewrite standards into a different voice unless the source is fragmentary and the fragment itself is the only available statement.

### Synthesizing human coding schemes

`humanCodingScheme` is a human-readable code that communicates tree position — it is not an identifier. When the source has real standards codes, preserve them (mapping table above). When it does not, synthesize one. **Never copy opaque machine identifiers** (hashes, nanoid-style IDs like `mt_Xy12ab34`, UUIDs) into this field — carry those in namespaced `extensions` keys (e.g. `"source:topicId"`) or `notes`.

Synthesis recipe:

1. Give each top-level grouping a short code: a 3–4 letter abbreviation or a sequential code (`CMP`, `ENG`, … or `S01`, `S02`, …).
2. Append one dotted segment per level below it: zero-padded sibling indexes (`CMP.D01.A05.T03`).
3. Derive every index from sibling order — the same order used for `sequenceNumber` — so codes are deterministic and stable across republished versions.
4. No spaces, ampersands, or punctuation beyond dots and hyphens. Aim for ≤ 40 characters: abbreviate long level names and use indexes, not titles (`CMP.D01.A05.T03`, not `CMP.Algorithms & Programming.age5.T03`).
5. Uniqueness across the framework is mandatory — the validator warns on duplicate schemes.
6. Record the convention in `CFDocument.notes` (e.g. "Coding scheme synthesized as SUBJECT.DOMAIN.BAND.TOPIC from source order") so consumers can decode it.

## Phase 5: Create Definitions Only When They Are Actually Used

Use `CFDefinitions` for reusable vocabulary:

- `CFItemTypes` for item classifications you assign to CFItems
- `CFSubjects` for subjects referenced by `subjectURI`
- `CFConcepts` for reusable concept links
- `CFLicenses` when the document names a license
- `CFAssociationGroupings` only when you need named groups of associations

Every definition object needs `identifier`, `uri`, `title`, and `lastChangeDateTime`, plus type-specific required fields — omitting them is the most common import failure:

- `CFSubjects` and `CFConcepts`: also `hierarchyCode`
- `CFItemTypes`: also `hierarchyCode` and `description`
- `CFLicenses`: also `licenseText`

### Strong recommendation

If a CFItem has `CFItemTypeURI`, define the matching item type in `CFDefinitions.CFItemTypes`.

If a CFDocument or CFItem has `subjectURI`, define the matching subject in `CFDefinitions.CFSubjects`.

If you are not going to reference a definition object, do not create it just to fill space.

### Important OpenSALT detail

`conceptKeywordsURI` is treated as a single `LinkURI`, not an array, in the shipped DTOs and transformers. Use at most one linked concept there.

## Phase 6: Generate Identifiers and URIs

Generate a UUID v4 for every CASE entity:

- `CFDocument`
- each `CFItem`
- each `CFAssociation`
- each definition object you create
- each rubric, rubric criterion, and rubric level

Use `uuidgen` to generate real IDs:

```bash
for i in $(seq 1 N); do uuidgen; done
```

For every entity, set:

- `identifier`: the UUID
- `uri`: `urn:uuid:{identifier}`

`urn:uuid:` URIs are valid — OpenSALT stores the URI exactly as sent and does not require it to resolve. For frameworks meant for distribution, prefer the canonical pattern `https://{host}/ims/case/v1p1/{ObjectType}/{identifier}` (object-type segment matching the collection, identifier suffix matching the object) so external consumers can dereference links.

Use one ISO 8601 timestamp for the package generation run unless the source provides a better timestamp to preserve.

## Phase 7: Build the Package

Write a top-level JSON object with this shape:

```json
{
  "CFDocument": {},
  "CFItems": [],
  "CFAssociations": [],
  "CFDefinitions": {},
  "CFRubrics": []
}
```

`CFRubrics` is optional and should only be included when the source contains rubric or proficiency structures.

### Minimum practical package

At minimum, a useful generated package should contain:

- one `CFDocument`
- one or more `CFItems`
- one `isChildOf` association for every CFItem

The formal schema only requires `CFDocument`, but a generated framework without items and associations is usually not useful.

## Phase 8: Association Rules

Use these CASE association types only when supported by the source:

- `isChildOf`
- `isPartOf`
- `isPeerOf`
- `precedes`
- `isRelatedTo`
- `exactMatchOf`
- `hasSkillLevel`
- `exemplar`
- `replacedBy`
- `isTranslationOf`

### Default rule

For document-to-framework conversion, `isChildOf` is the only association you should assume by default.

Add other associations only when the source explicitly indicates them, such as:

- "prerequisite" -> `precedes`
- "aligned to" / "equivalent to" -> `exactMatchOf`
- "replaced by" -> `replacedBy`
- "translation of" -> `isTranslationOf`

## Phase 9: Link Object Rules

`LinkURI` shape:

```json
{
  "title": "Human readable title",
  "identifier": "11111111-1111-4111-8111-111111111111",
  "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
}
```

Use `LinkURI` for:

- `CFPackageURI`
- `CFDocumentURI`
- `CFItemTypeURI`
- `subjectURI`
- `licenseURI`
- `CFAssociationGroupingURI`
- `CFItemURI` inside rubrics

`LinkGenURI` shape:

```json
{
  "title": "Human readable title",
  "identifier": "11111111-1111-4111-8111-111111111111",
  "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
}
```

Use `LinkGenURI` for `originNodeURI` and `destinationNodeURI`.

Important: if you include `targetType`, the CASE 1.1 OpenAPI/OpenSALT schema expects `"CASE"` or an `ext:...` value, not `"CFItem"` or `"CFDocument"`. For internal package links, the safest choice is to omit `targetType`.

## Phase 10: Validation Checklist

Before writing the file, verify:

- every CFItem has a non-empty `fullStatement`
- every CFItem has exactly one `isChildOf` association
- every top-level item points to the CFDocument as its parent
- nested items point to the correct parent item
- `sequenceNumber` values are contiguous per parent in source order
- all UUIDs are unique and valid
- every `uri` is `urn:uuid:{identifier}`
- every link object points to an entity that exists in the package, unless it is intentionally external
- every `CFItemTypeURI` resolves to a defined `CFItemType`
- every `subjectURI` resolves to a defined `CFSubject`
- every generated `CFItemType` has a `description`
- every definition object has `hierarchyCode` (CFItemTypes, CFSubjects, CFConcepts) and `lastChangeDateTime`
- every `humanCodingScheme` is human-meaningful: no opaque machine IDs, no whitespace, unique across the framework
- `conceptKeywordsURI`, if used, is a single `LinkURI`
- `caseVersion` is `"1.1"`
- `CFPackageURI` points to the document itself
- `CFDocumentURI` is present on items and associations
- no decorative or non-framework text was turned into CFItems

## Output

Write the JSON to a file using the `Write` tool.

- Use a slugified version of the framework title plus `.json`
- If no reliable title exists, use `case-output.json`

Do not print the raw JSON to the console. The file is the deliverable.

If the source is too incomplete to extract a full hierarchy, still produce the best package you can:

- create a minimal `CFDocument`
- create one or more CFItems from the clearest statements available
- attach them directly to the document with `isChildOf`
- record assumptions or ambiguity in `CFDocument.notes`

For field-level details, see [data-model-reference.md](data-model-reference.md). For a sample package shape, see [examples/example_output.json](examples/example_output.json).

## Phase 11: Quality-control handoff

The written package is a first draft. Before delivering it as final, hand it to the opensalt-skill quality-control pass: structural validation (`../opensalt-skill/scripts/validate_case_package.py --strict`), the mechanical inventory (`../opensalt-skill/scripts/qc_inventory.py`), content-fidelity sampling against this source, and a QC report ending in human sign-off — see [../opensalt-skill/references/quality-control.md](../opensalt-skill/references/quality-control.md). Do not call the file final without that sign-off.

## Companion skill: opensalt-skill

This repository also ships **opensalt-skill** (`../opensalt-skill/`), covering what this skill deliberately does not:

- **Validation**: run `python3 ../opensalt-skill/scripts/validate_case_package.py <output>.json` on the generated package before delivering — it catches missing `hierarchyCode`/`lastChangeDateTime` on definitions, dangling references, and OpenSALT kind requirements.
- **OpenSALT item kinds** (`course`, `job`, `credential`, `organization`, …), distribution and versioning guidance.
- **Upload and read-back** against a live OpenSALT registry (`/api/v1` writes, CASE catalog and `/uri/` markdown reads).
