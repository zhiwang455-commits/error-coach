# error-coach 🧭

> ChatGPT forgives the same mistake every day. **We remember it.**

An error-learning system for Thai programming beginners. A student pastes a
Python error → the AI classifies it against a **closed taxonomy** and explains
it in Thai + English → every error is logged → the system counts
**"this is your 3rd time"** → the teacher sees where the whole class is stuck.

## Run it

```bash
cd ~/error-coach
./venv/bin/streamlit run app.py
# opens http://localhost:8501
```

Requires `DEEPSEEK_API_KEY` in the environment (already in `~/.bashrc`).

## Files

| File | What it is |
|---|---|
| `coach.py` | **The heart.** classify / log / count / practice / cache. Read this first. |
| `app.py` | Streamlit shell: student view + teacher view. |
| `convert_form.py` | Google Form CSV → anonymized `errors.csv` + `labeling_sheet.csv`. |
| `eval.py` | Step 2.5: accuracy = correct / hand-labeled. The pitch number. |
| `errors.csv` | The database. ⚠️ **Currently DEMO data** — replace before judging (below). |
| `cache.json` | Step 7 cache: identical questions never hit the API twice. |
| `step0.py` `step2.py` | Learning checkpoints from Day 1. Keep for the story. |
| `CLAUDE.md` | The blueprint. All design decisions live there. |

## Before the demo (Day 4 checklist)

1. Download form responses → `form_responses.csv`
2. `rm errors.csv cache.json` ← deletes the demo data
3. `./venv/bin/python convert_form.py` ← real data in, anonymized
4. Hand-fill `hand_label` in `labeling_sheet.csv`, then `./venv/bin/python eval.py`
   → gives the line: *"X% accuracy on 40 hand-labeled real student errors."*
5. Revisit the taxonomy (`ERROR_TYPES` in `coach.py`) against what the 40 errors
   actually show — see `taxonomy_candidates.md` rule: 3+ real occurrences.

## The answer to "why not just ChatGPT?"

ChatGPT doesn't remember what you got wrong, and it can't tell the teacher
where the class is stuck. The memory (`errors.csv`) is the product.
