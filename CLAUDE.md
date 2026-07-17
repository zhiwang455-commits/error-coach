# CLAUDE.md — Project Blueprint

> Put this file in the project root. Claude Code reads it automatically on every session.
> Teammates: read sections 1–3 before writing any code.

---

## 1. What This Is

An error-learning system for Thai programming beginners.

**One line:**
> ChatGPT forgives the same mistake every day. We remember it.

**Core loop:**
```
Student pastes error → AI classifies + explains in Thai + rebuilds causal trace
                     → Write to CSV
                     → Count "this is your Nth time"
                     → Targeted practice problems
                     → Teacher sees class-wide aggregate
```

## 2. The Moat (the one thing that can't be copied)

**"This is the 3rd time you've made this mistake."**

- Thai explanation, causal trace, practice problems → all prompt engineering, copyable in a day
- **"3rd time" → built from accumulated history. Cannot be copied.**
- Teacher view and cost caching are *downstream* of remembering — not separate features.

One error is noise. Three identical errors is **a concept gap speaking**.
The entire point of this product: **turn noise into diagnosis.**

## 3. Explicitly NOT Doing (scope guard)

- ❌ Auto-capturing tracebacks (`sys.settrace` / `subprocess`) → **manual paste is enough**
- ❌ General execution visualizer (do NOT rebuild Python Tutor) → only replay the **moment of failure**
- ❌ Postgres / auth / Docker / deployment → **one CSV is enough**
- ❌ Slide generator → cut
- ❌ Mobile / offline → not in one week

---

## 4. Data Schema (lock this now — changing fields later invalidates collected data)

`errors.csv`

| Column | Notes |
|---|---|
| `timestamp` | |
| `student_id` | `student_01` — **never real names** |
| `error_type` | **must come from the closed list below** |
| `raw_error` | original traceback |
| `code_snippet` | student's code — **do not skip this**, the teacher view depends on it |

## 5. Closed Error Taxonomy (the product lives or dies here)

If the AI describes error types freely, the same bug gets written three different ways →
**frequency counting breaks → the product is dead.**

```python
ERROR_TYPES = [
    "undefined_variable",
    "scope_issue",
    "return_vs_print",
    "type_mismatch",
    "indentation_error",
    "index_out_of_range",
    "loop_logic_error",
    "function_argument_error",
    "dict_list_operation_error",
    "other",
]
```

**Rules:**
- Hard-code this list into the prompt; require the AI to return one value verbatim
- Add a guard in code: value not in list → force to `"other"`
- Finalize the taxonomy from the **40 real student errors we collect** — not from imagination

## 6. Prompt Template

```
You are a teaching assistant for Thai programming beginners.

Analyze the code and error below. Return ONLY JSON — no other text, no markdown fences.

Format:
{
  "error_type": "exactly one of: [undefined_variable, scope_issue, return_vs_print, type_mismatch, indentation_error, index_out_of_range, loop_logic_error, function_argument_error, dict_list_operation_error, other]",
  "thai_explanation": "simple Thai a beginner can understand",
  "call_trace": ["step 1", "step 2", "step 3 ← the error is here"],
  "concept": "the concept the student hasn't actually learned"
}

Code:
{code}

Error:
{error}
```

---

## 7. Build Steps (each step must run before moving on)

### Step 0 · API Hello World 【highest priority — write NO other code until this runs】
20 lines: send one sentence to the Claude API, print the response. Nothing else.

### Step 1 · Manual input
```python
code = input("Paste your code: ")
error = input("Paste your error: ")
```
No auto-capture. Judges don't care.

### Step 2 · Force structured output 【hardest — budget time for it】
Use the prompt above until `json.loads()` succeeds.

