# OpenSALT Registry API (2026)

Condensed from the host's own LLM documentation (`core/public/llms/*.md`, current as of 2026-11). The governing rule: **prefer CASE and `/uri/` for reading published content; use `/api/v1` for authenticated create and update. Never treat the HTML UI or `/framework/editor/` as an integration API.**

## Reading published content (no token needed)

CASE 1.1 base path: `/ims/case/v1p1` (v1.0: `/ims/case/v1p0` — prefer v1.1; the two serializations differ). These routes are read-only `GET`.

| Resource | Path |
|---|---|
| Catalog | `GET /ims/case/v1p1/CFDocuments` — `limit` (default 100), `offset`, `sort`, `orderBy`; `X-Total-Count` header |
| Full package | `GET /ims/case/v1p1/CFPackages/{documentIdentifier}` (`?download=1` forces an attachment) |
| Document / item / association | `GET .../CFDocuments/{id}` · `.../CFItems/{id}` · `.../CFAssociations/{id}` |
| Associations for an item | `GET .../CFItemAssociations/{id}` (also accepts `.../CFItems/{id}/associations`) |
| Definitions | `.../CFSubjects/{id}` · `.../CFLicenses/{id}` · `.../CFItemTypes/{id}` · `.../CFConcepts/{id}` · `.../CFAssociationGroupings/{id}` |
| Rubrics | `.../CFRubrics/{id}` · `.../CFRubricCriteria/{id}` · `.../CFRubricCriterionLevels/{id}` |
| Related documents | `GET .../CFDocuments/{id}/related` |

Notes:

- Paths take **no** `.json` suffix; send `Accept: application/json`. Identifiers are UUIDs.
- Successful GETs send `ETag`, `Last-Modified`, and a 60 s public cache max-age — repeat with `If-None-Match` / `If-Modified-Since` for `304 Not Modified`.
- The catalog hides `Private Draft` frameworks and non-visible mirrored frameworks from anonymous callers; a framework absent from the catalog can still be fetched by UUID if known. Direct fetch by UUID is not filtered like the catalog — an unlisted UUID is not secret.
- Item-association lists omit associations pointing at private-draft documents the caller cannot see; check both reads with the same credentials before treating a link as missing.
- All read prefixes (`/ims/case/`, `/uri/`) and `/api/v1/` are CORS-enabled with wildcard origins.

### Markdown and other representations via `/uri/`

Content-negotiated view of any object that has an identifier:

| Request | Returns |
|---|---|
| `/uri/{identifier}.md` | One object as markdown (preferred for agents) |
| `/uri/p{documentIdentifier}.md` | Whole framework as markdown (`p` + document UUID) |
| `/uri/{frameworkIdentifier}/{identifier}` | Object scoped to a framework |
| Suffixes | `.json`, `.jsonld`, `.html`, `.csv`; NDJSON via `Accept: application/x-ndjson` |

- Always send `Accept` **or** use a path suffix — with neither, the server answers `300 Multiple Choices` listing alternates.
- Markdown shape: YAML front matter (identity, owning framework, `title`, `lastChangeDateTime`, `itemType`, `humanCodingScheme`, `language`, simple `extensions`) then headings. `kind` is the item kind (`credential`, `course`, `job`, `organization`, `assessment`, …); `itemType` is the framework's own label. Associations are grouped by relationship type; incoming ones are labeled `(incoming)`.
- Package markdown is large: ~1–2 MB for a ~1,000-item framework. Fetch a single item when you only need one statement.

### MCP server (read-only)

Point an MCP client at `/_mcp` on the origin (HTTP transport). No auth; serves public content only. Tools: `opensalt_list_documents`, `opensalt_get_document`, `opensalt_list_items`, `opensalt_get_item`, `opensalt_search_related_items`. Resources: `opensalt://documents`, `opensalt://items/recent`. **No writes over MCP.**

## Writing frameworks (authenticated `/api/v1`)

Machine-readable spec: `GET /api/v1/doc.json` (Swagger UI at `/api/v1/doc`). Security scheme name in the spec: `Bearer`.

### Tokens and roles

