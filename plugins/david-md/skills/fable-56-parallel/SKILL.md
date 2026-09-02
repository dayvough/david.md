---
name: fable-56-parallel
description: Ask Claude Fable 5.1 High and GPT-5.6 Sol High the same read-only question at the same time, then return both complete answers exactly as written. Use only when the user explicitly invokes this skill or asks for both raw responses.
---

# Fable 5.1 + 5.6 Parallel

Run two independent, read-only advisory passes on one task and return the two answers unchanged.

## Output contract

- Treat explicit invocation as authorization to call Fable for this request only.
- Give both models the same task payload and the same task-relevant context.
- Keep both runs read-only. Do not let either model edit files, send messages, change external state, or delegate further.
- Do not summarize, reconcile, rank, critique, quote selectively, or add a recommendation.
- In the final response, add only these two source headings, in this order:

  `## Fable 5.1 High`

  `## GPT-5.6 Sol High`

- Under each heading, reproduce that model's complete answer verbatim. Do not wrap it in a code fence or normalize its formatting.
- If a run fails, do not substitute another model. Put its exact error output under that model's heading.

## Parallel workflow

1. Extract the user's task after the skill invocation. Preserve its wording. Add only context strictly required to make the task self-contained, and give that identical payload to both models.
2. This skill requires the current Codex session to already be GPT-5.6 Sol
   with high reasoning. If it is not, stop instead of substituting a model.
   Start the GPT run with `spawn_agent` using only:
   - `task_name`: `gpt56_high`
   - `fork_turns`: `none`
   - `message`: the shared payload plus: `Return only your answer to the task. Do not describe your process. Do not modify files or external state.`

   The sub-agent inherits the current session's model and reasoning level. Do
   not pass unsupported `model` or `reasoning_effort` fields.
3. Immediately start Fable in the task's working directory. Put the shared payload in a temporary prompt file and run:

   ```sh
   claude -p --model claude-fable-5-1 --effort high --output-format text --permission-mode plan --safe-mode --tools "Read,Grep,Glob" < PROMPT_FILE
   ```

   Capture standard output exactly. If the command fails, capture the exact error output and exit status without interpreting them.
4. After the Fable command returns, wait for `gpt56_high` if needed. Capture the agent's final message exactly.
5. Emit the final response according to the output contract. Add no preface, conclusion, status block, or other text.

## Context rules

- For a self-contained question, send only the question and its supplied material.
- For a repository question, name the working directory and allow both models to inspect only the relevant files read-only.
- Never silently broaden the task or provide one model with conclusions from the other.
- If essential context is unavailable, ask one concise question before launching either run.