⚠️ The AI often adds "Sure, here's the result:" outside the JSON → `json.loads()` explodes.
Write a cleaning function: strip ` ```json ` fences, take from first `{` to last `}`.
**This step eats the most time. That's normal.**

### Step 2.5 · Eval: is the classifier actually right? 【easy to skip — skip it and everything downstream is garbage】

**The question nobody asks: how do we know the AI classified correctly?**

If accuracy is 50%, then frequency counts, the "3rd time" trigger, the teacher view, the practice problems — **all of it is counting noise.**

**How (30 minutes):**
1. Take the 40 collected real errors and **hand-label them ourselves** → this is ground truth
2. Run the AI over the same 40
3. Count how many it got right

```python
accuracy = correct / 40
```

It's one division.

**Two payoffs:**
- **Engineering:** low accuracy → we know to fix the prompt, instead of guessing
- **Pitch:** "Our classifier hits 85% accuracy on 40 hand-labeled real student errors."
  — this is **verifiable**, which beats any amount of rhetoric

⚠️ **The taxonomy must grow out of these 40 real errors — not out of our imagination.**
Hand-labeling may reveal that `indentation_error` never occurs, while "forgot the colon `:`" is a third of all cases.
**A guessed taxonomy destroys the frequency counts.**

### Step 3 · Write to CSV
Append mode, five fields.

### Step 4 · Count the "3rd time" 【the moat — it's just a for loop】
```python
count = 0
for row in rows:
    if row["student_id"] == sid and row["error_type"] == etype:
        count += 1
```
**Once this works, the product exists.**

### Step 5 · Generate targeted practice
Send the student's top error type back to the API: "write 3 practice problems in Thai for this error."

### Step 6 · Teacher view
Same CSV, group by `error_type` → one sentence + one bar chart.
> "68% of the class is stuck on scope and return-vs-print this week."

### Step 7 (if time) · Caching
Same `error_type` + similar code → reuse the stored explanation, skip the API call.
Demo: **student count rising, API calls flat.**
This chart is the *only* evidence for our accessibility story.

---

## 8. How We Use Claude Code

**Hand-written by us (~100 lines — the heart):**
- API call
- Prompt + closed taxonomy (**this is judgment, not code — never outsource it**)
- CSV read/write
- The "3rd time" counter

**Delegated to Claude Code (the shell):**
- Streamlit UI (three parts: input box / result card / teacher view)
- Charts (frequency bars, cost curve)
- JSON parsing fallbacks
- README

**When prompting Claude Code:**
1. One small task at a time. **Never say "build the whole project."**
2. Always give it our existing schema (CSV column names), or it invents its own
3. Constrain libraries (streamlit + pandas only)
4. Require comments explaining every line

**Hard rule: every line Claude Code writes, we must be able to read and explain.**
At 2am when it breaks, or when a judge asks why we designed it this way, only code we understand can save us.

## 8.5 Learning Mode (standing instruction to Claude Code)

**We are beginner programmers learning through this project. Always:**

- **Comment every line in both English and Chinese**, explaining **WHY it's written this way**, not what it does
  - ❌ `# open the file`
  - ✅ `# Use 'a' not 'w' — 'w' wipes history, which kills the entire moat`
- **Stop and explain any syntax we may not have seen** before putting it in the code
- **Never give more than 30 lines at once** — past 30 lines we scroll instead of read

**Also:**
- When we're stuck: **give direction and hints, not the answer**
- When we state our understanding: **point out what's wrong**, don't just hand over the correct version
- Code we cannot explain to someone else does not stay in this project

---

## 9. Demo Survival Rules

- **An empty database = a dead demo.** The 40 collected real errors must be pre-loaded into the CSV as seed data.
- Opening line of the demo: **"This is real error data from 8 CMU students."**
- The judges must see the **"⚠️ 3rd time"** line — that is the climax of the demo.

## 10. The Question We Must Answer

> **"Why wouldn't a student just use ChatGPT?"**

> ChatGPT doesn't remember what they got wrong, and it can't tell the teacher where the class is stuck.

---

## 11. Six-Day Plan

| Day | Task |
|---|---|
| 1 | Step 0 (API working) + send out Google Form to collect errors |
| 2 | Step 2 (hardest) |
| 3 | Step 3 + 4 ← **product exists ✅ critical day** |
| 4 | Step 5 + finalize taxonomy + load seed data |
| 5 | Claude Code builds the UI |
| 6 | Rehearse pitch + **buffer (for firefighting, not new features)** |

**Day 3 is the critical day.** If the loop runs by end of Day 3, we're safe — everything after is bonus.
