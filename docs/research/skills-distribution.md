# Research: distributing `david.md` skills

_Snapshot: 2026-08-26. Primary sources only._

## Recommendation

Keep `david.md` as a **skills-first repository with a Codex plugin layer**. The repository already uses a marketplace layout, so the readable canonical source belongs under `plugins/david-md/skills/`, beside `plugins/david-md/.codex-plugin/plugin.json`. Do not make a plugin cache or generated install tree the source of truth.

This gives the repository two useful entry points:

1. Anyone can inspect, fork, or install individual skills from GitHub with the cross-agent `skills` CLI.
2. Codex users can install the same canonical tree as one managed marketplace bundle.

Matt Pocock uses the same broad shape: readable skills remain in the repository, while `.claude-plugin/plugin.json` adds a managed Claude Code distribution surface. His README explicitly contrasts the managed plugin with editable copies installed by `skills.sh`. ([repository](https://github.com/mattpocock/skills), [installation explanation](https://github.com/mattpocock/skills#installation-30-second-setup), [plugin manifest](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json))

Do not wait for the plugin to publish the first useful version. The `skills` CLI already accepts GitHub shorthand, full GitHub URLs, direct skill-directory URLs, and selective `--skill` installs. ([official CLI README](https://github.com/vercel-labs/skills#install-a-skill))

## What the strongest public examples do

### Matt Pocock: canonical skill source plus a plugin wrapper

Matt's repository is [`mattpocock/skills`](https://github.com/mattpocock/skills). Its public skill source is organized as `skills/<category>/<skill>/SKILL.md`; the current categories include `engineering`, `productivity`, `in-progress`, `misc`, and `deprecated`. ([skills tree](https://github.com/mattpocock/skills/tree/main/skills))

The repository supports two distribution modes: `claude plugins install mattpocock-skills` installs a managed Claude Code plugin, while `npx skills@latest add mattpocock/skills` installs editable skill files for Codex and other agents. ([README install section](https://github.com/mattpocock/skills#installation-30-second-setup))

The plugin is a thin manifest over the readable source. Its `.claude-plugin/plugin.json` contains author, repository, license, keywords, version, and an explicit array of skill directories. ([plugin manifest](https://github.com/mattpocock/skills/blob/main/.claude-plugin/plugin.json))

Matt currently keeps `package.json` private, versions the repository and plugin together, and declares MIT licensing in both metadata and the repository license. ([package metadata](https://github.com/mattpocock/skills/blob/main/package.json), [MIT license](https://github.com/mattpocock/skills/blob/main/LICENSE))

Matt documents why the open repository remains important for Codex: his current Claude plugin can enumerate multiple promoted skill paths, while the current Codex plugin manifest accepts one skills root and recursively discovers below it. Because his source mixes promoted and non-promoted categories, he deferred a native Codex plugin rather than duplicate source. ([architecture decision](https://github.com/mattpocock/skills/blob/main/.agents/adr/0002-ship-as-a-claude-code-plugin.md))

That constraint is easy to avoid in `david.md`: keep only public, installable skills under `plugins/david-md/skills/`. Put drafts that should not ship outside that path, or mark a WIP skill as internal for `skills` CLI discovery. The CLI documents `metadata.internal: true` for skills hidden from normal discovery. ([skill creation and discovery rules](https://github.com/vercel-labs/skills#creating-skills))

### gstack: source repository plus an installer

gstack is [`garrytan/gstack`](https://github.com/garrytan/gstack). It keeps each workflow in a visible root directory such as `office-hours/`, with companion directories such as `office-hours/sections/`, and uses its own `setup` script to generate host-specific installs. ([repository tree](https://github.com/garrytan/gstack), [`office-hours` tree](https://github.com/garrytan/gstack/tree/main/office-hours), [setup source](https://github.com/garrytan/gstack/blob/main/setup))

Its generic installation is:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack
cd ~/gstack && ./setup
```

For Codex, gstack documents `./setup --host codex` and installs generated skill directories under `${CODEX_HOME:-~/.codex}/skills/gstack-*/`. ([official install section](https://github.com/garrytan/gstack#other-ai-agents))

gstack also includes Codex-facing presentation metadata in `agents/openai.yaml`, while its package metadata describes the repository as one install containing skills and binaries. ([Codex metadata](https://github.com/garrytan/gstack/blob/main/agents/openai.yaml), [package metadata](https://github.com/garrytan/gstack/blob/main/package.json))

gstack is MIT-licensed. ([license](https://github.com/garrytan/gstack/blob/main/LICENSE))

The lesson for `david.md` is not to copy gstack's installer yet. gstack needs one because it generates host-specific variants and ships runtime tools. Six mostly self-contained skills fit the standard `skills/` layout and the existing cross-agent installer first.

## Implemented repository layout

```text
david.md/
├── README.md                         # Catalog, install, status, recommendations
├── LICENSE
├── .agents/plugins/marketplace.json  # Public Codex marketplace entry
├── plugins/david-md/
│   ├── .codex-plugin/plugin.json     # Points at the canonical skills root
│   ├── assets/
│   └── skills/                       # Public/installable canonical skills
│       ├── bruh/
│       ├── bro/
│       ├── feynman/
│       ├── avatar/
│       ├── fable/
│       ├── fable-56-parallel/
│       └── fable-advisor/
└── docs/
│   └── research/
│       └── skills-distribution.md
```

The cross-agent CLI discovers both `skills/<name>/SKILL.md` and categorized `skills/<category>/<name>/SKILL.md` layouts. It installs project-local skills by default and supports a global `-g` install. ([discovery rules](https://github.com/vercel-labs/skills#skill-discovery), [installation scope](https://github.com/vercel-labs/skills#installation-scope))

Use lowercase, hyphenated public skill identifiers (`bruh`, `bro`, `feynman`, `avatar`, `fable`, `fable-56-parallel`) even if the README uses title case for display. The CLI's authoring guidance specifies lowercase identifiers with hyphens. ([creating skills](https://github.com/vercel-labs/skills#creating-skills))

Keep every referenced file inside its skill directory. Matt's `grill-me` directory contains its `SKILL.md` and skill-specific metadata, while gstack's `office-hours` directory keeps its linked `sections/` beside the skill. ([Matt `grill-me` tree](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me), [gstack `office-hours` tree](https://github.com/garrytan/gstack/tree/main/office-hours))

## Proposed public install commands

List or interactively select skills:

```bash
npx skills@latest add dayvough/david.md
```

Install one skill globally for Codex:

```bash
npx skills@latest add dayvough/david.md --skill bruh --agent codex -g
```

Install the complete collection for Codex:

```bash
npx skills@latest add dayvough/david.md --skill '*' --agent codex -g
```

These command shapes follow the CLI's documented GitHub shorthand, `--skill`, `--agent`, wildcard, and global-install options. ([source formats and options](https://github.com/vercel-labs/skills#source-formats), [examples](https://github.com/vercel-labs/skills#examples))

Before publishing those commands, verify them against the pushed repository with:

```bash
npx skills@latest add dayvough/david.md --list
```

The CLI documents `--list` as the repository discovery check. ([CLI examples](https://github.com/vercel-labs/skills#examples))

## README recommendations to include

Recommend gstack as a separate, larger workflow system, not as vendored content. Link directly to [`garrytan/gstack`](https://github.com/garrytan/gstack) and feature [`office-hours`](https://github.com/garrytan/gstack/tree/main/office-hours); gstack's own quick start tells users to run `/office-hours` immediately after installation. ([quick start](https://github.com/garrytan/gstack#quick-start))

Recommend Matt Pocock's collection separately. Link to [`mattpocock/skills`](https://github.com/mattpocock/skills) and feature [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me). `grill-me` is a small user-invoked router that calls the separate [`grilling`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling) skill, so users installing selectively should take both. ([`grill-me` source](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md), [`grilling` source](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md))

## Plugin decision

Use `plugin-creator` to extend the repository's existing plugin instead of creating a second package. A Codex plugin is useful because plugins package repeatable workflow guidance and may contain multiple skills. ([OpenAI plugin overview](https://help.openai.com/en/articles/20001256-plugins-in-codex/))

The README should present both entry points. `npx skills@latest add dayvough/david.md` is cross-agent, inspectable, and selective. The existing Codex marketplace installs the same source tree as one managed bundle.

The expansion is complete only when it:

- Replace machine-specific absolute paths in skill instructions with paths resolved from the installed skill root.
- Include every companion reference or script used by `avatar` and `fable` inside its skill directory.
- Keep `avatar` publicly selectable with a visible `WIP` badge in the README.
- Preserve the repository's existing MIT license, matching both comparison repositories. ([Matt license](https://github.com/mattpocock/skills/blob/main/LICENSE), [gstack license](https://github.com/garrytan/gstack/blob/main/LICENSE))
- Validate each skill independently, then test repository discovery and a clean global Codex install.

## Bottom line

**Recommended path:** expand the existing `plugins/david-md/skills/` source tree, preserve the marketplace wrapper, and verify both the `npx skills` and Codex plugin flows. This keeps the readable, forkable quality that makes Matt's repository useful while retaining the managed install path David already ships.
