# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- **Three Core Actions Identified:**
  1. **Profile Management (Owner & Pet Onboarding)**: Register owners with specific availability limits and pets with unique attributes (species, breed, age, energy levels, and medical conditions).
  2. **Task Creation & Configuration**: Add or edit tasks with parameters including category, duration, priority level, recurrence pattern, and time-of-day preferences.
  3. **Automated Daily Schedule Generation & Conflict Resolution**: Process the pool of tasks to output a structured daily agenda within the owner's time constraints, providing natural-language reasoning for every prioritization or deferral decision.

- **Initial UML Design — Classes and Responsibilities:**
  - `Owner`: Manages caregiver identity (name, contact, daily availability) and holds the roster of associated pets. Acts as the entry point for the scheduling engine.
  - `Pet`: Stores per-pet demographics (species, breed, age, energy level, medical notes) and owns its task list. Medical notes directly influence scheduling priority — pets with conditions are scheduled ahead of healthy pets within the same priority tier.
  - `Task`: Represents a single unit of care with its duration, priority, time-slot preference, recurrence settings, and completion state. Designed to be self-contained so it can be moved between pools without mutation.
  - `DailyScheduler`: The scheduling engine. Compiles tasks from pets into a candidate pool, enforces the owner's time budget with a greedy sort, resolves time conflicts, and emits a full natural-language decision log for transparency.

**b. Design changes**

During implementation, two changes were made relative to the initial sketch:

1. **`task_pool` added to `DailyScheduler`**: The initial UML omitted the staging collection. Without it, `add_task_to_pool()` had nowhere to hold candidates before `generate_schedule()` ran. Adding `task_pool` made the pool → schedule pipeline explicit and enabled duplicate-task detection at insertion time.

2. **`Pet` now owns its task list**: Initially, tasks were to be managed externally and injected into the scheduler directly. During implementation it became clear that `Pet` should be the source of truth for its tasks (`Pet.tasks`, `add_task()`, `remove_task()`), with `load_from_owner()` as a convenience to pull all tasks into the scheduler pool. This made the ownership hierarchy clean: `Owner → Pet → Task`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints in order:

1. **Priority tier** (critical → high → medium → low): Non-negotiable care (medication, feeding) always runs before optional enrichment. This was the most important constraint because missing a medication has real consequences.
2. **Medical urgency**: Within the same priority tier, pets with `medical_notes` are scheduled before healthy pets. This prevents a healthy pet's tasks from consuming time that a medically fragile pet needs.
3. **Time-slot preference** (morning → specific HH:MM → anytime → evening): Used as a tie-breaker after priority and medical urgency, and as the display ordering after generation via `sort_by_time()`.

The daily time budget is the hard ceiling — no task is ever silently dropped; all overflow goes to `unscheduled_tasks` with a `DEFERRED` log entry explaining exactly why.

**b. Tradeoffs**

The scheduler uses a **global greedy sort**: all tasks are ranked once, then packed sequentially until the budget is exhausted. This means a 5-minute low-priority task that would easily fit after all high-priority tasks finish may still be deferred if a longer high-priority task consumed the last available minutes before the low-priority task was reached in the sorted order.

This tradeoff is intentional and appropriate here: correctness of care (critical medications always first, medical pets always prioritized) matters more than maximizing the raw count of completed tasks. A full knapsack optimizer would find the highest-value subset fitting the budget, but it adds O(n²) complexity and produces schedules that are harder for a non-technical pet owner to understand or predict. The greedy approach produces a deterministic, auditable schedule where the reasoning for every decision is logged in plain English.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across all phases of the project:

- **Design brainstorming (Phase 1)**: Asked the AI to critique the initial four-class UML — it identified that `task_pool` was missing from `DailyScheduler` and that the `Task → Pet` relationship in the UML implied ownership in the wrong direction.
- **Implementation (Phases 2–4)**: Used AI to scaffold method bodies from docstrings, then reviewed and adjusted the logic. The sorting key using `lambda` and `_slot_to_minutes()` was AI-suggested and adopted as-is after verifying it passed all mixed-slot ordering tests.
- **Testing (Phase 5)**: Prompted AI to audit the existing test suite for gaps. It identified that edge cases — empty pool, budget boundary conditions, `due_date=None` fallback for recurrence, and cross-pet slot conflicts — were all untested. These were added as the `TestEdgeCases` class.
- **Refactoring**: Asked AI to convert the original class-based implementation to Python dataclasses. Reviewed the output to ensure `__post_init__` was used correctly for `daily_time_limit_minutes` and that mutable defaults used `field(default_factory=...)`.

The most effective prompting pattern was: *"here is the method signature and docstring — implement it, then identify one edge case the implementation does not handle."* This kept AI output scoped and surfaced real gaps rather than generic suggestions.

**b. Judgment and verification**

