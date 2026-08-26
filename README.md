# David.md for Codex

David.md is an MIT-licensed collection of practical, inspectable agent skills. Version `0.2.0` expands the existing Fable Advisor plugin into a broader toolkit for clear language, first-principles explanations, product judgment, and bounded model collaboration.

## Skills

| Skill | What it does | Status |
| --- | --- | --- |
| [`$bruh`](plugins/david-md/skills/bruh/SKILL.md) | Rewrites content with Simplified Technical English principles. | Ready |
| [`$bro`](plugins/david-md/skills/bro/SKILL.md) | Restates the previous answer in shorter, everyday language. | Ready |
| [`$feynman`](plugins/david-md/skills/feynman/SKILL.md) | Explains difficult ideas from first principles without losing rigor. | Ready |
| [`$avatar`](plugins/david-md/skills/avatar/SKILL.md) | Routes founder and product decisions through a small set of useful mental models. | **WIP** |
| [`$fable`](plugins/david-md/skills/fable/SKILL.md) | Runs Claude Fable as a bounded, audited advisor or implementer. | Ready |
| [`$fable-56-parallel`](plugins/david-md/skills/fable-56-parallel/SKILL.md) | Runs one read-only prompt through Fable High and GPT-5.6 Sol High, then returns both raw answers. | Ready |
| [`$fable-advisor`](plugins/david-md/skills/fable-advisor/SKILL.md) | Preserves the original read-only Fable planning and review workflow. | Explicit only |

`$avatar` is public so people can inspect and try it, but its lens set and routing are still being refined.

`$fable-advisor` remains available for backward compatibility. Generic Fable requests route to `$fable`; invoke `$fable-advisor` by name when you specifically want the original read-only workflow.

## Install as a Codex plugin

```sh
codex plugin marketplace add dayvough/david.md
codex plugin add david-md@david-md
```

Restart or refresh Codex after installation. The plugin installs the full collection.

## Install individual skills

The cross-agent [`skills`](https://github.com/vercel-labs/skills) CLI can inspect and install individual skills directly from this repository.

List the available skills:

```sh
npx skills@latest add dayvough/david.md --list
```

Install one skill globally for Codex:

```sh
npx skills@latest add dayvough/david.md --skill feynman --agent codex -g
```

Install every discovered skill globally for Codex:

```sh
npx skills@latest add dayvough/david.md --skill '*' --agent codex -g
```

## Requirements

The explanation and product-thinking skills are prompt-only.

`$fable`, `$fable-56-parallel`, and `$fable-advisor` require:

- Claude Code installed as `claude` and authenticated.
- Access to the named Claude models.
- Python 3.10 or newer.

`$fable-56-parallel` also requires a Codex host that exposes sub-agent spawning and the `gpt-5.6-sol` model.

## Recommended collections

- [gstack](https://github.com/garrytan/gstack) is the larger end-to-end workflow system I recommend. Start with [`$office-hours`](https://github.com/garrytan/gstack/tree/main/office-hours) to pressure-test a product idea before implementation.
- [Matt Pocock's skills](https://github.com/mattpocock/skills) are the best next catalog to explore. Start with [`$grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) and its underlying [`$grilling`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling) skill.

Install Matt's collection and select both grilling skills when prompted:

```sh
npx skills@latest add mattpocock/skills
```

## Repository layout

```text
.
├── .agents/plugins/marketplace.json
├── plugins/david-md/
│   ├── .codex-plugin/plugin.json
│   ├── assets/
│   └── skills/                   # Canonical public skill source
└── docs/research/                # Source-backed distribution research
```

The research behind this structure is in [`docs/research/skills-distribution.md`](docs/research/skills-distribution.md).

## Verification

Run the Fable launcher test suites:

```sh
python3 -m unittest -v plugins/david-md/skills/fable/scripts/test_fable.py
python3 -m unittest -v plugins/david-md/skills/fable-advisor/scripts/test_fable_advisor.py
```

Before a release, validate the plugin manifest, validate every `SKILL.md`, and run the `npx skills --list` discovery check.

## License

[MIT](LICENSE)
