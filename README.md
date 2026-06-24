# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Biscuit (dog, Golden Retriever) | Age: 36mo | Energy: high | Medical notes: arthritis
Mochi (cat, Siamese) | Age: 18mo | Energy: medium | Medical notes: None

======================================================
  Today's Schedule — 2026-06-23
  Owner: Jordan (budget: 120 min)
======================================================
  00:00  [critical] Arthritis medication (5min) — Biscuit
  00:05  [critical] Feeding (10min) — Mochi
  00:15  [high    ] Morning walk (30min) — Biscuit
  00:45  [medium  ] Evening walk (25min) — Biscuit
  01:10  [medium  ] Enrichment play (20min) — Mochi

  Deferred (1):
    - Grooming session (45min, low)

  Reasoning:
    SCHEDULED 'Arthritis medication' [Biscuit] priority=critical, 5min, slot=morning, starts at min 0.
    SCHEDULED 'Feeding' [Mochi] priority=critical, 10min, slot=morning, starts at min 5.
    SCHEDULED 'Morning walk' [Biscuit] priority=high, 30min, slot=morning, starts at min 15.
    SCHEDULED 'Evening walk' [Biscuit] priority=medium, 25min, slot=evening, starts at min 45.
    SCHEDULED 'Enrichment play' [Mochi] priority=medium, 20min, slot=anytime, starts at min 70.
    DEFERRED  'Grooming session' [Biscuit]: needs 135 min total, limit is 120 min.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature              | Method(s)                                          | Notes |
| -------------------- | -------------------------------------------------- | ----- |
| **Task sorting**     | `DailyScheduler.sort_by_time(entries?)`            | Sorts any `{task, pet}` list by `time_slot_preference`. Named slots (`morning`, `anytime`, `evening`) map to representative clock times (06:00 / 12:00 / 18:00) so they interleave naturally with explicit `HH:MM` tasks. Uses a `lambda` key over `_slot_to_minutes()`. |
| **Priority sorting** | `DailyScheduler.generate_schedule()`               | Greedy sort: critical → high → medium → low. Within each priority tier, pets with `medical_notes` are scheduled first. Tie-breaks by slot time. |
| **Filtering**        | `DailyScheduler.filter_tasks(pet_name, completed)` | Filters any `{task, pet}` list by pet name (case-insensitive) and/or completion status. Both parameters are optional and composable. |
| **Conflict handling**| `DailyScheduler.resolve_conflicts()`               | Two-pass detection: (1) exact `HH:MM` slot collision; (2) duration-overlap check on `[start, start+duration)` intervals. Returns warning strings and appends to the decision log without crashing. |
| **Recurring tasks**  | `Task.generate_next_occurrence()`, `DailyScheduler.apply_recurring_tasks()` | `generate_next_occurrence()` returns a fresh Task with `due_date = original + timedelta`. `apply_recurring_tasks()` iterates completed recurring tasks, generates the next instance, and attaches it to the owning Pet. Supports `daily` (+1 day) and `weekly` (+7 days). |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: `<!-- Insert a screenshot or link to a demo video here -->`