When implementing `resolve_conflicts()`, the AI initially suggested raising a `ValueError` when two tasks claimed the same `HH:MM` slot. That was rejected: raising an exception would crash the schedule generation for a recoverable situation that a pet owner should simply be warned about. The design was changed to log a `CONFLICT` warning and continue — the scheduler never crashes on data it can reason about. The revised behavior was verified by writing `test_conflict_logged_for_same_timeslot`, which asserts the warning appears in the decision log without any exception being raised.

A second rejection: the AI suggested adding `__slots__` to the dataclasses for memory efficiency. Given that a typical owner has 2–5 pets and 10–20 tasks, memory optimization at that scale is premature and `__slots__` conflicts with dataclass inheritance patterns that may be needed later. It was not adopted.

**c. Working across phases with an AI assistant**

Using a consistent, phase-structured workflow — design → implement → test → refactor → UI — kept each session focused. The AI was briefed on the current phase goal at the start of each session rather than carrying all prior context forward. This prevented earlier design decisions from contaminating later refactoring (e.g., the AI proposing to revert the dataclass migration when it wasn't relevant to Phase 5 testing).

The key discipline was treating AI output as a first draft requiring judgment, not a final answer. Every method generated by AI was read, compared against the docstring contract, and verified with at least one test before being accepted. When AI suggested something architecturally questionable (like the `ValueError` above), the right call was to articulate *why* the suggestion violated the design contract and override it.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers 48 behaviors across six areas:

- **Task lifecycle**: `mark_as_completed()` changes status and is idempotent; `is_urgent()` returns correct results for all four priority levels; `update_task_details()` updates allowed fields and rejects protected ones (`task_id`, `is_completed`).
- **Pet & Owner management**: Adding/removing pets and tasks, duplicate prevention, `get_all_tasks()` aggregation across multiple pets.
- **Scheduling core**: Priority ordering, medical-urgency prioritization within a tier, time-budget enforcement (tasks deferred not dropped), completed tasks skipped with a log entry, duplicate task pool detection, `load_from_owner()` correctly populates the pool.
- **Sorting & filtering**: HH:MM chronological ordering, named-slot ordering (morning/anytime/evening), mixed HH:MM + named slots interleaving, pet-name filter, completion-status filter, combined filter.
- **Recurring tasks**: Daily and weekly `due_date` deltas, property inheritance, new `task_id` per occurrence (not a reference to the original), `due_date=None` fallback to today, correct pet attachment.
- **Edge cases**: Empty pool, pet with no tasks, owner with no pets, budget exactly met vs. one minute over, cross-pet same-slot conflict, empty sort input, stable sort with equal slots.

These tests mattered because the scheduler makes implicit promises — medications always run before walks, medical pets always get priority, nothing is silently dropped — that are easy to break with a small logic change. Having explicit tests for each promise makes regressions immediately visible.

**b. Confidence**

48/48 tests pass in 0.02 seconds. Confidence is high for the core scheduling algorithm, sort/filter operations, and recurrence rollover.

Edge cases that would be tested next with more time:
- Tasks with `duration_minutes = 0` (degenerate input)
- Recurrence with an unknown `recurrence_pattern` string (currently returns `None` silently — could log a warning)
- Very large task pools (100+ tasks) to verify O(n log n) sort performance holds
- `apply_recurring_tasks()` called twice without clearing the pool (idempotency under repeated calls)

---

## 5. Reflection

**a. What went well**

The decision-log architecture is the part of this project that worked best. Logging every scheduling decision as a human-readable string (`SCHEDULED`, `DEFERRED`, `CONFLICT`, `RECURRING`) made the system transparent at the terminal level and trivially surfaceable in the Streamlit UI. It also made debugging almost trivial — if a task appeared in the wrong place, the log showed exactly what sort key caused it. This pattern — building observability into the core engine rather than adding it as an afterthought — is something worth carrying into future projects.

**b. What you would improve**

The `task_pool` is a flat list of dicts (`{"task": Task, "pet": Pet}`). This works for a single day with a small number of tasks, but it is not a good data structure for querying or filtering at scale. A future iteration would replace it with a proper indexed structure (e.g., a dict keyed by `task_id`, or a small dataclass like `PoolEntry`) so that lookups and deduplication are O(1) rather than O(n). The filter and sort APIs would remain the same externally — only the internal storage would change.

A second improvement: the scheduler is stateless between days. Running it a second time on the same `DailyScheduler` instance overwrites `scheduled_tasks` and `decision_log`. Adding a `clear()` method and documenting the intended lifecycle (instantiate fresh per day, or call `clear()` before re-running) would prevent subtle bugs when the scheduler is reused across multiple calls.

**c. Key takeaway**

The most important thing this project demonstrated about working with AI is that **the architect's job does not disappear — it moves earlier**. When you can generate a working method body in seconds, the bottleneck is no longer writing code; it is knowing what the code should *do*, how it should *behave at the boundary*, and what *invariants* it must preserve. Every AI suggestion that was rejected in this project was rejected on architectural grounds (ownership model, error handling contract, premature optimization), not on syntactic ones. The clearer your design constraints are before you prompt, the more useful the AI output is — and the easier it is to spot when the AI has subtly violated them.
