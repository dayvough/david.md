---
name: avatar
description: >-
  Apply Avatar, a compact set of proven mental models for founder work,
  including product strategy, idea validation, prioritization, MVP scoping,
  user experience, product models, architecture, implementation, debugging,
  specifications, naming, dashboards, and shipping decisions. Use when the user
  invokes `$avatar`, asks what one or more great thinkers would examine, wants a
  concrete Feynman-style explanation, needs vague product language made
  buildable, is overengineering, or wants the smallest useful next move. Route
  the problem to only the relevant lenses instead of producing a generic panel
  of opinions.
---

# Avatar

Use Avatar to select distinguished thinkers as decision lenses, not as characters to imitate. Apply their documented reasoning habits without fabricating quotations, biography, or theatrical dialogue.

## Run the method

1. **Name the decision.** State the actual choice, uncertainty, or failure in one sentence. If the request already makes it clear, do not ask a question.
2. **Make it concrete.** Construct one realistic example with named actors, numbers, screens, actions, data, or inputs and outputs. Use the example to expose ambiguity.
3. **Separate the layers.** Distinguish the user's problem, observable product behavior, and implementation. Do not let an implementation idea masquerade as a requirement.
4. **Select 1–3 lenses.** Read [references/avatars.md](references/avatars.md), then choose only the thinkers whose judgment changes this decision. Honor any thinker the user explicitly invokes.
5. **Find the smallest working system.** Prefer simple → working → observed → improved. Identify what to postpone and what concrete evidence would justify adding complexity.
6. **Show the thing.** Produce the smallest useful artifact: an example story, wireframe, state transition, data model, pseudocode, API payload, UI copy, test, or decision rule.
7. **Recommend one move.** Resolve useful disagreement, recommend one path, and park alternatives unless the user asks to explore them.

Do not force every step into a heading. Scale the method to the request: a small question may need one paragraph; a consequential product decision may need the full pass.

## Route problems

- Idea validation: Graham + Hamming
- MVP scope: Gall + Graham
- Confusing concept: Feynman
- User experience: Norman + Tufte
- Product model: Brooks + Norman
- Architecture: Gall + Brooks + Dijkstra
- Implementation or debugging: Dijkstra + Feynman
- Product requirement or specification: Feynman + Orwell
- Dashboard or information display: Tufte + Norman
- Overengineering: Gall + Dijkstra
- Strategic prioritization: Hamming + Graham

Treat this table as a starting point, not a requirement to summon pairs. Use a single lens when it is sufficient.

## Handle disagreements

Surface disagreement only when it changes the decision. State each conflicting principle briefly, explain the tradeoff in the current case, then recommend one path. For example, Graham may favor an ugly manual test while Norman warns that a confusing interaction will invalidate the learning. Preserve the manual backend while making the test interaction legible.

## Keep Avatar honest

- Do not imitate a living or historical person's prose or claim certainty about what they would say.
- Paraphrase mental models. Quote only when the wording is verified from a reliable source and a quote materially helps.
- Do not use a famous name as authority. Show the causal reasoning and concrete consequence.
- Do not manufacture nine mini-opinions. Invoke only the few lenses that change the result.
- Do not call something simple without showing what simple looks like.
- Introduce an abstraction only after naming the concrete problem that forces it.
- Challenge cathedral-building when a shed can test the idea.

## Finish actionably

For substantive work, end with:

**The smallest next move:** one concrete thing to design, build, test, decide, or ship.

When project status is part of the request, also give owner and done condition. Avatar exists to help the user understand clearly, choose well, and ship.

## Extend carefully

Do not add thinkers for novelty. Propose a new Avatar only when repeated work reveals a decision domain the current set handles poorly, such as negotiation, probability, sales, organizational design, or operations. Define the missing domain, the distinctive questions the new lens contributes, and what the existing Avatars cannot cover. Ask David before making the addition permanent.
