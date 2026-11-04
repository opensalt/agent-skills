# AGENTS.md

Guidance for any agent (Claude Code, Codex, Cursor, ZCode, Gemini CLI, …) working in this repository.

## What this repository is

Two agent skills for [1EdTech CASE 1.1](https://www.imsglobal.org/spec/case/v1p1) and [OpenSALT](https://github.com/opensalt/opensalt), packaged for distribution:

- `skills/case-json/` — converts source documents (text, CSV/TSV, JSON, XML/HTML, PDFs, spreadsheets, job descriptions, curricula, …) into CASE 1.1 `CFPackage` JSON. Derived from Brandon Dorman's original case-json skill.
- `skills/opensalt-skill/` — authors, validates, publishes, and reads back competency frameworks against a live OpenSALT registry. Bundles the CASE 1.1 format reference (`references/case-1.1-format.md`), the registry API reference (`references/registry-api.md`), and a package validator (`scripts/validate_case_package.py`).
- `test-outputs/` — historical conversion outputs kept as regression fixtures. Do not edit or delete them.
- `plugin.json` (repo root) — Agent Plugins open-standard manifest, read by GitHub Copilot (CLI, app, VS Code) and Cursor, and taking precedence over the vendor manifests in Copilot. `.antigravity-plugin/plugin.json` — Antigravity plugin manifest (`agy plugin`, Antigravity Marketplace; uses Antigravity's own schema with `displayName` and `suggestedPrompts`). `.claude-plugin/plugin.json` — Claude Code plugin manifest. `.zcode-plugin/plugin.json` — ZCode plugin manifest. `.cursor-plugin/plugin.json` — Cursor plugin manifest (its auto-discovery finds `skills/`). `.claude-plugin/marketplace.json` — marketplace catalog for Claude Code, ZCode, and Copilot CLI (documented fallback location); `.cursor-plugin/marketplace.json` — Cursor's marketplace catalog.

## Working in this repository

- Validate any CASE package — including one you just generated — before declaring it done:

  ```bash
  python3 skills/opensalt-skill/scripts/validate_case_package.py <file>.json [--strict] [--summary]
  ```

  Exit 0 = no errors. Exit 1 = errors (fix them). Warnings are review items, not noise; `--strict` promotes them to failures.

- Skills follow the agentskills.io layout: `skills/<name>/SKILL.md` with `name` + `description` YAML frontmatter, and the `name` must match its directory. Optional format check: `skills-ref validate skills/<name>` (the agentskills.io reference validator — it checks the SKILL.md package, not CASE semantics).
- Keep `SKILL.md` bodies lean (target < 500 lines) with trigger-focused descriptions; push heavy detail into the skill's `references/` and load it on demand.
- The references in `skills/opensalt-skill/references/` are dated snapshots of OpenSALT's docs (`core/public/llms/` in the product monorepo; every deployed OpenSALT host also serves them at `/llms.txt`). When re-syncing, update the footer date and note what changed.
- The validator is stdlib-only Python by design — do not add third-party dependencies.
- Keep plugin metadata consistent: `name`, `version`, and `description` must match across all seven manifests — root `plugin.json`, `.claude-plugin/plugin.json`, `.zcode-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.antigravity-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json` (the Antigravity manifest additionally carries `displayName` and `suggestedPrompts`).

## Installing the skills (for humans)

Full per-harness instructions are in [README.md](README.md). Summary:

- **Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode**: copy or symlink `skills/<name>/` into `.agents/skills/` (project) or `~/.agents/skills/` (personal) — all five read those locations. ChatGPT installs skills through Codex.
- **Claude Code**: `.claude/skills/<name>/` or `~/.claude/skills/<name>/` (symlinked skill folders are supported), or install as a plugin: `/plugin marketplace add opensalt/agent-skills` then `/plugin install opensalt-agent-skills@opensalt`.
- **ZCode**: Plugin Marketplace → Add → paste this repo (or a local clone), then install.
- **Cursor**: Customize → From GitHub Repository (`.cursor-plugin/marketplace.json`), or copy into `.cursor/skills/` / `.agents/skills/`.
- **GitHub Copilot**: `copilot plugin marketplace add opensalt/agent-skills` then `copilot plugin install opensalt-agent-skills@opensalt` (reads `.claude-plugin/marketplace.json` + root `plugin.json`), or copy into `.github/skills/` / `.agents/skills/`.
- **Antigravity**: `agy plugin install https://github.com/opensalt/agent-skills` (`.antigravity-plugin/plugin.json`), or copy into `.agents/skills/` (workspace) — no manifest needed for skills alone.
- **AGENTS.md readers generally**: add this checkout to the agent's workspace context — this file is the guidance.
