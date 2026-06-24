"""Demo script — verifies backend logic end-to-end before connecting to the UI."""

from datetime import date
from pawpal_system import DailyScheduler, Owner, Pet, Task


def build_demo() -> tuple[Owner, list[Pet]]:
    owner = Owner("Jordan", "jordan@pawpal.io", available_hours_per_day=2.0)

    biscuit = Pet("Biscuit", "dog", "Golden Retriever", 36,
                  energy_level="high", medical_notes=["arthritis"])
    mochi = Pet("Mochi", "cat", "Siamese", 18, energy_level="medium")

    biscuit.add_task(Task("Arthritis medication", "medication", 5,
                          priority="critical", time_slot_preference="morning"))
    biscuit.add_task(Task("Morning walk", "walk", 30,
                          priority="high", time_slot_preference="morning"))
    biscuit.add_task(Task("Evening walk", "walk", 25,
                          priority="medium", time_slot_preference="evening"))
    biscuit.add_task(Task("Grooming session", "grooming", 45,
                          priority="low", time_slot_preference="anytime"))

    mochi.add_task(Task("Feeding", "feeding", 10,
                        priority="critical", time_slot_preference="morning",
                        is_recurring=True, recurrence_pattern="daily"))
    mochi.add_task(Task("Enrichment play", "enrichment", 20,
                        priority="medium", time_slot_preference="anytime"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner, [biscuit, mochi]


def print_schedule(scheduler: DailyScheduler) -> None:
    print(f"\n{'='*54}")
    print(f"  Today's Schedule — {scheduler.target_date}")
    print(f"  Owner: {scheduler.owner.name} "
          f"(budget: {scheduler.daily_time_limit_minutes} min)")
    print(f"{'='*54}")

    if not scheduler.scheduled_tasks:
        print("  No tasks scheduled.")
    else:
        for entry in scheduler.scheduled_tasks:
            t = entry["task"]
            start = entry["start_minute"]
            h, m = divmod(start, 60)
            print(f"  {h:02d}:{m:02d}  [{t.priority:8s}] {t.title} "
                  f"({t.duration_minutes}min) — {entry['pet'].name}")

    if scheduler.unscheduled_tasks:
        print(f"\n  Deferred ({len(scheduler.unscheduled_tasks)}):")
        for t in scheduler.unscheduled_tasks:
            print(f"    - {t.title} ({t.duration_minutes}min, {t.priority})")

    print(f"\n  Reasoning:")
    for line in scheduler.get_reasoning():
        print(f"    {line}")
    print()


def main() -> None:
    owner, pets = build_demo()

    for pet in pets:
        print(pet.get_care_summary())

    scheduler = DailyScheduler(owner, date.today())
    scheduler.load_from_owner()
    scheduler.generate_schedule()
    print_schedule(scheduler)


if __name__ == "__main__":
    main()
