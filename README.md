# david.md

Six skills for six jobs. A skill is a folder of instructions that tells an agent how to handle one kind of request.

## Skills

- [`$bruh`](plugins/david-md/skills/bruh/SKILL.md) rewrites content with short sentences and common words.
- [`$bro`](plugins/david-md/skills/bro/SKILL.md) restates the previous answer in plain, concise language.
- [`$feynman`](plugins/david-md/skills/feynman/SKILL.md) starts with basic facts, builds the explanation step by step, and shows where it stops being true.
- [`$avatar`](plugins/david-md/skills/avatar/SKILL.md) **(WIP)** uses questions from one to three thinkers to examine a founder or product problem, then recommends the smallest useful move.
- [`$fable`](plugins/david-md/skills/fable/SKILL.md) gives Claude Fable one repository task with explicit limits and records what it did.
- [`$fable-56-parallel`](plugins/david-md/skills/fable-56-parallel/SKILL.md) asks Fable and GPT-5.6 Sol the same question without letting either change files, then returns both answers without choosing between them.

## Install

Install all six as one Codex plugin:

```sh
codex plugin marketplace add dayvough/david.md
codex plugin add david-md@david-md
```

Install one skill globally for Codex:

```sh
npx skills@latest add dayvough/david.md --skill feynman --agent codex -g
```

## Fable requirements

The two Fable skills require Claude Code, access to Claude Fable, and Python 3.10 or newer. `$fable-56-parallel` also requires the current Codex session to use GPT-5.6 Sol with high reasoning and support sub-agents.

## More skills

- [gstack](https://github.com/garrytan/gstack): start with [`$office-hours`](https://github.com/garrytan/gstack/tree/main/office-hours) to define the problem before writing code.
- [Matt Pocock's skills](https://github.com/mattpocock/skills): start with [`$grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me) and [`$grilling`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling) to expose weak assumptions in a plan.

## License

[MIT](LICENSE)
