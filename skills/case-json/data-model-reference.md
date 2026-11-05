# CASE 1.1 Data Model Reference for AI Generation

This reference is based on:

- `/core/public/case-v1p1-openapi.json`
- OpenSALT CASE DTOs and transformers in `core/src/`

It is intentionally generation-focused: the goal is to help an AI produce CASE packages that are both valid and practical to import into OpenSALT.

## Generation Priorities

When generating a CASE package from a document, optimize for these priorities in order:

1. valid JSON structure
2. faithful hierarchy and source ordering
3. complete `fullStatement` text on every item
4. internally consistent links and definitions
5. helpful metadata when the source provides it

## Top-Level `CFPackage`

```json
{
  "CFDocument": {},
  "CFItems": [],
  "CFAssociations": [],
  "CFDefinitions": {},
  "CFRubrics": []
}
```

### Practical rule

The schema formally requires only `CFDocument`, but a useful generated framework should almost always include:

- `CFDocument`
- `CFItems`
- `CFAssociations`

`CFDefinitions` and `CFRubrics` are optional.

## Core Invariants

These are the most important rules for document-to-framework generation:

- Every `CFItem` needs a unique UUID and `urn:uuid:` URI.
- Every `CFItem` should have exactly one `isChildOf` association.
- Top-level items should point to the `CFDocument` as parent.
- Child items should point to a parent `CFItem`.
- `sequenceNumber` should preserve source order within each parent.
- `fullStatement` must never be empty.
- If you use `CFItemTypeURI`, `subjectURI`, `licenseURI`, or `CFAssociationGroupingURI`, define the referenced object in `CFDefinitions`.

## `CFDocument`

### Required fields

| Field | Type | Notes |
|---|---|---|
| `identifier` | UUID | Generate a real UUID v4 |
| `uri` | URI | `urn:uuid:{identifier}`; canonical `https://…/ims/case/v1p1/{ObjectType}/{identifier}` for distribution |
| `creator` | string | Issuing body, author, or best available source |
| `title` | string | Framework title |
| `lastChangeDateTime` | date-time | ISO 8601 |

### Recommended fields

| Field | Type | When to use |
|---|---|---|
| `caseVersion` | string | Set to `"1.1"` |
| `CFPackageURI` | `LinkURI` | Recommended for compatibility with OpenSALT exports/imports |
| `frameworkType` | string | Such as `State Standard`, `Competency Framework`, `Course Outcomes` |
| `officialSourceURL` | URI | Canonical source URL |
| `publisher` | string | Publishing organization |
| `description` | string | Short description of the framework |
| `subject` | string[] | Prefer arrays even if there is one subject |
| `subjectURI` | `LinkURI`[] | Only if matching `CFSubjects` exist |
| `language` | string | Prefer RFC 5646 tags like `en-US` |
| `version` | string | Source version label |
| `adoptionStatus` | string | CASE 1.1 recommends `Draft`, `Pending Implementation`, `Implemented`, `Retired`; OpenSALT adds `Private Draft` (hides from catalog). Any string is accepted and stored as sent. `Implemented`/`Retired` lock edits |
| `statusStartDate` | date or date-time | If stated |
| `statusEndDate` | date or date-time | If stated |
| `licenseURI` | `LinkURI` | If license is known and defined |
| `notes` | string | Assumptions, provenance, ambiguity |

### Safe defaults

- `caseVersion`: `"1.1"`
- `language`: `"en-US"` for English-language sources
- `adoptionStatus`: `"Draft"` when synthesizing from a document with no explicit official status

## `CFItems`

Each `CFItem` represents either:

- a meaningful grouping node, such as Domain, Strand, Cluster, Topic, Section, or Category, or
- a concrete standard, competency, skill, or learning outcome.

### Required fields

| Field | Type | Notes |
|---|---|---|
| `identifier` | UUID | Generate a real UUID v4 |
| `uri` | URI | `urn:uuid:{identifier}`; canonical `https://…/ims/case/v1p1/{ObjectType}/{identifier}` for distribution |
| `fullStatement` | string | Preserve source wording |
| `lastChangeDateTime` | date-time | ISO 8601 |

### Recommended fields

| Field | Type | Notes |
|---|---|---|
| `CFDocumentURI` | `LinkURI` | Recommended compatibility field |
| `humanCodingScheme` | string | Preserve source codes like `2.OA.1`; when the source has none, synthesize a hierarchical, space-free code from tree position (see SKILL.md) — never an opaque machine ID |
| `listEnumeration` | string | Optional list marker, not a substitute for `sequenceNumber` |
| `abbreviatedStatement` | string | Short form of the statement |
| `alternativeLabel` | string | Alternate label if the source uses one |
| `CFItemType` | string | Text label like `Domain`, `Standard`, `Skill` |
| `CFItemTypeURI` | `LinkURI` | Preferred when matching definition exists |
| `educationLevel` | string[] | Prefer arrays |
| `language` | string | Usually inherited from the document |
| `conceptKeywords` | string[] | Free-text keywords |
| `conceptKeywordsURI` | `LinkURI` | Singular link, not an array in OpenSALT DTOs |
| `subject` | string[] | Prefer arrays |
| `subjectURI` | `LinkURI`[] | Must match defined `CFSubjects` if used |
| `notes` | string | Clarifications or source notes |
| `statusStartDate` | date or date-time | If stated |
| `statusEndDate` | date or date-time | If stated |
| `licenseURI` | `LinkURI` | If item-specific license exists |