- A person creates tokens in the browser at `/account/tokens`; send `Authorization: Bearer <token>`. Agents never scrape `/login`.
- Token scopes chosen at creation: **read**, **crosswalk**, **write**. Write modes: `none`, `all`, `sandbox` (frameworks the token creates), `documents` (+ `write.frameworks` list; optionally also sandbox). `GET /api/v1/token` describes the token on the request (never returns the secret).
- Writes need a signed-in user with the **Editor** role; the framework must not be a mirrored copy; the caller must have created it, been granted access, or belong to its organization.
- `401` invalid/missing token · `403` account or token not allowed · `404` unknown identifier.

### Endpoints

| Method | Path | Effect |
|---|---|---|
| `POST` | `/api/v1/packages` | Import a CFPackage — creates the framework (Editor) |
| `PUT` | `/api/v1/packages/{documentIdentifier}` | Replace a framework from a CFPackage (Editor) |
| `DELETE` | `/api/v1/packages/{documentIdentifier}` | Delete the framework (Editor) |
| `GET` | `/api/v1/packages/{documentIdentifier}` | Package JSON (public) |
| `POST` / `PUT` | `/api/v1/documents[/{documentIdentifier}]` | Create / replace document metadata |
| `GET` | `/api/v1/documents` | Paginated, filterable application list (catalog rules apply) |
| `POST` | `/api/v1/packages/{documentIdentifier}/items` and `/associations` | Create a single item/association |
| `GET` `PUT` `DELETE` | `.../items/{itemIdentifier}` · `.../associations/{associationIdentifier}` | Manage a single object |
| `GET` | `/api/v1/token` | Describe the presented token |
| `POST` | `/api/v1/articulations/evaluate` | Evaluate sending courses against articulation packages (institutions matched via identifier/uri/extension keys on organization items; courses via identifier/uri/courseCode/extension keys) |

### Write mechanics

- Send `Accept: application/json` on writes. `POST`/`PUT` of packages answer **`201` with an empty body**; the `Location` header holds the package URL.
- Validation failures return JSON whose `detail` lists what is wrong; several missing required properties are listed together. Do not invent properties the schema does not list.
- **Idempotent imports**: generate identifiers on the client (e.g. UUID version 5 over a stable key) and send them in the package. `POST` creates; a later `PUT /api/v1/packages/{documentIdentifier}` with those same identifiers replaces it. Items and associations in other packages may reference those identifiers. There is no get-or-create call.
- `POST` of a single item or association may omit `identifier` and `uri` — the server assigns both. Send `identifier` when a later replace must target the same id.
- `CFItemType` on an item is a label kept for the editor — it is **not** preserved as the item type on export. Declare types in `CFDefinitions.CFItemTypes` (each needs `identifier`, `uri`, `title`, `hierarchyCode`, `lastChangeDateTime`) and set the item's `CFItemTypeURI`.
- `uri` values are stored as sent; they do not have to be URLs the server can resolve.

### Publication status

- CASE 1.1 recommends `Draft`, `Pending Implementation`, `Implemented`, `Retired`; OpenSALT additionally uses `Private Draft`. Legacy CASE 1.0 `Adopted` / `Deprecated` are kept as sent and follow the rules of the values that replaced them (`Implemented` / `Retired`). Recognized spellings are stored canonically regardless of case; **any other value (including `Official` or `Final`) is stored as sent**.
- `Private Draft` is the only status hidden from the anonymous catalog (and from `GET /api/v1/documents` for callers who cannot see it). Every other status, including empty, is listed.
- `Implemented` (and stored `Adopted`): **item edits locked, association edits allowed**. `Retired` (and stored `Deprecated`): item and association edits locked. Draft / Pending Implementation / Private Draft / empty / any other value stay editable. A document update that sets a writable status applies the request's other changes even when the stored status was locked.
- There is no separate publish endpoint: set `adoptionStatus` in the imported package or via `PUT /api/v1/documents/{documentIdentifier}`. Fetch-by-UUID keeps working for frameworks outside the catalog.

## Not integration APIs

`/editor/…` and `/framework/editor/…` serve the Vue editor (session/Bearer on the main site; not a stable contract). Reading a framework in a browser is `/editor/{documentIdentifier}`; agents needing competency text should use `/uri/p{documentIdentifier}.md`. The issuer registry (`/issuer-registry/…`, OpenID Federation entity statements, no token) publishes organization/issuer metadata derived from public `organization` items.
