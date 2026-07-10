# David.md for Codex

David.md is a shareable Codex plugin for practical agent workflows. Version
`0.1.1` starts with **Fable Advisor**: a verified, read-only bridge from Codex to
Claude Fable for planning, architecture review, and second opinions grounded in
the actual repository.

## What Fable Advisor does

Fable gets advisory access to repository files, search, web research, and
read-only shell commands. It cannot edit the project, mutate git, send messages,
deploy, or perform external side effects. Codex remains responsible for execution
and verification.

That boundary is deliberate: an advisor needs wide visibility, not side effects.
If Fable fails or silently falls back to another model, the launcher reports the
exact blocker instead of replacing its output with a Codex-authored answer.

## Requirements

- Codex with plugin support.
- Claude Code installed as `claude` and authenticated.
- Access to the `fable` model.
- Python 3.10 or newer.

## Install from the public marketplace repository

```sh
codex plugin marketplace add dayvough/david.md
codex plugin add david-md@david-md
```

Restart or refresh Codex after installation. Then ask:

> Ask Fable to review this plan before implementation.

## Contents

- `fable-advisor` — streamed, resumable, model-verified Fable planning and
  review with a read-only permission boundary.

## Security model

The plugin is skill-only: it does not bundle an app connector, external tool
server, hook, credential, or background service. The launcher uses the Claude Code
installation and authentication already present on the user's machine. Raw run
logs are saved locally under `~/.codex/fable-advisor/runs/`.

## License

MIT
