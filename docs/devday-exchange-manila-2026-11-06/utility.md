# Track: Utility

**Goal: one thing, done really well.** One input, one output. A judge should be able to hand you an input you've never seen, and it should just work.

---

## What makes a utility build win

- **One sentence, no "and."** If your description has "and" in it, cut everything after the "and."
- **Handle messy input.** Real people paste extra spaces, commas, peso signs, and blank lines. Doing those well is what "really well" means.
- **No friction.** Paste, see the result. No settings, no sign-up.
- **Test cases first.** Write down inputs and the exact output you expect *before* you build. AI tools build much better from examples, and the judges will test you with inputs you haven't seen.

---

## Your pitch line

> **Give it ___, and it instantly gives you ___.**

*Example: Give it a peso amount, and it instantly gives you the words to write on a check.*

---

## Step 1: Paste these Build Rules first

Copy this block, then add your seed below it **in the same message.**

```
You are helping a team build a small, useful web tool in about 25 minutes at a hackathon. It must do one thing extremely well.

Rules:
- Default to one index.html file that opens by double-clicking. No build step unless we ask for one.
- Libraries from a CDN are fine if they save real work (reading PDFs, parsing CSV, handling dates).
- AI calls are fine if we give you an API key. Use plain code for anything with one exact right answer (math, formatting, parsing). Use AI only for the fuzzy part.
- Keep it short. Aim for under 300 lines.
- One input area, one output area. The output updates as I type or paste.
- Handle messy input: extra spaces, commas, mixed case, blank lines. Never crash. For input you can't handle, show a short friendly message in the output area.
- Include a "Copy result" button. Use navigator.clipboard, and fall back to selecting the text and calling document.execCommand('copy') if that fails.
- Below the tool, add a small "Self-test" section. It runs every test case I give you and shows ✅ or ❌ for each, with the expected and actual output on failures. (Test only the parts that have exact answers.)
- Do money math in centavos (whole numbers) to avoid floating-point errors.
- Build the smallest working version first. When I ask for changes, always return the full updated file.
- Our idea below is a starting point. Follow our changes as we go.

Here's our tool:
```

### When a self-test fails

```
Test ___ shows ❌.
Expected: ___
Got: ___
Fix the logic for that case only. All other tests must still pass.
Give me the full updated index.html.
```

---

## Step 2: Your idea (start here)

Start with your own idea. The best ones come out of the intros: the thing that annoyed someone this week. Fill this in and paste it under the Build Rules:

```
Build a tool that does exactly one thing: [one sentence, no "and"].
Input: [what the user pastes, types, or uploads].
Output: [exactly what appears].
Rules for messy input: [extra spaces? commas? blank lines? what counts as invalid?]

Test cases (put these in the Self-test section):
1. "___" → "___"
2. "___" → "___"
3. "___" → "___"
4. (something invalid) "___" → "___"
```

**Test:** if you can't write 3 test cases with exact outputs, the idea isn't concrete yet.

**Good places to find one:** a converter you Google every month, a format you clean by hand in Excel, a calculation you redo on your phone, a message you rewrite every week.

---

## Need a spark? Example seeds

**These are examples, not a menu.** What matters is the pattern: a tight spec plus test cases with exact outputs. Copy that pattern for your own idea. Using a seed won't earn you more or fewer points.

If you do use one, **paste its test cases too.** They're what keep the model on track.

---

### Seed U1: Peso Amount → Check Words

**Pitch:** Give it a peso amount, and it instantly gives you the words to write on a check.

