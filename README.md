# OpenSALT Agent Skills

Two agent skills for [1EdTech CASE 1.1](https://www.imsglobal.org/spec/case/v1p1) and [OpenSALT](https://github.com/opensalt/opensalt):

| Skill | What it does | When to reach for it |
|---|---|---|
| **`case-json`** | Converts **any source** — plain text, CSV/TSV, JSON, XML/HTML, PDFs, images, job descriptions, resumes, course catalogs, existing non-CASE frameworks — into a valid CASE 1.1 `CFPackage` JSON document, preserving source wording, hierarchy, and ordering. | "Turn this document / spreadsheet / job list into CASE JSON." |
| **`opensalt-skill`** | Authors, validates, publishes, and reads back competency **frameworks** against a live OpenSALT registry: OpenSALT item kinds (`course`, `job`, `credential`, `organization`, …), distribution guidance, a bundled package validator, `/api/v1` upload, and reading via the CASE catalog, `/uri/` markdown, or MCP. | "Create a framework for distribution", "validate this package", "upload it to OpenSALT", "fetch framework X back." |

The skills compose: `case-json` produces the package; `opensalt-skill` validates it (`scripts/validate_case_package.py`), applies distribution/registry guidance, and handles upload and verification.

## Repository layout

```
AGENTS.md                         cross-harness guidance for agents working in this repo
plugin.json                       Agent Plugins (open standard) manifest — Copilot CLI/app/VS Code, Cursor
.claude-plugin/plugin.json        Claude Code plugin manifest
.claude-plugin/marketplace.json   marketplace catalog (read by Claude Code and ZCode)
.zcode-plugin/plugin.json         ZCode plugin manifest
.cursor-plugin/plugin.json        Cursor plugin manifest (skills auto-discovered from skills/)
.cursor-plugin/marketplace.json   Cursor marketplace manifest ("From GitHub Repository" import)
.antigravity-plugin/plugin.json   Antigravity plugin manifest (agy plugin / Marketplace)
skills/
  case-json/                      source → CFPackage conversion skill
    SKILL.md
    data-model-reference.md
    examples/example_output.json
  opensalt-skill/                 framework authoring / validation / publishing skill
    SKILL.md
    references/case-1.1-format.md   CASE 1.1 format reference (corrected copy)
    references/registry-api.md      current OpenSALT registry API (from core/public/llms/)
    scripts/validate_case_package.py
test-outputs/                     historical conversion outputs kept as regression fixtures
```

## Installation

The skill folders are plain [agentskills.io](https://agentskills.io) packages — every harness below reads the same `SKILL.md` format; only the discovery paths differ (documented per harness as of 2026-10). Copy or symlink `skills/case-json/` and `skills/opensalt-skill/` into any of them:

| Harness | Project skills | Personal skills |
|---|---|---|
| Codex (OpenAI — also ChatGPT's coding agent) | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` (also reads `.claude/skills/`) — or install the plugin via **Customize → From GitHub Repository** (this repo ships `.cursor-plugin/marketplace.json`) | `~/.agents/skills/` or `~/.cursor/skills/` |
| GitHub Copilot (incl. VS Code) | `.github/skills/` or `.agents/skills/` (also reads `.claude/skills/`) — or `copilot plugin marketplace add opensalt/agent-skills` then `copilot plugin install opensalt-agent-skills@opensalt` | `~/.copilot/skills/` or `~/.agents/skills/` |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/` | `~/.gemini/skills/` or `~/.agents/skills/` |
| OpenCode | `.opencode/skills/` or `.agents/skills/` (also reads `.claude/skills/`) — no plugin layer; its "plugins" are JS hook modules, so folders are the whole story | `~/.config/opencode/skills/` |
| Antigravity (Google) | `.agents/skills/` (workspace, walked up to repo root) — or `agy plugin install https://github.com/opensalt/agent-skills` | `~/.gemini/config/skills/` |
| Claude Code | `.claude/skills/<name>/` | `~/.claude/skills/<name>/` |

`.agents/skills/` is the shared cross-tool location: Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode, and Antigravity all read it. Claude Code reads `.claude/skills/` and supports symlinked skill folders, so teams standardizing on one location can link `.claude/skills/<name>` → `../.agents/skills/<name>`.

### Plugin flows (optional)

- **Claude Code**: `claude plugin add <repo-checkout>` — or `/plugin marketplace add opensalt/agent-skills`, then `/plugin install opensalt-agent-skills@opensalt` (note: the repo is `opensalt/agent-skills`; the installable plugin inside it is named `opensalt-agent-skills`)
- **ZCode**: Plugin Marketplace → Add → paste this repo (or a local clone), then install
- **Cursor**: Customize → **From GitHub Repository** → paste `opensalt/agent-skills` (reads `.cursor-plugin/marketplace.json`); on Teams/Enterprise it can be added as a team marketplace, and the plugin can be submitted to cursor.com/marketplace/publish
- **GitHub Copilot**: `copilot plugin marketplace add opensalt/agent-skills`, then `copilot plugin install opensalt-agent-skills@opensalt` — the CLI reads our `.claude-plugin/marketplace.json` (documented fallback location) and the Agent Plugins `plugin.json`. Also works via the Copilot app and VS Code (**Chat: Install Plugin from Source**, with `chat.plugins.enabled`)
- **Antigravity**: `agy plugin install https://github.com/opensalt/agent-skills`, or drop the repo folder into `.agents/plugins/` (workspace) / `~/.gemini/config/plugins/` (global) — reads `.antigravity-plugin/plugin.json`. Validate with `agy plugin validate --strict`. Skills alone install via `.agents/skills/` with no manifest

### AGENTS.md readers (Codex, Cursor, Copilot, Gemini CLI, …)

This repo ships [`AGENTS.md`](AGENTS.md); add the checkout to the agent's workspace and it picks up the repository guidance automatically.

## Usage

```
/case-json Here are our team competencies: 1. Project Management - planning, scheduling, risk assessment. 2. Technical Writing - documentation, API specs, user guides.
/case-json /path/to/skills.csv
```

```
Create a CASE 1.1 package for our robotics curriculum and validate it for distribution.
Upload /tmp/framework.json to our OpenSALT registry and verify it by fetching it back.
```

## Validation

`skills/opensalt-skill/scripts/validate_case_package.py` is a stdlib-only Python validator for any CASE 1.1 package (both skills' output included):

```bash
python3 skills/opensalt-skill/scripts/validate_case_package.py package.json
# options: --strict (warnings fail) · --summary (counts by kind and association type)
```

It checks required fields, UUID/URI/datetime formats, `LinkURI` shape, association types and referential integrity, duplicate identifiers, OpenSALT item kinds (`ob3` credential payload), label-only `CFItemType` usage, `adoptionStatus` spellings, and rubric structure.

## Provenance and syncing

The bundled references are snapshots, dated in their footers:

- `case-1.1-format.md` — from this project's `CASE_1.1_OpenSALT_Reference.md`, corrected against the registry's current docs.
- `registry-api.md` — condensed from the host's LLM documentation (`core/public/llms/*.md`, current as of 2026-11). Every deployed OpenSALT host serves these publicly (`GET /llms.txt`, `/llms/*.md`), so refresh from any live registry when the product changes.

## Credits

Maintained by **opensalt**. The `case-json` skill is derived from the original [case-json skill](https://github.com/fibonacciskills/case-json-skill) by Brandon Dorman; the versions in this repository are not his work. `opensalt-skill` is original to this repository.

## License

MIT — see `.claude-plugin/plugin.json`.