### Mapping guidance

| Source clue | CASE field |
|---|---|
| Standard text / skill statement | `fullStatement` |
| Code / identifier / number | `humanCodingScheme` |
| Grade band / level | `educationLevel` |
| Heading label | `abbreviatedStatement` or `CFItemType` depending on role |
| Topic words / tags | `conceptKeywords` |
| Subject area | `subject` |

### Practical rules

- Do not create items for purely decorative headings.
- If the source only provides a short label, use that as `fullStatement`.
- Prefer one item per source statement unless the source clearly combines them as one unit.
- Keep grouping nodes when they carry real structural meaning.

## `CFAssociations`

Associations encode hierarchy and any additional relationships.

### Required fields

| Field | Type | Notes |
|---|---|---|
| `identifier` | UUID | Generate a real UUID v4 |
| `associationType` | enum or `ext:...` | Use defined CASE types unless the source truly needs an extension |
| `uri` | URI | `urn:uuid:{identifier}`; canonical `https://…/ims/case/v1p1/{ObjectType}/{identifier}` for distribution |
| `originNodeURI` | `LinkGenURI` | Source / child / origin side |
| `destinationNodeURI` | `LinkGenURI` | Target / parent / destination side |
| `lastChangeDateTime` | date-time | ISO 8601 |

### Recommended fields

| Field | Type | Notes |
|---|---|---|
| `CFDocumentURI` | `LinkURI` | Recommended compatibility field |
| `sequenceNumber` | integer | Strongly recommended for `isChildOf` |
| `CFAssociationGroupingURI` | `LinkURI` | Only if a grouping is defined |
| `notes` | string | Only when useful |

### Valid CASE association types

| Value | Meaning |
|---|---|
| `isChildOf` | Child to parent hierarchy |
| `isPeerOf` | Peer relationship |
| `isPartOf` | Part to whole |
| `exactMatchOf` | Semantic equivalence |
| `precedes` | Sequence or prerequisite |
| `isRelatedTo` | General related link |
| `replacedBy` | Superseded by |
| `exemplar` | Example resource or exemplar link |
| `hasSkillLevel` | Skill to level relationship |
| `isTranslationOf` | Translation relationship |

### Default hierarchy recipe

For document-to-framework conversion, use this pattern:

```json
{
  "associationType": "isChildOf",
  "originNodeURI": {
    "title": "Child Item",
    "identifier": "22222222-2222-4222-8222-222222222222",
    "uri": "urn:uuid:22222222-2222-4222-8222-222222222222"
  },
  "destinationNodeURI": {
    "title": "Parent Item Or Document",
    "identifier": "11111111-1111-4111-8111-111111111111",
    "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
  },
  "sequenceNumber": 1
}
```

### Strong rule

Unless the source explicitly states another relationship, generate only `isChildOf`.

## `CFDefinitions`

Use `CFDefinitions` for reusable vocabulary objects referenced elsewhere in the package.

```json
{
  "CFSubjects": [],
  "CFItemTypes": [],
  "CFConcepts": [],
  "CFLicenses": [],
  "CFAssociationGroupings": []
}
```

### `CFSubject`

Required:

- `identifier`
- `uri`
- `title`
- `hierarchyCode`
- `lastChangeDateTime`

Optional:

- `description`

Use for subjects referenced by `subjectURI`.

### `CFItemType`

Required:

- `identifier`
- `uri`
- `title`
- `description`
- `hierarchyCode`
- `lastChangeDateTime`

Optional:

- `typeCode`

Use for labels like `Domain`, `Cluster`, `Standard`, `Competency`, `Skill`, `Indicator`, `Objective`.

Important: `description` is required in the OpenAPI/schema model even though many summaries omit that fact.

### `CFConcept`

Required:

- `identifier`
- `uri`
- `title`
- `hierarchyCode`
- `lastChangeDateTime`

Optional:

- `keywords`
- `description`

Use only if you actually need linked concept vocabulary.

### `CFLicense`

Required:

- `identifier`
- `uri`
- `title`
- `licenseText`
- `lastChangeDateTime`

Optional:

- `description`

Use only when the source names a license worth preserving.

### `CFAssociationGrouping`

Required:

- `identifier`
- `uri`
- `title`
- `lastChangeDateTime`

Optional:

- `description`

Use only if you need named groups of associations.

## `CFRubrics`

`CFRubrics` are optional. Only generate them when the source actually contains rubric or proficiency information.