```
A tool that converts a peso amount into the words you write on a check.

Spec:
- Input: one amount. Accept a "₱" or "PHP" prefix, commas, and spaces. Round to 2 decimals.
- Supported range: 0 to 999,999,999.99. Outside that range, or for non-numbers, show "Please enter an amount from 0 to 999,999,999.99".
- Output format: Title Case words, then "Peso" if the whole-peso part is exactly 1, otherwise "Pesos".
  If centavos > 0, add " and XX/100" (always 2 digits). Always end with " Only".
- Hyphenate numbers from 21 to 99 (Twenty-One). Do not use the word "and" between number words.
- Show the result in big text with a Copy button.

Test cases (put these in the Self-test section):
1. "1234.56" → "One Thousand Two Hundred Thirty-Four Pesos and 56/100 Only"
2. "₱12,345.67" → "Twelve Thousand Three Hundred Forty-Five Pesos and 67/100 Only"
3. "500" → "Five Hundred Pesos Only"
4. "1" → "One Peso Only"
5. "0.75" → "Zero Pesos and 75/100 Only"
6. "1,000,000" → "One Million Pesos Only"
7. "abc" → "Please enter an amount from 0 to 999,999,999.99"
```

---

### Seed U2: PH Mobile Number Cleaner

**Pitch:** Give it a messy list of PH mobile numbers, and it instantly gives you a clean, de-duplicated list in +63 format.

```
A tool that cleans a messy list of Philippine mobile numbers.

Spec:
- Input: a textarea. Numbers are separated by new lines, commas, or semicolons. (Spaces can be INSIDE a number, so do not split on spaces.) Ignore blank entries.
- For each entry, remove spaces, dashes, dots, parentheses, and a leading "+". Then look at the digits:
  - 11 digits starting with "09" → "+63" + the last 10 digits
  - 12 digits starting with "639" → "+" + the digits
  - 10 digits starting with "9" → "+63" + the digits
  - anything else → invalid
- Remove duplicates and keep the first one seen. Keep the original order.
- Output:
  - A summary line: "X valid · Y duplicates removed · Z invalid"
  - The clean list, one per line, with a Copy button
  - A "Couldn't read" list showing invalid entries exactly as they were typed

Test case (put this in the Self-test section):
Input (one per line):
  0917 123 4567
  +63 917-123-4567
  9181234567
  639991234567
  0917123456
  (02) 8123 4567
  0998.765.4321
Expected clean list:
  +639171234567
  +639181234567
  +639991234567
  +639987654321
Expected summary: "4 valid · 1 duplicates removed · 2 invalid"
Expected "Couldn't read": "0917123456" and "(02) 8123 4567"
```

---

### Seed U3: Barkada Bill Splitter

**Pitch:** Give it who ordered what, and it instantly gives you what each person owes, service charge included, down to the centavo.

```
A bill splitter for group meals with a service charge.

Spec:
- Input: a textarea with lines like "Ana: 250". A name can appear on several lines; add their amounts up.
  A line starting with "shared:" is split equally among everyone named.
  Accept "₱" and commas in amounts. Ignore blank lines. Names are case-sensitive as typed.
- A "Service charge %" number field, default 10.
- Math (do it in centavos, as integers):
  - grand total = round((sum of all amounts) × (100 + service%) / 100)
  - each person's exact share = (their amount + shared ÷ number of people) × (100 + service%) / 100
  - round each share DOWN to the centavo, then give the leftover centavos one at a time to people in the order they first appear, until the shares add up to the grand total exactly.
- Output: a table with Name | Amount owed (₱X,XXX.XX), then a bold Grand Total row, and a Copy button that copies it as plain text.
- If no names are entered, show "Add at least one person, like  Ana: 250".

Test cases (put these in the Self-test section):
1. "Ana: 250 / Ben: 180 / Cy: 120 / shared: 300", service 10
   → Ana ₱385.00, Ben ₱308.00, Cy ₱242.00, Total ₱935.00
2. "Ana: 0 / Ben: 0 / Cy: 0 / shared: 100", service 0
   → Ana ₱33.34, Ben ₱33.33, Cy ₱33.33, Total ₱100.00
3. "Ana: 150 / Ben: 200 / Ana: 50", service 10
   → Ana ₱220.00, Ben ₱220.00, Total ₱440.00
4. "Ana: ₱1,200 / Ben: 800", service 10
   → Ana ₱1,320.00, Ben ₱880.00, Total ₱2,200.00
(" / " here means a new line.)
```

---

### Seed U4: PDF Copy-Paste Fixer

**Pitch:** Give it text copied from a PDF, and it instantly gives you clean paragraphs.

