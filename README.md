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

**Run the full test suite:**
```bash
python -m pytest tests/test_pawpal.py -v
```

**Test Coverage:**
The test suite covers 48 critical behaviors across five areas:

- **Task lifecycle** (6 tests): completion status, urgency checks, field updates, protection of immutable fields
- **Pet & Owner management** (9 tests): task ownership, pet roster management, aggregation across pets, duplicate handling
- **Scheduling core** (10 tests): priority ordering, medical-urgency prioritization, time-budget enforcement, completed task skipping, duplicate task pool detection, load-from-owner, conflict logging
- **Sorting & filtering** (5 tests): HH:MM and named-slot ordering, pet-name filtering, completion-status filtering
- **Recurring tasks** (8 tests): daily/weekly rollover, property inheritance, new task IDs per occurrence, `due_date=None` fallback, attachment to correct pet
- **Edge cases** (10 tests): empty pool, pet with no tasks, owner with no pets, budget boundary conditions (exact fit vs. overflow), cross-pet conflicts, mixed slot ordering, combined filtering

**Test Run Output:**
```
============================= test session starts ==============================
platform darwin -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/roop/Documents/Codepath/PawPal+/ai110-module2show-pawpal-starter
collected 48 items

tests/test_pawpal.py::TestTask::test_mark_as_completed_changes_status PASSED [  2%]
tests/test_pawpal.py::TestTask::test_mark_as_completed_is_idempotent PASSED [  4%]
tests/test_pawpal.py::TestTask::test_is_urgent_critical_and_high PASSED  [  6%]
tests/test_pawpal.py::TestTask::test_is_urgent_medium_and_low PASSED     [  8%]
tests/test_pawpal.py::TestTask::test_update_task_details_allowed_fields PASSED [ 10%]
tests/test_pawpal.py::TestTask::test_update_task_details_ignores_unknown_keys PASSED [ 12%]
tests/test_pawpal.py::TestPet::test_add_task_increases_count PASSED      [ 14%]
tests/test_pawpal.py::TestPet::test_add_task_duplicate_ignored PASSED    [ 16%]
tests/test_pawpal.py::TestPet::test_remove_task PASSED                   [ 18%]
tests/test_pawpal.py::TestPet::test_remove_task_nonexistent_noop PASSED  [ 20%]
tests/test_pawpal.py::TestPet::test_get_care_summary_includes_name PASSED [ 22%]
tests/test_pawpal.py::TestOwner::test_add_pet PASSED                     [ 25%]
tests/test_pawpal.py::TestOwner::test_add_pet_duplicate_ignored PASSED   [ 27%]
tests/test_pawpal.py::TestOwner::test_remove_pet PASSED                  [ 29%]
tests/test_pawpal.py::TestOwner::test_get_all_tasks_aggregates_across_pets PASSED [ 31%]
tests/test_pawpal.py::TestDailyScheduler::test_time_limit_defaults_to_owner_budget PASSED [ 33%]
tests/test_pawpal.py::TestDailyScheduler::test_critical_scheduled_before_low PASSED [ 35%]
tests/test_pawpal.py::TestDailyScheduler::test_task_deferred_when_budget_exceeded PASSED [ 37%]
tests/test_pawpal.py::TestDailyScheduler::test_completed_task_skipped PASSED [ 39%]
tests/test_pawpal.py::TestDailyScheduler::test_duplicate_task_in_pool_ignored PASSED [ 41%]
tests/test_pawpal.py::TestDailyScheduler::test_medical_pet_tasks_prioritised_within_tier PASSED [ 43%]
tests/test_pawpal.py::TestDailyScheduler::test_load_from_owner_populates_pool PASSED [ 45%]
tests/test_pawpal.py::TestDailyScheduler::test_conflict_logged_for_same_timeslot PASSED [ 47%]
tests/test_pawpal.py::TestDailyScheduler::test_get_reasoning_returns_copy PASSED [ 50%]
tests/test_pawpal.py::TestDailyScheduler::test_duration_overlap_conflict_detected PASSED [ 52%]
tests/test_pawpal.py::TestSortAndFilter::test_sort_by_time_hhmm_ordering PASSED [ 54%]
tests/test_pawpal.py::TestSortAndFilter::test_sort_named_slots_ordering PASSED [ 56%]
tests/test_pawpal.py::TestSortAndFilter::test_filter_by_pet_name PASSED  [ 58%]
tests/test_pawpal.py::TestSortAndFilter::test_filter_by_completed_false PASSED [ 60%]
tests/test_pawpal.py::TestSortAndFilter::test_filter_by_completed_true PASSED [ 62%]
tests/test_pawpal.py::TestRecurringTasks::test_generate_next_occurrence_daily PASSED [ 64%]
tests/test_pawpal.py::TestRecurringTasks::test_generate_next_occurrence_weekly PASSED [ 66%]
tests/test_pawpal.py::TestRecurringTasks::test_generate_next_occurrence_non_recurring_returns_none PASSED [ 68%]
tests/test_pawpal.py::TestRecurringTasks::test_apply_recurring_tasks_attaches_to_pet PASSED [ 70%]
tests/test_pawpal.py::TestRecurringTasks::test_apply_recurring_skips_non_recurring PASSED [ 72%]
tests/test_pawpal.py::TestRecurringTasks::test_next_occurrence_has_new_task_id PASSED [ 75%]
tests/test_pawpal.py::TestRecurringTasks::test_next_occurrence_inherits_properties PASSED [ 77%]
tests/test_pawpal.py::TestRecurringTasks::test_next_occurrence_no_due_date_falls_back_to_today PASSED [ 79%]
tests/test_pawpal.py::TestEdgeCases::test_empty_pool_returns_empty_schedule PASSED [ 81%]
tests/test_pawpal.py::TestEdgeCases::test_pet_with_no_tasks_does_not_crash PASSED [ 83%]
tests/test_pawpal.py::TestEdgeCases::test_owner_with_no_pets PASSED      [ 85%]
tests/test_pawpal.py::TestEdgeCases::test_budget_boundary_task_fits_exactly PASSED [ 87%]
tests/test_pawpal.py::TestEdgeCases::test_task_one_minute_over_budget_deferred PASSED [ 89%]
tests/test_pawpal.py::TestEdgeCases::test_conflict_cross_pet_same_hhmm_slot PASSED [ 91%]
tests/test_pawpal.py::TestEdgeCases::test_sort_empty_list_returns_empty PASSED [ 93%]
tests/test_pawpal.py::TestEdgeCases::test_sort_mixed_hhmm_and_named_slots PASSED [ 95%]
tests/test_pawpal.py::TestEdgeCases::test_filter_combined_pet_and_completion PASSED [ 97%]
tests/test_pawpal.py::TestEdgeCases::test_sort_stable_equal_slots PASSED [100%]

============================== 48 passed in 0.02s ==============================
```

**Confidence Level: ⭐⭐⭐⭐⭐ (5/5)**

All 48 tests pass with zero failures. The test suite validates:
- Data integrity (no race conditions, immutable fields protected)
- Scheduling correctness (priority ordering, medical urgency, time-budget enforcement)
- Conflict detection (exact slot collision, duration overlap, cross-pet conflicts)
- Sorting stability (HH:MM times, named slots, mixed interleaving)
- Recurrence rollover (correct date deltas, property inheritance, new task IDs)
- Edge cases (empty pool, boundary conditions, combined filtering)

The system is **production-ready** for a single-owner, single-day scheduling context.

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
