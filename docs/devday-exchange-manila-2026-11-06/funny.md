# Track: Funny

**Goal: make the room laugh during the demo.** Nobody has to use it. It just has to be funny when you show it.

---

## What makes a funny build work

- **The joke lands in the first 10 seconds.** If you have to explain it, it isn't the joke yet.
- **Do one joke well.** That beats five jokes done halfway.
- **Be specific.** "Excuses for being late" is fine. "Excuses for being late, rated by whether your tita will believe them" is funnier.
- **Go local.** The room is full of Manila devs. Use EDSA, Grab, titas, GCash, being left on "Seen", the office rice cooker.
- **Commit to the bit.** A serious, corporate-looking app for a silly problem is funnier than a silly-looking app.

---

## Your pitch line

> **It's a ___ for ___, but ___.**

*Example: It's a real-time operations dashboard for the office Skyflakes supply, but it treats every missing pack like a security breach.*

---

## Step 1: Paste these Build Rules first

Copy this block, then add your seed below it **in the same message.**

```
You are helping a team build a small, funny web app in about 25 minutes at a hackathon.

Rules:
- Build the smallest thing that shows the joke. Default to one index.html file that opens by double-clicking. No build step unless we ask for one.
- Libraries from a CDN are fine if they make things easier (confetti, animation, charts, sound).
- AI calls are fine if we give you an API key. If the AI call fails, fall back to a list of pre-written lines so the demo still works. If we don't give you a key, use lists of pre-written lines picked at random.
- Keep it short. Aim for under 300 lines.
- Make it look polished: centered layout, big clear buttons, simple smooth animations.
- Build the smallest working version first. I'll ask for more after.
- When I ask for changes, always return the full updated file.
- Our idea below is a starting point. Follow our changes as we go.

Here's our idea:
```

---

## Step 2: Your idea (start here)

Start with your own idea. The best ones come out of the intros: the thing that annoyed someone this week, or the thing that made someone laugh. Fill this in and paste it under the Build Rules:

```
Build: [one sentence describing the app].
The joke is: [one sentence].
When the page opens, it shows: [what you see].
When I click [button], this happens: [what happens].
```

If you can't fill in all four blanks, the idea isn't concrete yet. Keep talking for 2 more minutes, or borrow a shape from the examples below.

---

## Need a spark? Example seeds

**These are examples, not a menu.** Steal the shape and change the topic. A seed you've rewritten around your office, your barangay, or your family group chat will beat one used as-is. Using a seed won't earn you more or fewer points.

Each example has a **Done when** line, so you know when to stop and record. **Extra if time** is optional.

---

### Seed F1: Skyflakes Ops Center

An enterprise command center for a trivial office problem.

```
An enterprise-grade "SKYFLAKES OPS CENTER" dashboard that monitors the office Skyflakes supply like a security operation.

- Header: "SKYFLAKES OPS CENTER" with a live clock and a blinking red "LIVE" dot.
- 4 stat cards: Packs Remaining, Packs Consumed Today, Threat Level, Prime Suspect.
- Start with 15 packs remaining.
- A button "Simulate Snack Event". Each click:
  - Packs Remaining goes down by 1, Packs Consumed goes up by 1.
  - Prime Suspect changes to a random name from a list of 8 Filipino first names.
  - A new line appears at the TOP of an "Incident Log" with the current time and a dramatic message picked at random from a list of at least 12. Example: "Unauthorized wrapper sound detected near pantry."
- Threat Level: "LOW" in green above 10 packs, "ELEVATED" in orange from 4 to 10, "CRITICAL" in red below 4.
- At 0 packs: the whole screen flashes red and a big banner shows "SKYFLAKES DEPLETED. ESCALATING TO HR." The button stops working.
- A "Restock" button resets everything to the start.
- Style: dark mode, serious corporate look, monospace numbers.
```

**Done when:** you can click from 15 down to 0 and the screen flashes red at 0.
**Swap the target:** the office rice cooker, the shared umbrella, the aircon remote, the last parking slot.
**Extra if time:** an alarm beep made with the Web Audio API (no sound files) when it hits CRITICAL.

---

### Seed F2: Reply Decision Engine

Fake AI that overthinks whether you should reply to a message.

```
A serious-looking SaaS product called "Reply Decision Engine" that decides if you should reply to a message.

- A text box: "Paste the message you received."
- A big button: "Analyze".
- After clicking, show a progress bar that takes about 8 seconds. Under it, show fake analysis steps one at a time, picked at random from a list of at least 15. Examples:
  "Measuring passive-aggression levels...", "Consulting your tita...",
  "Checking if they used 'k' or 'ok'...", "Cross-referencing with Mercury retrograde..."
- Then show a verdict card with:
  - A big verdict, picked at random from: "REPLY NOW", "LEAVE ON SEEN", "WAIT EXACTLY 3 HOURS", "REPLY WITH A STICKER ONLY", "MOVE TO CEBU".
  - "Confidence: XX.X%" with a random number between 80 and 99.9.
  - A one-line reason picked at random from a list of at least 10.
- Special rule: if the pasted message, trimmed and ignoring case, is exactly "k" or "ok", always show "LEAVE ON SEEN" with the reason "They started it."
- An "Analyze Again" button resets everything.
- Style: clean, white, looks like a real startup product.
```