```
A tool that fixes text copied from a PDF: broken lines, split words, extra spaces.

Spec (apply in this order):
1. Treat Windows line breaks (\r\n) the same as \n.
2. Two or more line breaks in a row = a paragraph break. In the output, keep exactly one blank line between paragraphs.
3. Lines that start with "• ", "- ", "* ", or a number followed by ". " (like "1. ") are list items. Keep each list item on its own line.
4. Inside a paragraph, if a line ends with "-" and the next line starts with a lowercase letter, join them with no space and remove the "-".
5. Inside a paragraph, any other single line break becomes a space.
6. Collapse multiple spaces into one. Trim each line.
- Show the cleaned text with a Copy button, and a small note: "Fixed N line breaks".

Test cases (put these in the Self-test section; \n means a line break):
1. "This is a sen-\ntence that was\nbroken by a PDF." → "This is a sentence that was broken by a PDF."
2. "First para line one\nline two.\n\n\n\nSecond para." → "First para line one line two.\n\nSecond para."
3. "Too    many   spaces." → "Too many spaces."
4. "Steps:\n1. Open the file\n2. Save it" → "Steps:\n1. Open the file\n2. Save it"
5. "Line one\r\nline two" → "Line one line two"
```

---

### Seed U5: Working Days Counter

**Pitch:** Give it two dates and your holidays, and it instantly tells you how many working days you really have.

```
A tool that counts working days (Monday to Friday) between two dates, minus holidays you list.

Spec:
- Inputs: Start date and End date (date pickers), and a textarea "Holidays to skip" with one date per line in YYYY-MM-DD format.
- Count every Monday–Friday from start to end, INCLUDING both the start and end dates.
- Subtract listed holidays that fall on a weekday inside the range. Ignore duplicates, holidays on weekends, and holidays outside the range.
- IMPORTANT: parse dates as local dates by splitting the "YYYY-MM-DD" string into numbers. Do NOT use new Date("YYYY-MM-DD"), because that causes timezone bugs.
- Output: the working-day count in big text. Under it: calendar days in range, weekend days, and the holidays that were skipped.
- If end is before start, show "End date is before start date".

Test cases (put these in the Self-test section):
1. 2026-11-02 → 2026-11-06, no holidays → 5
2. 2026-11-06 → 2026-11-13, no holidays → 6
3. 2026-11-07 → 2026-11-08, no holidays → 0
4. 2026-11-02 → 2026-11-06, holiday 2026-11-04 → 4
5. 2026-11-02 → 2026-11-13, holiday 2026-11-08 (a Sunday) → 10
```

---

### Seed U6: 13th Month Pay Calculator

**Pitch:** Give it your basic salary and months worked, and it instantly gives you your 13th month pay with the math shown.

```
A 13th month pay calculator for the Philippines.

Rule: 13th month pay = total BASIC salary earned in the calendar year ÷ 12.
(Basic salary only. Not overtime, allowances, or bonuses. Say this in a small note.)

Spec:
- Input: one or more rows of "Monthly basic salary" and "Months at this salary" (decimals allowed, e.g. 6.5).
  An "Add row" button for salary changes during the year. Accept "₱" and commas.
- Output: the 13th month pay in big text, formatted ₱X,XXX.XX, rounded to the centavo.
- Under it, show the math with the user's numbers, e.g. "₱225,000.00 ÷ 12 = ₱18,750.00".
- If total months is more than 12, show a warning "That's more than 12 months" and no result.

Test cases (put these in the Self-test section):
1. 25,000 × 12 months → ₱25,000.00
2. 25,000 × 9 months → ₱18,750.00
3. 18,000 × 6.5 months → ₱9,750.00
4. 20,000 × 6 months + 24,000 × 6 months → ₱22,000.00
5. 30,000 × 13 months → warning "That's more than 12 months"
```

---

## Demo tips (5 minutes)

- **Open with the messy input.** Paste the ugliest example you have first.
- **Show the Self-test section.** A row of ✅ tells the judges a lot very fast.
- **Expect a surprise input.** A judge will hand you something you haven't seen. Try to break your own tool before they do.
