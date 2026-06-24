"""
PawPal+ demo script — exercises all Phase 4 features in the terminal.

Run:  python main.py
"""

from datetime import date
from pawpal_system import DailyScheduler, Owner, Pet, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hm(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def print_section(title: str) -> None:
    print(f"\n{'─' * 56}")
    print(f"  {title}")
    print(f"{'─' * 56}")


def print_task_list(entries: list, label: str = "") -> None:
    if label:
        print(f"\n  {label}")
    for e in entries:
        t = e["task"]
        start = e.get("start_minute")
        time_str = f"  {_hm(start)}" if start is not None else "      "
        status = "✓" if t.is_completed else "·"
        print(
            f"    {status} {time_str}  [{t.priority:8s}] {t.title:30s} "
            f"({t.duration_minutes}min, slot={t.time_slot_preference}) — {e['pet'].name}"
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def build_demo() -> tuple[Owner, Pet, Pet]:
    owner = Owner("Jordan", "jordan@pawpal.io", available_hours_per_day=2.5)  # 150 min

    biscuit = Pet("Biscuit", "dog", "Golden Retriever", 36,
                  energy_level="high", medical_notes=["arthritis"])
    mochi = Pet("Mochi", "cat", "Siamese", 18, energy_level="medium")

    # Tasks added intentionally OUT OF TIME ORDER to exercise sort_by_time()
    biscuit.add_task(Task("Evening walk",          "walk",        25, priority="medium",
                          time_slot_preference="evening"))
    biscuit.add_task(Task("Arthritis medication",  "medication",   5, priority="critical",
                          time_slot_preference="08:00",
                          is_recurring=True, recurrence_pattern="daily",
                          due_date=date.today()))
    biscuit.add_task(Task("Morning walk",          "walk",        30, priority="high",
                          time_slot_preference="morning"))
    biscuit.add_task(Task("Grooming session",      "grooming",    45, priority="low",
                          time_slot_preference="anytime"))

    mochi.add_task(Task("Breakfast feeding", "feeding",    10, priority="critical",
                        time_slot_preference="08:00",       # ← same slot as Biscuit's med
                        is_recurring=True, recurrence_pattern="daily",
                        due_date=date.today()))
    mochi.add_task(Task("Enrichment play",   "enrichment", 20, priority="medium",
                        time_slot_preference="15:30"))
    mochi.add_task(Task("Evening feeding",   "feeding",    10, priority="high",
                        time_slot_preference="18:00",
                        is_recurring=True, recurrence_pattern="daily",
                        due_date=date.today()))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner, biscuit, mochi


def main() -> None:
    owner, biscuit, mochi = build_demo()

    print_section("Pet Profiles")
    for pet in owner.get_all_pets():
        print(f"  {pet.get_care_summary()}")

    # ------------------------------------------------------------------
    # 4.2 — Sort & Filter demo (pre-schedule)
    # ------------------------------------------------------------------
    scheduler = DailyScheduler(owner, date.today())
    scheduler.load_from_owner()

    print_section("4.2 — All tasks, sorted by time slot (pre-schedule)")
    sorted_pool = scheduler.sort_by_time(scheduler.task_pool)
    print_task_list(sorted_pool)

    print_section("4.2 — Filtered: Mochi's pending tasks only")
    mochi_pending = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    print_task_list(mochi_pending)

    # ------------------------------------------------------------------
    # Generate schedule
    # ------------------------------------------------------------------
    print_section("Generating Daily Schedule")
    scheduler.generate_schedule()

    print_section("Scheduled tasks (sorted by time slot)")
    sorted_schedule = scheduler.sort_by_time()
    print_task_list(sorted_schedule, "")

    if scheduler.unscheduled_tasks:
        print(f"\n  Deferred ({len(scheduler.unscheduled_tasks)}):")
        for t in scheduler.unscheduled_tasks:
            print(f"    - {t.title} ({t.duration_minutes}min, priority={t.priority})")

    # ------------------------------------------------------------------
    # 4.4 — Conflict detection output
    # ------------------------------------------------------------------
    conflicts = [l for l in scheduler.get_reasoning() if l.startswith("CONFLICT")]
    if conflicts:
        print_section("4.4 — Conflict Warnings")
        for c in conflicts:
            print(f"  ⚠  {c}")

    # ------------------------------------------------------------------
    # 4.3 — Recurring tasks: mark some complete, roll over
    # ------------------------------------------------------------------
    print_section("4.3 — Mark recurring tasks complete, generate next occurrences")
    for entry in scheduler.task_pool:
        if entry["task"].is_recurring:
            entry["task"].mark_as_completed()
            print(f"  Marked complete: {entry['task'].title} [{entry['pet'].name}]")

    new_tasks = scheduler.apply_recurring_tasks()
    print(f"\n  Next occurrences created: {len(new_tasks)}")
    for t in new_tasks:
        print(f"    → {t.title}  due {t.due_date}")

    # ------------------------------------------------------------------
    # Decision log
    # ------------------------------------------------------------------
    print_section("Full Decision Log")
    for line in scheduler.get_reasoning():
        print(f"  {line}")


if __name__ == "__main__":
    main()
