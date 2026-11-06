# Quality control for a first-draft framework

Run the **full pass** once a framework has been first created (generated or converted), before it is delivered, uploaded, or published. Run the **delta pass** on each republish (last section).

Division of labor: the agent runs every mechanical check and writes a QC report; the **human** reviews the report and signs off. The validator proves structural conformance — it cannot judge content fidelity, hierarchy sanity at scale, or whether the framework is *right*. Do not deliver or publish a first draft without human sign-off.

## 1. Structural validation (the gate)

`python3 <skill>/scripts/validate_case_package.py <file> --strict --summary` — zero errors, every warning triaged or fixed. This proves the package is *importable*; everything below proves it is *good*.

## 2. Inventory and shape

`python3 <skill>/scripts/qc_inventory.py <file>` — read the report end to end. Flag:

- depth histogram inconsistent with the intended levels (e.g. micro-topics at two different depths)
- grouping types with no children (a `Domain` or `Age Band` with nothing under it)
- multi-parent items (valid CASE, but each occurrence must be intentional cross-listing)
- duplicate `fullStatement` values (often a source-extraction defect)
- identifier-convention mixing (item URIs split across `/uri/` and CASE spec spaces)
- field-coverage surprises (e.g. zero `conceptKeywords` when the source has tags; `educationLevel` gaps)

## 3. Content fidelity sampling

- Sample 5–10 items per `CFItemType` (more if the human asks) and compare `fullStatement`, `abbreviatedStatement`, and `notes` **verbatim** against the source material.
- Confirm no boilerplate, decorative headings, or license text became items, and that no whole source section is missing (walk source section headings against top-level items).
- Check `humanCodingScheme` values read as codes, not IDs; check `educationLevel` values match the source's grade/age bands.

## 4. Metadata and conventions

- Document metadata complete: `creator`, `publisher`, `officialSourceURL`, `version`, `adoptionStatus` (+ `statusStartDate`), `language`, `description`, license (`CFLicense` + `licenseURI`).
- Conventions recorded in `CFDocument.notes`: synthesized coding-scheme format, URI convention chosen, assumptions and ambiguities from the source.
- Subjects: subject-like top-level groupings mirrored into `CFDefinitions.CFSubjects` with `subjectURI` on descendants — or a documented reason not to.

## 5. Round-trip smoke test (when a target host is known)

Import with `POST /api/v1/packages`, fetch back with `GET /api/v1/packages/{documentIdentifier}`, compare item/association counts and identifiers, and sanity-read `/uri/p{documentIdentifier}.md`. For a test on a production host, leave the framework in `Private Draft` or delete the import afterward.

## The QC report

Deliver a short report with: the validator result; inventory highlights (counts, depth, duplicates, coverage); sampling findings with quoted diffs against the source; metadata gaps; and open questions. End with an explicit ask — "approve for delivery?" — and stop. Do not publish, upload, or hand off as final until the human approves.

## Delta pass on republish

Re-run validation and the inventory; diff item/association counts against the previous version; sample only changed or new items; confirm identifiers stayed stable (idempotent import) and that `version` and `lastChangeDateTime` moved. Anything the delta touches gets the full section 3 treatment.