**Done when:** you paste `ok`, wait for the progress bar, and get **LEAVE ON SEEN — They started it.**
**Extra if time:** with an AI key, have it read the actual message and write a reason specific to it.

---

### Seed F3: The Sign-Up Form That Fights Back

Password rules that get more and more unreasonable.

```
A sign-up page for a fake app called "Totally Normal App". The password rules get more unreasonable as you go.

- Fields: Name, Email, Password. A "Sign Up" button that stays disabled.
- Show password rules one at a time, below the password field. Show rule 1 first. When the password satisfies a rule, mark it with a green check and reveal the next rule. Earlier rules must stay satisfied (show a red X if one breaks).
- Rules, in order:
  1. At least 8 characters.
  2. Must include a number.
  3. Must include a capital letter.
  4. The digits in your password must add up to 15.
  5. Must include the name of an MRT-3 station (case-insensitive): North Avenue, Quezon Avenue, Kamuning, Cubao, Santolan, Ortigas, Shaw, Boni, Guadalupe, Buendia, Ayala, Magallanes, Taft.
  6. Must not contain the letter "e".
  7. This rule never passes. Show: "This password is already used by Tito Boy. Please choose another."
- Check rules live as the user types.
- Style: friendly, pastel, startup-looking. The cheerful look makes it funnier.
```

**Done when:** you type `Taft96Ayala`, rules 1–6 turn green, and rule 7 blames Tito Boy.
**Extra if time:** a "Give up" button that jumps to a random spot whenever the mouse gets close.

---

### Seed F4: Late Excuse Generator, Metro Manila Edition

Excuses with a believability score and a tita approval stamp.

```
"Late Excuse Generator: Metro Manila Edition".

- A dropdown "Late for:" with options Work, Date, Family Lunch, Standup Meeting.
- A slider "How late?" from 5 to 180 minutes. Show the current value.
- A button "Generate Excuse".
- The excuse is built from 3 random pieces, each from its own list, written in natural Taglish:
  - a cause (at least 12, e.g. "EDSA was a parking lot", "the underpass flooded"),
  - a complication (at least 10, e.g. "and my Grab driver took a 'shortcut'"),
  - a closer (at least 8, e.g. "pero on the way na talaga ako").
- Show the excuse in big text.
- Show a "Believability" meter from 0 to 100:
  believability = 95 − (minutes ÷ 2), then subtract 15 more if "Date" is selected. Clamp between 0 and 100. Round to a whole number.
- Show a stamp based on believability: above 60 → green "TITA APPROVED", 30 to 60 → orange "HMMM...", below 30 → red "SINUNGALING".
```

**Done when:** 5 minutes late to Work shows **TITA APPROVED**, and 180 minutes late to a Date shows **SINUNGALING**.
**Extra if time:** a stamp animation that slams onto the card.

---

### Seed F5: Teleserye Mode

Paste any boring text and it plays like the climax of a teleserye.

```
"Teleserye Mode": paste any boring text and it plays back like the dramatic climax of a teleserye.

- A text box, pre-filled with a sample: a boring office email saying the 2pm meeting is moved to 3pm.
- A big "Dramatize" button.
- On click: the screen goes black. The text appears one word at a time, about 2 words per second, in big centered white letters.
- Every few words, apply one random effect to the current word: zoom in, shake, turn red, or ALL CAPS.
- Between sentences, sometimes insert a dramatic stage direction in italics, picked at random from a list of at least 10. Examples: "(slaps table)", "(thunder)", "(camera zooms in on her face)", "(SINO KA BA TALAGA?)".
- At the end, "ITUTULOY..." fades in slowly and stays.
- A small "Exit" button in the corner. The Escape key also exits.
```

**Done when:** the sample email plays start to finish and ends on **ITUTULOY...**
**Extra if time:** with an AI key, rewrite the pasted text as a teleserye script before playing it.

---

### Seed F6: Tita Calculator

A real calculator with a tita who comments on every answer.

```
A working calculator with a tita who comments on every result.

- A normal calculator: digits 0–9, decimal point, + − × ÷, =, and C (clear). The math must be correct.
- Next to it, a tita avatar (the emoji 👵 in a big circle) with a speech bubble.
- After every "=", the tita comments on the result. Pick a line at random from the matching category (at least 4 lines each, in Taglish):
  - result is exactly 0
  - result is negative (utang jokes)
  - result is greater than 10,000 (ipon / "pautang naman" jokes)
  - result has decimals
  - anything else (general list of at least 10)
- Every 5th calculation, the tita ignores the math and asks an unrelated question instead, picked at random: "Kailan ka mag-aasawa?", "Magkano sweldo mo?", "Ikaw ba yung nag-IT? Paayos naman printer ko.", "Nasa abroad ka pa ba?"
- Style: warm colors, the speech bubble pops in with a small bounce.
```

**Done when:** 2 + 2 gives 4 with a comment, 5 − 5 triggers a zero line, and the 5th calculation triggers a question.
**Extra if time:** the tita gets more tired-looking (😩) the more you calculate.

---

## Demo tips (5 minutes, no audience participation)

- **Lead with the punchline.** Don't spend a minute on setup.
- **Know your 3 best clicks** and do them in order. Rehearse them once.
- **Deadpan works.** Present it like a serious product launch.
- **Keep your video open in a tab** as a backup.
