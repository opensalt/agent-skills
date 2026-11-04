# CASE 1.1 JSON Reference for OpenSALT Import

## Overview

This document is a practical reference for developers and LLMs generating CASE 1.1 JSON packages for import into OpenSALT. It covers every object type, required/optional fields, extension properties, and import-specific details — without the internal OpenSALT implementation details.

**CASE (Competencies and Academic Standards Exchange)** is an 1EdTech specification for representing and exchanging competency frameworks, academic standards, and related artifacts. OpenSALT supports importing CASE 1.1 JSON documents via its package API.

---

## Table of Contents

1. [Package Structure](#package-structure)
2. [CFDocument (Framework Metadata)](#cfdocument-framework-metadata)
3. [CFItems (Competency Items)](#cfitems-competency-items)
4. [OpenSALT Item Kinds](#opensalt-item-kinds)
5. [CFAssociations (Relationships)](#cfassociations-relationships)
6. [CFDefinitions (Supporting Objects)](#cfdefinitions-supporting-objects)
7. [CFRubrics](#cfrubrics)
8. [LinkURI and LinkGenURI](#linkuri-and-linkgenuri)
9. [Identifiers and URIs](#identifiers-and-uris)
10. [Complete Import Examples](#complete-import-examples)
11. [API Upload Guide](#api-upload-guide)

---

## Package Structure

A CASE 1.1 import package is a single JSON object with these top-level keys:

```json
{
  "CFDocument": { ... },
  "CFItems": [ ... ],
  "CFAssociations": [ ... ],
  "CFDefinitions": {
    "CFConcepts": [ ... ],
    "CFSubjects": [ ... ],
    "CFLicenses": [ ... ],
    "CFItemTypes": [ ... ],
    "CFAssociationGroupings": [ ... ]
  },
  "CFRubrics": [ ... ],
  "extensions": { ... }
}
```

| Field            | Type   | Required | Description                            |
| ---------------- | ------ | -------- | -------------------------------------- |
| `CFDocument`     | object | Yes      | Framework metadata                     |
| `CFItems`        | array  | No       | Competency items and specialized kinds |
| `CFAssociations` | array  | No       | Relationships between items            |
| `CFDefinitions`  | object | No       | Supporting definitions                 |
| `CFRubrics`      | array  | No       | Rubrics with criteria and levels       |
| `extensions`     | object | No       | Package-level extensions (optional)    |

---

## CFDocument (Framework Metadata)

The `CFDocument` object contains metadata about the entire framework.

### Fields

| Field                | Type                       | Required | Description                                                       |
| -------------------- | -------------------------- | -------- | ----------------------------------------------------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier for the document                                |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required) for the document                                   |
| `caseVersion`        | string                     | Yes      | Must be `"1.1"`                                                   |
| `frameworkType`      | string                     | No       | Type of framework, e.g. `"Competency Framework"`                  |
| `creator`            | string                     | Yes      | Creator of the document                                           |
| `title`              | string                     | Yes      | Title of the document                                             |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Timestamp of last change, e.g. `"2025-01-15T10:30:00+00:00"`      |
| `officialSourceURL`  | string (URI)               | No       | Official source URL                                               |
| `publisher`          | string                     | No       | Publisher name                                                    |
| `description`        | string                     | No       | Description of the document                                       |
| `subject`            | string or string[]         | No       | Subject(s) as plain strings                                       |
| `subjectURI`         | LinkURI[]                  | No       | Subject(s) as linked objects                                      |
| `language`           | string                     | No       | Language code (RFC 5646), e.g. `"en"`                             |
| `version`            | string                     | No       | Document version string                                           |
| `adoptionStatus`     | string                     | No       | CASE 1.1 recommends `"Draft"`, `"Pending Implementation"`, `"Implemented"`, `"Retired"`; OpenSALT adds `"Private Draft"`. Any string is accepted and stored as sent (recognized spellings canonicalized). `"Private Draft"` hides the framework from the public catalog; `"Implemented"` locks item edits; `"Retired"` locks all edits |
| `statusStartDate`    | string (date)              | No       | Date the status started, format `YYYY-MM-DD`                      |
| `statusEndDate`      | string (date)              | No       | Date the status ended, format `YYYY-MM-DD`                        |
| `licenseURI`         | LinkURI                    | No       | License reference                                                 |
| `notes`              | string                     | No       | Additional notes                                                  |
| `CFPackageURI`       | LinkURI                    | No       | Reference to the parent package                                   |
| `extensions`         | object                     | No       | Extension properties (for custom metadata)                        |

### Example

```json
{
  "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "caseVersion": "1.1",
  "frameworkType": "Competency Framework",
  "creator": "State Education Department",
  "title": "K-12 Mathematics Standards",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "officialSourceURL": "https://example.com/math-standards",
  "publisher": "State Education Department",
  "description": "Mathematics competency framework for grades K-12",
  "subject": ["Mathematics"],
  "subjectURI": [
    {
      "title": "Mathematics",
      "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ],
  "language": "en",
  "version": "2.0",
  "adoptionStatus": "Implemented",
  "statusStartDate": "2025-01-01",
  "licenseURI": {
    "title": "Creative Commons BY 4.0",
    "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901"
  },
  "notes": "Updated for 2025 academic year",
  "CFPackageURI": {
    "title": "K-12 Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFPackages/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  }
}
```

---

## CFItems (Competency Items)

Each `CFItem` represents a single competency, standard, or learning objective.

### Standard Fields

| Field                  | Type                       | Required | Description                                           |
| ---------------------- | -------------------------- | -------- | ----------------------------------------------------- |
| `identifier`           | UUID                       | Yes      | Unique identifier                                     |
| `uri`                  | string (URI)               | Yes      | URI (stored as sent; resolvability not required)                                        |
| `CFDocumentURI`        | LinkURI                    | Yes      | Reference to the parent document                      |
| `fullStatement`        | string                     | Yes      | Full text of the competency                           |
| `alternativeLabel`     | string                     | No       | Alternative label                                     |
| `CFItemType`           | string                     | No       | Item type name (e.g. `"Competency"`)                  |
| `CFItemTypeURI`        | LinkURI                    | No       | Item type reference                                   |
| `humanCodingScheme`    | string                     | No       | Human-readable code (e.g. `"MATH-7.ALG.1"`)           |
| `listEnumeration`      | string                     | No       | Enumeration in source                                 |
| `abbreviatedStatement` | string                     | No       | Shortened statement                                   |
| `conceptKeywords`      | string[]                   | No       | Concept keywords                                      |
| `conceptKeywordsURI`   | LinkURI                    | No       | Primary concept keyword URI                           |
| `notes`                | string                     | No       | Additional notes                                      |
| `subject`              | string or string[]         | No       | Subject(s)                                            |
| `subjectURI`           | LinkURI[]                  | No       | Subject(s) as linked objects                          |
| `language`             | string                     | No       | Language code                                         |
| `educationLevel`       | string or string[]         | No       | Education levels (e.g. `["Grade 7", "Grade 8"]`)      |
| `licenseURI`           | LinkURI                    | No       | License reference                                     |
| `statusStartDate`      | string (date)              | No       | Status start date, format `YYYY-MM-DD`                |
| `statusEndDate`        | string (date)              | No       | Status end date, format `YYYY-MM-DD`                  |
| `lastChangeDateTime`   | string (ISO 8601 datetime) | Yes      | Last change timestamp                                 |
| `extensions`           | object                     | No       | Extension properties (for item kinds and custom data) |

### Example

```json
{
  "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012",
  "CFDocumentURI": {
    "title": "K-12 Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "fullStatement": "Students will demonstrate the ability to solve linear equations with one variable.",
  "alternativeLabel": "Solve linear equations",
  "CFItemType": "Competency",
  "CFItemTypeURI": {
    "title": "Competency",
    "identifier": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFItemTypes/d4e5f6a7-b8c9-0123-defa-234567890123"
  },
  "humanCodingScheme": "MATH-7.ALG.1",
  "listEnumeration": "1",
  "abbreviatedStatement": "Solve 1-var linear equations",
  "conceptKeywords": ["algebra", "linear equations", "variables"],
  "conceptKeywordsURI": {
    "title": "Algebra",
    "identifier": "e5f6a7b8-c9d0-1234-efab-345678901234",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFConcepts/e5f6a7b8-c9d0-1234-efab-345678901234"
  },
  "notes": "Includes equations with rational coefficients",
  "subject": ["Mathematics"],
  "subjectURI": [
    {
      "title": "Mathematics",
      "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ],
  "language": "en",
  "educationLevel": ["Grade 7", "Grade 8"],
  "licenseURI": {
    "title": "Creative Commons BY 4.0",
    "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901"
  },
  "statusStartDate": "2025-01-01",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00"
}
```

---

## OpenSALT Item Kinds

OpenSALT extends the standard `CFItem` with specialized **item kinds**. Each kind is still a valid `CFItem` — it just sets `extensions.salt:type` and adds kind-specific extension properties.

### How to set a kind

Add `salt:type` to the item's `extensions` object:

```json
"extensions": {
  "salt:type": "course"
}
```

Set it to one of the kind names in the table below, or omit it for a standard competency item.

### Kind Reference

| `salt:type` value | What it represents             | Extension keys                                                                                                                        |
| ----------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| *(omit)*          | Standard competency item       | —                                                                                                                                     |
| `job`             | Occupation / job               | `ceterms:subjectWebpage`                                                                                                              |
| `course`          | Learning course                | `ceterms:subjectWebpage`, `ceterms:deliveryType`                                                                                      |
| `assessment`      | Assessment instrument          | `ceterms:subjectWebpage`, `ceterms:deliveryType`                                                                                      |
| `credential`      | Open Badges 3.x credential     | `ob3`                                                                                                                                 |
| `organization`    | Organization                   | `ceterms:agentType`, `ceterms:subjectWebpage`, `ceterms:image`, `ceterms:jurisdiction`, `sdo:legalName`, `ceterms:ctid`, `salt:rorId` |
| `identifier`      | External URI identifier        | `salt:idType`                                                                                                                         |
| `public_key`      | Public cryptographic key (JWK) | `salt:kid`                                                                                                                            |

### Standard Field Mappings

Each kind maps its data onto standard CASE fields plus extension properties:

| Standard CASE field    | Used by kinds as…                                 |
| ---------------------- | ------------------------------------------------- |
| `abbreviatedStatement` | Short name / title / label / key id               |
| `fullStatement`        | Description / serialized payload                  |
| `humanCodingScheme`    | Coded notation                                    |
| `language`             | `inLanguage`                                      |
| `conceptKeywords`      | Keywords / tags                                   |
| `uri`                  | The identifier itself (for the `identifier` kind) |

### Job (`salt:type: "job"`)

An occupation / job description.

| Extension key            | Type         | Description         |
| ------------------------ | ------------ | ------------------- |
| `ceterms:subjectWebpage` | string (URL) | URL of the job page |

Standard mapping: `abbreviatedStatement` = title, `fullStatement` = description, `humanCodingScheme` = coded notation, `conceptKeywords` = keywords.

### Course (`salt:type: "course"`)

A learning course.

| Extension key            | Type         | Description                                    |
| ------------------------ | ------------ | ---------------------------------------------- |
| `ceterms:subjectWebpage` | string (URL) | URL of the course page                         |
| `ceterms:deliveryType`   | string       | Delivery type (e.g. `"online"`, `"in-person"`) |

Standard mapping: `abbreviatedStatement` = name, `fullStatement` = description, `humanCodingScheme` = coded notation, `language` = inLanguage.

### Assessment (`salt:type: "assessment"`)

An assessment instrument.

| Extension key            | Type         | Description                               |
| ------------------------ | ------------ | ----------------------------------------- |
| `ceterms:subjectWebpage` | string (URL) | URL of the assessment page                |
| `ceterms:deliveryType`   | string       | Delivery type (e.g. `"online proctored"`) |

Standard mapping: `abbreviatedStatement` = name, `fullStatement` = description, `language` = inLanguage, `conceptKeywords` = keywords.

### Credential (`salt:type: "credential"`)

An Open Badges 3.x credential. The entire credential is carried in a single extension property.

| Extension key | Type          | Description                                              |
| ------------- | ------------- | -------------------------------------------------------- |
| `ob3`         | string (JSON) | The Open Badges 3.x credential document as a JSON string |

Provide `ob3` as a string whose content is a JSON object (escape inner quotes). On import, OpenSALT also copies these values out of the `ob3` object into standard CASE fields for searchability:

- `abbreviatedStatement` ← `ob3.name`
- `fullStatement` ← `ob3.description`
- `humanCodingScheme` ← `ob3.humanCode`
- `language` ← `ob3.inLanguage`
- `conceptKeywords` ← `ob3.tag`

### Organization (`salt:type: "organization"`)

An organization described using CTDL and schema.org terms.

| Extension key            | Type         | Description                            |
| ------------------------ | ------------ | -------------------------------------- |
| `ceterms:agentType`      | string       | Agent type (e.g. `"GovernmentAgency"`) |
| `ceterms:subjectWebpage` | string (URL) | Official webpage URL                   |
| `ceterms:image`          | string (URL) | Logo URL                               |
| `ceterms:jurisdiction`   | string       | Jurisdiction (e.g. `"US-CA"`)          |
| `sdo:legalName`          | string       | Legal name                             |
| `ceterms:ctid`           | string       | Credential Engine CTID                 |
| `salt:rorId`             | string (URL) | ROR identifier                         |

Standard mapping: `abbreviatedStatement` = name, `fullStatement` = description.

### Identifier (`salt:type: "identifier"`)

An external identifier expressed as a URI.

| Extension key | Type   | Description                             |
| ------------- | ------ | --------------------------------------- |
| `salt:idType` | string | Type of identifier (e.g. `"canonical"`) |

Standard mapping: `abbreviatedStatement` = the identifier (a URI), `fullStatement` = description.

> **Note:** If the identifier value matches a URI scheme pattern (`scheme:...`), OpenSALT also sets the item's top-level `uri` to that value.

### Public Key (`salt:type: "public_key"`)

A public cryptographic key represented as a JWK.

| Extension key | Type   | Description                       |
| ------------- | ------ | --------------------------------- |
| `salt:kid`    | string | Key format type (default `"jwk"`) |

Standard mapping: `abbreviatedStatement` = key id (`kid`), `fullStatement` = the JWK serialized as a JSON string.

> **Note:** On import, OpenSALT normalizes the key (from JWK JSON or PEM/DER) and re-serializes it as a canonical JWK. If no `kid` is present, the SHA-256 JWK thumbprint is computed and used.

### Kind Examples

**Course:**
```json
{
  "identifier": "11aa22bb-33cc-4455-bbee-678901abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/11aa22bb-33cc-4455-bbee-678901abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "fullStatement": "Introduction to the study of algebra, functions, and modeling.",
  "abbreviatedStatement": "Intro to Algebra",
  "humanCodingScheme": "MATH-101",
  "language": "en",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "course",
    "ceterms:subjectWebpage": "https://example.edu/courses/math-101",
    "ceterms:deliveryType": "online"
  }
}
```

**Credential:**
```json
{
  "identifier": "22bb33cc-44dd-5566-aaff-789012abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/22bb33cc-44dd-5566-aaff-789012abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "abbreviatedStatement": "Algebra I Proficiency",
  "fullStatement": "Demonstrates mastery of introductory algebra.",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "credential",
    "ob3": "{\"name\":\"Algebra I Proficiency\",\"description\":\"Demonstrates mastery of introductory algebra.\",\"humanCode\":\"ALG-1\",\"inLanguage\":\"en\",\"tag\":[\"algebra\",\"math\"]}"
  }
}
```

**Job:**
```json
{
  "identifier": "33cc44dd-55ee-6677-bbcc-890123abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/33cc44dd-55ee-6677-bbcc-890123abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "abbreviatedStatement": "Mathematics Teacher",
  "fullStatement": "Teaches mathematics courses at the secondary level.",
  "humanCodingScheme": "SOC-25-2021",
  "conceptKeywords": ["teaching", "mathematics", "secondary education"],
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "job",
    "ceterms:subjectWebpage": "https://example.edu/careers/math-teacher"
  }
}
```

**Organization:**
```json
{
  "identifier": "55ee66ff-77aa-8899-ddee-012345abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/55ee66ff-77aa-8899-ddee-012345abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "abbreviatedStatement": "State Education Department",
  "fullStatement": "The state agency responsible for K-12 education standards.",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "organization",
    "ceterms:agentType": "GovernmentAgency",
    "ceterms:subjectWebpage": "https://example.gov/education",
    "ceterms:image": "https://example.gov/education/logo.png",
    "ceterms:jurisdiction": "US-CA",
    "sdo:legalName": "California Department of Education",
    "ceterms:ctid": "ce-12345678-1234-1234-1234-123456789abc",
    "salt:rorId": "https://ror.org/012345678"
  }
}
```

**Identifier:**
```json
{
  "identifier": "66ff77aa-88bb-9900-eeff-123456abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/66ff77aa-88bb-9900-eeff-123456abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "abbreviatedStatement": "https://example.org/standards/math/algebra",
  "fullStatement": "Canonical URI for the Algebra competency framework.",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "identifier",
    "salt:idType": "canonical"
  }
}
```

**Public Key:**
```json
{
  "identifier": "77aa88bb-99cc-0011-ffaa-234567abcdef",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/77aa88bb-99cc-0011-ffaa-234567abcdef",
  "CFDocumentURI": {
    "title": "Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "abbreviatedStatement": "a1b2c3d4e5f6g7h8i9j0",
  "fullStatement": "{\"kty\":\"RSA\",\"n\":\"...\",\"e\":\"AQAB\",\"kid\":\"a1b2c3d4e5f6g7h8i9j0\"}",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "extensions": {
    "salt:type": "public_key",
    "salt:kid": "jwk"
  }
}
```

> **`salt:type` vs `CFItemType`:** The OpenSALT **kind** (`salt:type`) and the CASE **item type** (`CFItemType` / `CFItemTypeURI`) are independent. A specialized item may also carry a `CFItemType`, but they are not required to correspond.

---

## CFAssociations (Relationships)

Each `CFAssociation` represents a relationship between two items (or between an item and a document).

### Fields

| Field                      | Type                       | Required | Description                      |
| -------------------------- | -------------------------- | -------- | -------------------------------- |
| `identifier`               | UUID                       | Yes      | Unique identifier                |
| `uri`                      | string (URI)               | Yes      | URI (stored as sent; resolvability not required)                   |
| `CFDocumentURI`            | LinkURI                    | Yes      | Reference to the parent document |
| `lastChangeDateTime`       | string (ISO 8601 datetime) | Yes      | Last change timestamp            |
| `sequenceNumber`           | integer                    | No       | Ordering for child items         |
| `CFAssociationGroupingURI` | LinkURI                    | No       | Association grouping reference   |
| `originNodeURI`            | LinkGenURI                 | Yes      | Origin node reference            |
| `associationType`          | string                     | Yes      | Type of relationship             |
| `destinationNodeURI`       | LinkGenURI                 | Yes      | Destination node reference       |
| `notes`                    | string                     | No       | Annotation                       |
| `extensions`               | object                     | No       | Extension properties             |

### Association Types

| Type              | Description                      |
| ----------------- | -------------------------------- |
| `isChildOf`       | Parent-child relationship        |
| `exactMatchOf`    | Exact match (symmetric)          |
| `isRelatedTo`     | General relationship (symmetric) |
| `isPartOf`        | Part-whole relationship          |
| `replacedBy`      | Replacement relationship         |
| `precedes`        | Sequential relationship          |
| `hasSkillLevel`   | Skill level relationship         |
| `isPeerOf`        | Peer relationship (symmetric)    |
| `exemplar`        | Exemplar relationship            |
| `isTranslationOf` | Translation relationship         |

You can also use extension types matching the pattern `ext:[a-zA-Z0-9._-]+`.

### Example

```json
{
  "identifier": "f6a7b8c9-d0e1-2345-fabc-456789012345",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFAssociations/f6a7b8c9-d0e1-2345-fabc-456789012345",
  "CFDocumentURI": {
    "title": "K-12 Mathematics Standards",
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
  },
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "sequenceNumber": 1,
  "originNodeURI": {
    "title": "Solve linear equations",
    "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012",
    "targetType": "CASE"
  },
  "associationType": "isChildOf",
  "destinationNodeURI": {
    "title": "Algebra Standards",
    "identifier": "a7b8c9d0-e1f2-3456-abcd-567890123456",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/a7b8c9d0-e1f2-3456-abcd-567890123456",
    "targetType": "CASE"
  },
  "notes": "Primary algebra competency",
  "extensions": {
    "subtype": "curriculum"
  }
}
```

---

## CFDefinitions (Supporting Objects)

The `CFDefinitions` object contains arrays of supporting definition objects.

### CFSubject

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `title`              | string                     | Yes      | Subject name          |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `description`        | string                     | No       | Description           |
| `hierarchyCode`      | string                     | Yes      | Hierarchy code        |
| `extensions`         | object                     | No       | Extension properties  |

### CFLicense

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `title`              | string                     | Yes      | License name          |
| `description`        | string                     | No       | Description           |
| `licenseText`        | string                     | Yes      | Full license text     |
| `extensions`         | object                     | No       | Extension properties  |

### CFItemType

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `title`              | string                     | Yes      | Item type name        |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `description`        | string                     | Yes      | Description           |
| `typeCode`           | string                     | No       | Type code             |
| `hierarchyCode`      | string                     | Yes      | Hierarchy code        |
| `extensions`         | object                     | No       | Extension properties  |

### CFConcept

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `title`              | string                     | Yes      | Concept name          |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `description`        | string                     | No       | Description           |
| `hierarchyCode`      | string                     | Yes      | Hierarchy code        |
| `keywords`           | string                     | No       | Keywords              |
| `extensions`         | object                     | No       | Extension properties  |

### CFAssociationGrouping

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `title`              | string                     | Yes      | Grouping name         |
| `description`        | string                     | No       | Description           |
| `extensions`         | object                     | No       | Extension properties  |

---

## CFRubrics

Rubrics provide evaluation criteria for competency items.

### CFRubric

| Field                | Type                       | Required | Description           |
| -------------------- | -------------------------- | -------- | --------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier     |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)        |
| `title`              | string                     | No       | Rubric title          |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp |
| `description`        | string                     | No       | Description           |
| `CFRubricCriteria`   | array                      | No       | Array of criteria     |
| `extensions`         | object                     | No       | Extension properties  |

### CFRubricCriterion

| Field                     | Type                       | Required | Description              |
| ------------------------- | -------------------------- | -------- | ------------------------ |
| `identifier`              | UUID                       | Yes      | Unique identifier        |
| `uri`                     | string (URI)               | Yes      | URI (stored as sent; resolvability not required)           |
| `lastChangeDateTime`      | string (ISO 8601 datetime) | Yes      | Last change timestamp    |
| `CFItemURI`               | LinkURI                    | No       | Associated item          |
| `rubricId`                | UUID                       | No       | Parent rubric identifier |
| `category`                | string                     | No       | Criterion category       |
| `description`             | string                     | No       | Description              |
| `position`                | integer                    | No       | Position order           |
| `weight`                  | number                     | No       | Weight factor            |
| `CFRubricCriterionLevels` | array                      | No       | Performance levels       |
| `extensions`              | object                     | No       | Extension properties     |

### CFRubricCriterionLevel

| Field                | Type                       | Required | Description                 |
| -------------------- | -------------------------- | -------- | --------------------------- |
| `identifier`         | UUID                       | Yes      | Unique identifier           |
| `uri`                | string (URI)               | Yes      | URI (stored as sent; resolvability not required)              |
| `rubricCriterionId`  | UUID                       | No       | Parent criterion identifier |
| `lastChangeDateTime` | string (ISO 8601 datetime) | Yes      | Last change timestamp       |
| `description`        | string                     | No       | Level description           |
| `feedback`           | string                     | No       | Feedback text               |
| `quality`            | string                     | No       | Quality label               |
| `score`              | number                     | No       | Numeric score               |
| `position`           | integer                    | No       | Position order              |
| `extensions`         | object                     | No       | Extension properties        |

### Example

```json
{
  "identifier": "d7e8f9a0-b1c2-3456-cdef-678901234567",
  "uri": "https://opensalt.example.com/ims/case/v1p1/CFRubrics/d7e8f9a0-b1c2-3456-cdef-678901234567",
  "title": "Linear Equations Rubric",
  "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
  "description": "Assessment rubric for linear equations competency",
  "CFRubricCriteria": [
    {
      "identifier": "e8f9a0b1-c2d3-4567-defa-789012345678",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFRubricCriteria/e8f9a0b1-c2d3-4567-defa-789012345678",
      "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
      "CFItemURI": {
        "title": "Solve linear equations",
        "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012"
      },
      "rubricId": "d7e8f9a0-b1c2-3456-cdef-678901234567",
      "category": "Problem Solving",
      "description": "Ability to solve linear equations",
      "position": 1,
      "weight": 1.0,
      "CFRubricCriterionLevels": [
        {
          "identifier": "f9a0b1c2-d3e4-5678-efab-890123456789",
          "uri": "https://opensalt.example.com/ims/case/v1p1/CFRubricCriterionLevels/f9a0b1c2-d3e4-5678-efab-890123456789",
          "rubricCriterionId": "e8f9a0b1-c2d3-4567-defa-789012345678",
          "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
          "description": "Exemplary",
          "quality": "Exceeds Expectations",
          "score": 4.0,
          "feedback": "Demonstrates complete understanding with no errors",
          "position": 1
        },
        {
          "identifier": "a0b1c2d3-e4f5-6789-fabc-901234567890",
          "uri": "https://opensalt.example.com/ims/case/v1p1/CFRubricCriterionLevels/a0b1c2d3-e4f5-6789-fabc-901234567890",
          "rubricCriterionId": "e8f9a0b1-c2d3-4567-defa-789012345678",
          "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
          "description": "Proficient",
          "quality": "Meets Expectations",
          "score": 3.0,
          "feedback": "Demonstrates understanding with minor errors",
          "position": 2
        }
      ]
    }
  ]
}
```

---

## LinkURI and LinkGenURI

### LinkURI

A standard reference structure used throughout CASE documents:

| Field        | Type         | Required | Description          |
| ------------ | ------------ | -------- | -------------------- |
| `title`      | string       | Yes      | Human-readable title |
| `identifier` | UUID         | Yes      | Unique identifier    |
| `uri`        | string (URI) | Yes      | URI (stored as sent; resolvability not required)       |

### LinkGenURI

Extends `LinkURI` with an additional field:

| Field        | Type         | Required | Description                                              |
| ------------ | ------------ | -------- | -------------------------------------------------------- |
| `title`      | string       | Yes      | Human-readable title                                     |
| `identifier` | string       | Yes      | Identifier (UUID for CASE objects)                       |
| `uri`        | string (URI) | Yes      | URI (stored as sent; resolvability not required)                                           |
| `targetType` | string       | No       | `"CASE"` for CASE objects, or `"ext:..."` for extensions |

`LinkGenURI` is used for `originNodeURI` and `destinationNodeURI` on associations.

---

## Identifiers and URIs

### Identifier Format

- Must be a valid lowercase UUID
- Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (8-4-4-4-12 hex digits)
- Example: `f1a2b3c4-d5e6-7890-abcd-ef1234567890`

### URI Construction

OpenSALT constructs URIs using the pattern:
```
https://{host}/ims/case/v1p1/{ObjectType}/{identifier}
```

Where `ObjectType` is one of: `CFDocuments`, `CFItems`, `CFAssociations`, `CFSubjects`, `CFLicenses`, `CFItemTypes`, `CFConcepts`, `CFAssociationGroupings`, `CFRubrics`, `CFRubricCriteria`, `CFRubricCriterionLevels`, `CFPackages`.

### URIs are stored as sent

CASE requires `uri` on each item and on the document. The value you send is stored; it does not have to be a URL the server can resolve. Following the canonical pattern above still matters for consumers that dereference URIs.

### Local URIs

For newly created objects before being persisted, OpenSALT uses:
```
local:{identifier}
```

---

## Complete Import Examples

### Minimal Package

```json
{
  "CFDocument": {
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "caseVersion": "1.1",
    "creator": "Example Organization",
    "title": "Sample Framework",
    "lastChangeDateTime": "2025-01-15T10:30:00+00:00"
  },
  "CFItems": [
    {
      "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012",
      "CFDocumentURI": {
        "title": "Sample Framework",
        "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
      },
      "fullStatement": "Sample competency statement",
      "lastChangeDateTime": "2025-01-15T10:30:00+00:00"
    }
  ]
}
```

### Full Package with All Object Types

```json
{
  "CFDocument": {
    "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890",
    "caseVersion": "1.1",
    "frameworkType": "Competency Framework",
    "creator": "State Education Department",
    "title": "Mathematics Standards",
    "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
    "officialSourceURL": "https://example.com/math-standards",
    "publisher": "State Education Department",
    "description": "K-12 Mathematics Standards",
    "subject": ["Mathematics"],
    "subjectURI": [
      {
        "title": "Mathematics",
        "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      }
    ],
    "language": "en",
    "version": "1.0",
    "adoptionStatus": "Implemented",
    "statusStartDate": "2025-01-01",
    "licenseURI": {
      "title": "Creative Commons BY 4.0",
      "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901"
    },
    "CFPackageURI": {
      "title": "Mathematics Standards",
      "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFPackages/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
    }
  },
  "CFItems": [
    {
      "identifier": "a7b8c9d0-e1f2-3456-abcd-567890123456",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/a7b8c9d0-e1f2-3456-abcd-567890123456",
      "CFDocumentURI": {
        "title": "Mathematics Standards",
        "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
      },
      "fullStatement": "Understand and apply algebraic concepts",
      "CFItemType": "Competency",
      "CFItemTypeURI": {
        "title": "Competency",
        "identifier": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItemTypes/d4e5f6a7-b8c9-0123-defa-234567890123"
      },
      "humanCodingScheme": "MATH-ALG",
      "abbreviatedStatement": "Algebraic concepts",
      "subject": ["Mathematics"],
      "subjectURI": [
        {
          "title": "Mathematics",
          "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        }
      ],
      "language": "en",
      "educationLevel": ["Grade 6", "Grade 7", "Grade 8"],
      "licenseURI": {
        "title": "Creative Commons BY 4.0",
        "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901"
      },
      "statusStartDate": "2025-01-01",
      "lastChangeDateTime": "2025-01-15T10:30:00+00:00"
    },
    {
      "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012",
      "CFDocumentURI": {
        "title": "Mathematics Standards",
        "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
      },
      "fullStatement": "Solve linear equations with one variable",
      "CFItemType": "Competency",
      "CFItemTypeURI": {
        "title": "Competency",
        "identifier": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItemTypes/d4e5f6a7-b8c9-0123-defa-234567890123"
      },
      "humanCodingScheme": "MATH-7.ALG.1",
      "listEnumeration": "1",
      "abbreviatedStatement": "Solve linear equations",
      "conceptKeywords": ["algebra", "linear equations"],
      "conceptKeywordsURI": {
        "title": "Algebra",
        "identifier": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFConcepts/e5f6a7b8-c9d0-1234-efab-345678901234"
      },
      "subject": ["Mathematics"],
      "subjectURI": [
        {
          "title": "Mathematics",
          "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        }
      ],
      "language": "en",
      "educationLevel": ["Grade 7"],
      "licenseURI": {
        "title": "Creative Commons BY 4.0",
        "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901"
      },
      "statusStartDate": "2025-01-01",
      "lastChangeDateTime": "2025-01-15T10:30:00+00:00"
    }
  ],
  "CFAssociations": [
    {
      "identifier": "f6a7b8c9-d0e1-2345-fabc-456789012345",
      "uri": "https://opensalt.example.com/ims/case/v1p1/CFAssociations/f6a7b8c9-d0e1-2345-fabc-456789012345",
      "CFDocumentURI": {
        "title": "Mathematics Standards",
        "identifier": "f1a2b3c4-d5e6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFDocuments/f1a2b3c4-d5e6-7890-abcd-ef1234567890"
      },
      "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
      "sequenceNumber": 1,
      "originNodeURI": {
        "title": "Solve linear equations",
        "identifier": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/c3d4e5f6-a7b8-9012-cdef-123456789012",
        "targetType": "CASE"
      },
      "associationType": "isChildOf",
      "destinationNodeURI": {
        "title": "Algebraic concepts",
        "identifier": "a7b8c9d0-e1f2-3456-abcd-567890123456",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItems/a7b8c9d0-e1f2-3456-abcd-567890123456",
        "targetType": "CASE"
      },
      "notes": "Core algebra competency",
      "extensions": {
        "subtype": "curriculum"
      }
    }
  ],
  "CFDefinitions": {
    "CFConcepts": [
      {
        "identifier": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFConcepts/e5f6a7b8-c9d0-1234-efab-345678901234",
        "title": "Algebra",
        "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
        "description": "Branch of mathematics",
        "hierarchyCode": "MATH.ALG",
        "keywords": "algebra"
      }
    ],
    "CFSubjects": [
      {
        "identifier": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFSubjects/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Mathematics",
        "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
        "description": "Mathematics subject area",
        "hierarchyCode": "MATH"
      }
    ],
    "CFLicenses": [
      {
        "identifier": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFLicenses/b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
        "title": "Creative Commons Attribution 4.0 International",
        "description": "CC BY 4.0",
        "licenseText": "This work is licensed under a Creative Commons Attribution 4.0 International License."
      }
    ],
    "CFItemTypes": [
      {
        "identifier": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "uri": "https://opensalt.example.com/ims/case/v1p1/CFItemTypes/d4e5f6a7-b8c9-0123-defa-234567890123",
        "title": "Competency",
        "lastChangeDateTime": "2025-01-15T10:30:00+00:00",
        "description": "A competency statement",
        "typeCode": "competency",
        "hierarchyCode": "COMP"
      }
    ]
  }
}
```

---

## API Upload Guide

Uploading, authentication, publication status, and reading content back are documented in [registry-api.md](registry-api.md) (bundled with this skill). In brief:

- `POST /api/v1/packages` imports a CFPackage; `PUT /api/v1/packages/{documentIdentifier}` replaces a framework (send the same client-generated identifiers — idempotent). Writes need a Bearer token (created by a person at `/account/tokens`) and the Editor role.
- Writes send `Accept: application/json`; success answers `201` with an empty body and a `Location` header; validation failures return JSON whose `detail` lists the problems (nothing is silently fixed).
- There is no publish endpoint: `adoptionStatus` ships in the package or is set via `PUT /api/v1/documents/{documentIdentifier}`. `Private Draft` hides the framework from the catalog; `Implemented` locks item edits; `Retired` locks all edits.

---

*This document reflects OpenSALT's CASE 1.1 import format as of 2026, updated against the host registry's current LLM documentation (`core/public/llms/`). Registry API changes (auth, package writes, publication status) are tracked in the bundled [registry-api.md](registry-api.md). For the full CASE specification, see the [1EdTech CASE 1.1 spec](https://www.imsglobal.org/spec/case/v1p1).*