### `CFRubric`

Required:

- `identifier`
- `uri`
- `lastChangeDateTime`

Optional but usually useful:

- `title`
- `description`
- `CFRubricCriteria`

### `CFRubricCriterion`

Required:

- `identifier`
- `uri`
- `lastChangeDateTime`

Optional but commonly used:

- `category`
- `description`
- `CFItemURI`
- `weight`
- `position`
- `rubricId`
- `CFRubricCriterionLevels`

### `CFRubricCriterionLevel`

Required:

- `identifier`
- `uri`
- `lastChangeDateTime`

Optional but commonly used:

- `description`
- `quality`
- `score`
- `feedback`
- `position`
- `rubricCriterionId`

## Link Objects

### `LinkURI`

Use for typed references to defined objects.

```json
{
  "title": "Human readable title",
  "identifier": "11111111-1111-4111-8111-111111111111",
  "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
}
```

Used by:

- `CFPackageURI`
- `CFDocumentURI`
- `CFItemTypeURI`
- `subjectURI`
- `licenseURI`
- `CFAssociationGroupingURI`
- `CFItemURI`

### `LinkGenURI`

Use for `originNodeURI` and `destinationNodeURI` in associations.

```json
{
  "title": "Human readable title",
  "identifier": "11111111-1111-4111-8111-111111111111",
  "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
}
```

Optional field:

- `targetType`

Important OpenSALT/OpenAPI note:

- If `targetType` is present, the model expects `"CASE"` or an `ext:...` value.
- Do not use `"CFItem"` or `"CFDocument"` here.
- For internal package links, omitting `targetType` is the safest option.

## OpenSALT-Specific Notes

These details come from the actual DTOs, normalizers, and transformers in `core/src/`.

### Compatibility fields

OpenSALT exports and accepts these fields even though they are represented somewhat unusually in the validation schema:

- `CFDocument.CFPackageURI`
- `CFItems[].CFDocumentURI`
- `CFAssociations[].CFDocumentURI`

When generating a package for OpenSALT, include them.

### `conceptKeywordsURI` shape

OpenSALT handles `conceptKeywordsURI` as a single `LinkURI`, not an array.

### Import repair behavior

The importer tries to repair a few common issues, including:

- missing `fullStatement` when `alternativeLabel` or `abbreviatedStatement` exists
- malformed item URIs in known packages
- bad association type `RelatedTo` corrected to `isRelatedTo`
- invalid date formats in some real-world imports

Do not rely on those repairs. Generate clean data instead.

## Minimal Useful Example

```json
{
  "CFDocument": {
    "identifier": "11111111-1111-4111-8111-111111111111",
    "uri": "urn:uuid:11111111-1111-4111-8111-111111111111",
    "creator": "Issuing Organization",
    "title": "Framework Title",
    "lastChangeDateTime": "2026-03-25T00:00:00Z",
    "caseVersion": "1.1",
    "CFPackageURI": {
      "title": "Framework Title",
      "identifier": "11111111-1111-4111-8111-111111111111",
      "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
    }
  },
  "CFItems": [
    {
      "identifier": "22222222-2222-4222-8222-222222222222",
      "uri": "urn:uuid:22222222-2222-4222-8222-222222222222",
      "CFDocumentURI": {
        "title": "Framework Title",
        "identifier": "11111111-1111-4111-8111-111111111111",
        "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
      },
      "fullStatement": "Analyze how evidence supports a claim.",
      "humanCodingScheme": "ELA.1",
      "CFItemType": "Standard",
      "lastChangeDateTime": "2026-03-25T00:00:00Z"
    }
  ],
  "CFAssociations": [
    {
      "identifier": "33333333-3333-4333-8333-333333333333",
      "uri": "urn:uuid:33333333-3333-4333-8333-333333333333",
      "CFDocumentURI": {
        "title": "Framework Title",
        "identifier": "11111111-1111-4111-8111-111111111111",
        "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
      },
      "associationType": "isChildOf",
      "originNodeURI": {
        "title": "Analyze how evidence supports a claim.",
        "identifier": "22222222-2222-4222-8222-222222222222",
        "uri": "urn:uuid:22222222-2222-4222-8222-222222222222"
      },
      "destinationNodeURI": {
        "title": "Framework Title",
        "identifier": "11111111-1111-4111-8111-111111111111",
        "uri": "urn:uuid:11111111-1111-4111-8111-111111111111"
      },
      "sequenceNumber": 1,
      "lastChangeDateTime": "2026-03-25T00:00:00Z"
    }
  ]
}
```

## Final Preflight Checklist

Before emitting a generated package, verify:

- all UUIDs are unique
- all URIs match their identifiers
- every item has non-empty `fullStatement`
- every item has one parent
- all hierarchy links are represented with `isChildOf`
- ordering is preserved with `sequenceNumber`
- linked definitions actually exist
- item type definitions include `description`
- `targetType` is omitted or valid
- no non-framework boilerplate was turned into a `CFItem`
