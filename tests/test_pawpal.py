"""Tests for pawpal_system — scheduling correctness and data-integrity contracts."""

import sys
from pathlib import Path

# Add project root to sys.path to allow running tests from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from datetime import date
from pawpal_system import DailyScheduler, Owner, Pet, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner() -> Owner:
    return Owner("Jordan", "jordan@test.com", available_hours_per_day=1.0)  # 60 min


@pytest.fixture
def pet_healthy() -> Pet:
    return Pet("Mochi", "cat", "Siamese", 18)


@pytest.fixture
def pet_medical() -> Pet:
    return Pet("Biscuit", "dog", "Golden Retriever", 36,
               medical_notes=["arthritis"])


@pytest.fixture
def scheduler(owner: Owner) -> DailyScheduler:
    return DailyScheduler(owner, date.today())


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class TestTask:
    def test_mark_as_completed_changes_status(self):
        task = Task("Walk", "walk", 20, priority="high")
        assert task.is_completed is False
        task.mark_as_completed()
        assert task.is_completed is True

    def test_mark_as_completed_is_idempotent(self):
        task = Task("Walk", "walk", 20)
        task.mark_as_completed()
        task.mark_as_completed()
        assert task.is_completed is True

    def test_is_urgent_critical_and_high(self):
        assert Task("Med", "medication", 5, priority="critical").is_urgent() is True
        assert Task("Walk", "walk", 20, priority="high").is_urgent() is True

    def test_is_urgent_medium_and_low(self):
        assert Task("Play", "enrichment", 15, priority="medium").is_urgent() is False
        assert Task("Groom", "grooming", 30, priority="low").is_urgent() is False

    def test_update_task_details_allowed_fields(self):
        task = Task("Walk", "walk", 20, priority="low")
        task.update_task_details({"priority": "high", "duration_minutes": 30})
        assert task.priority == "high"
        assert task.duration_minutes == 30

    def test_update_task_details_ignores_unknown_keys(self):
        task = Task("Walk", "walk", 20)
        task.update_task_details({"task_id": "hacked", "is_completed": True})
        assert task.is_completed is False  # protected field not mutated


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task_increases_count(self, pet_healthy: Pet):
        assert len(pet_healthy.tasks) == 0
        pet_healthy.add_task(Task("Feeding", "feeding", 10))
        assert len(pet_healthy.tasks) == 1

    def test_add_task_duplicate_ignored(self, pet_healthy: Pet):
        task = Task("Feeding", "feeding", 10)
        pet_healthy.add_task(task)
        pet_healthy.add_task(task)
        assert len(pet_healthy.tasks) == 1

    def test_remove_task(self, pet_healthy: Pet):
        task = Task("Play", "enrichment", 15)
        pet_healthy.add_task(task)
        pet_healthy.remove_task(task.task_id)
        assert len(pet_healthy.tasks) == 0

    def test_remove_task_nonexistent_noop(self, pet_healthy: Pet):
        pet_healthy.remove_task("nonexistent-id")  # should not raise

    def test_get_care_summary_includes_name(self, pet_medical: Pet):
        summary = pet_medical.get_care_summary()
        assert "Biscuit" in summary
        assert "arthritis" in summary


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class TestOwner:
    def test_add_pet(self, owner: Owner, pet_healthy: Pet):
        owner.add_pet(pet_healthy)
        assert len(owner.get_all_pets()) == 1

    def test_add_pet_duplicate_ignored(self, owner: Owner, pet_healthy: Pet):
        owner.add_pet(pet_healthy)
        owner.add_pet(pet_healthy)
        assert len(owner.get_all_pets()) == 1

    def test_remove_pet(self, owner: Owner, pet_healthy: Pet):
        owner.add_pet(pet_healthy)
        owner.remove_pet(pet_healthy.pet_id)
        assert len(owner.get_all_pets()) == 0

    def test_get_all_tasks_aggregates_across_pets(
        self, owner: Owner, pet_healthy: Pet, pet_medical: Pet
    ):
        pet_healthy.add_task(Task("Feeding", "feeding", 10))
        pet_medical.add_task(Task("Medication", "medication", 5))
        pet_medical.add_task(Task("Walk", "walk", 30))
        owner.add_pet(pet_healthy)
        owner.add_pet(pet_medical)
        assert len(owner.get_all_tasks()) == 3


# ---------------------------------------------------------------------------
# DailyScheduler
# ---------------------------------------------------------------------------

class TestDailyScheduler:
    def test_time_limit_defaults_to_owner_budget(self, scheduler: DailyScheduler):
        assert scheduler.daily_time_limit_minutes == 60

    def test_critical_scheduled_before_low(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        low = Task("Grooming", "grooming", 10, priority="low")
        critical = Task("Medication", "medication", 5, priority="critical")
        scheduler.add_task_to_pool(low, pet_healthy)
        scheduler.add_task_to_pool(critical, pet_healthy)
        plan = scheduler.generate_schedule()
        assert plan[0]["task"].task_id == critical.task_id

    def test_task_deferred_when_budget_exceeded(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        scheduler.add_task_to_pool(Task("Long task", "walk", 55, priority="high"), pet_healthy)
        scheduler.add_task_to_pool(Task("Short task", "feeding", 10, priority="medium"), pet_healthy)
        scheduler.generate_schedule()
        assert len(scheduler.unscheduled_tasks) == 1
        assert scheduler.unscheduled_tasks[0].title == "Short task"

    def test_completed_task_skipped(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        task = Task("Feeding", "feeding", 10)
        task.mark_as_completed()
        scheduler.add_task_to_pool(task, pet_healthy)
        plan = scheduler.generate_schedule()
        assert len(plan) == 0
        assert any("SKIPPED" in r for r in scheduler.get_reasoning())

    def test_duplicate_task_in_pool_ignored(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        task = Task("Walk", "walk", 20)
        scheduler.add_task_to_pool(task, pet_healthy)
        scheduler.add_task_to_pool(task, pet_healthy)
        assert len(scheduler.task_pool) == 1

    def test_medical_pet_tasks_prioritised_within_tier(
        self, scheduler: DailyScheduler, pet_healthy: Pet, pet_medical: Pet
    ):
        t_healthy = Task("Play", "enrichment", 15, priority="medium")
        t_medical = Task("Medication", "medication", 10, priority="medium")
        scheduler.add_task_to_pool(t_healthy, pet_healthy)
        scheduler.add_task_to_pool(t_medical, pet_medical)
        plan = scheduler.generate_schedule()
        assert plan[0]["task"].task_id == t_medical.task_id

    def test_load_from_owner_populates_pool(
        self, owner: Owner, pet_healthy: Pet, pet_medical: Pet
    ):
        pet_healthy.add_task(Task("Feeding", "feeding", 10))
        pet_medical.add_task(Task("Medication", "medication", 5))
        owner.add_pet(pet_healthy)
        owner.add_pet(pet_medical)
        scheduler = DailyScheduler(owner, date.today())
        scheduler.load_from_owner()
        assert len(scheduler.task_pool) == 2

    def test_conflict_logged_for_same_timeslot(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        t1 = Task("Walk", "walk", 10, priority="high", time_slot_preference="08:00")
        t2 = Task("Feed", "feeding", 10, priority="high", time_slot_preference="08:00")
        scheduler.add_task_to_pool(t1, pet_healthy)
        scheduler.add_task_to_pool(t2, pet_healthy)
        scheduler.generate_schedule()
        assert any("CONFLICT" in r for r in scheduler.get_reasoning())

    def test_get_reasoning_returns_copy(
        self, scheduler: DailyScheduler, pet_healthy: Pet
    ):
        scheduler.add_task_to_pool(Task("Walk", "walk", 10), pet_healthy)
        scheduler.generate_schedule()
        log = scheduler.get_reasoning()
        log.clear()
        assert len(scheduler.get_reasoning()) > 0  # original unaffected

    def test_duration_overlap_conflict_detected(
        self, pet_healthy: Pet, owner: Owner
    ):
        # Force overlapping start_minute values manually to trigger pass-2 conflict.
        scheduler = DailyScheduler(owner, date.today())
        t1 = Task("Walk", "walk", 30, priority="high")
        t2 = Task("Feed", "feeding", 20, priority="high")
        scheduler.add_task_to_pool(t1, pet_healthy)
        scheduler.add_task_to_pool(t2, pet_healthy)
        scheduler.generate_schedule()
        # Inject overlapping start times to simulate fixed-time scheduling.
        scheduler.scheduled_tasks[0]["start_minute"] = 0
        scheduler.scheduled_tasks[1]["start_minute"] = 10  # overlaps [0,30)
        warnings = scheduler.resolve_conflicts()
        assert any("Duration overlap" in w for w in warnings)


# ---------------------------------------------------------------------------
# Phase 4 — sort_by_time, filter_tasks, recurring tasks
# ---------------------------------------------------------------------------

class TestSortAndFilter:
    def test_sort_by_time_hhmm_ordering(self, owner: Owner, pet_healthy: Pet):
        scheduler = DailyScheduler(owner, date.today())
        t1 = Task("Late", "walk", 10, time_slot_preference="18:00")
        t2 = Task("Early", "feeding", 5, time_slot_preference="07:00")
        t3 = Task("Mid", "enrichment", 15, time_slot_preference="12:00")
        for t in (t1, t2, t3):
            scheduler.add_task_to_pool(t, pet_healthy)
        sorted_entries = scheduler.sort_by_time(scheduler.task_pool)
        titles = [e["task"].title for e in sorted_entries]
        assert titles == ["Early", "Mid", "Late"]

    def test_sort_named_slots_ordering(self, owner: Owner, pet_healthy: Pet):
        scheduler = DailyScheduler(owner, date.today())
        t1 = Task("Evening", "walk", 10, time_slot_preference="evening")
        t2 = Task("Morning", "feeding", 5, time_slot_preference="morning")
        t3 = Task("Anytime", "enrichment", 15, time_slot_preference="anytime")
        for t in (t1, t2, t3):
            scheduler.add_task_to_pool(t, pet_healthy)
        sorted_entries = scheduler.sort_by_time(scheduler.task_pool)
        titles = [e["task"].title for e in sorted_entries]
        assert titles == ["Morning", "Anytime", "Evening"]

    def test_filter_by_pet_name(self, owner: Owner, pet_healthy: Pet, pet_medical: Pet):
        scheduler = DailyScheduler(owner, date.today())
        scheduler.add_task_to_pool(Task("Walk", "walk", 10), pet_healthy)
        scheduler.add_task_to_pool(Task("Meds", "medication", 5), pet_medical)
        result = scheduler.filter_tasks(pet_name=pet_healthy.name)
        assert len(result) == 1
        assert result[0]["pet"].pet_id == pet_healthy.pet_id

    def test_filter_by_completed_false(self, owner: Owner, pet_healthy: Pet):
        scheduler = DailyScheduler(owner, date.today())
        done = Task("Done", "walk", 10)
        done.mark_as_completed()
        pending = Task("Pending", "feeding", 5)
        scheduler.add_task_to_pool(done, pet_healthy)
        scheduler.add_task_to_pool(pending, pet_healthy)
        result = scheduler.filter_tasks(completed=False)
        assert len(result) == 1
        assert result[0]["task"].title == "Pending"

    def test_filter_by_completed_true(self, owner: Owner, pet_healthy: Pet):
        scheduler = DailyScheduler(owner, date.today())
        done = Task("Done", "walk", 10)
        done.mark_as_completed()
        scheduler.add_task_to_pool(done, pet_healthy)
        scheduler.add_task_to_pool(Task("Pending", "feeding", 5), pet_healthy)
        result = scheduler.filter_tasks(completed=True)
        assert len(result) == 1
        assert result[0]["task"].is_completed is True


class TestRecurringTasks:
    def test_generate_next_occurrence_daily(self):
        today = date.today()
        task = Task("Feeding", "feeding", 10, is_recurring=True,
                    recurrence_pattern="daily", due_date=today)
        next_t = task.generate_next_occurrence()
        assert next_t is not None
        from datetime import timedelta
        assert next_t.due_date == today + timedelta(days=1)
        assert next_t.title == task.title

    def test_generate_next_occurrence_weekly(self):
        today = date.today()
        task = Task("Bath", "grooming", 20, is_recurring=True,
                    recurrence_pattern="weekly", due_date=today)
        next_t = task.generate_next_occurrence()
        from datetime import timedelta
        assert next_t.due_date == today + timedelta(weeks=1)

    def test_generate_next_occurrence_non_recurring_returns_none(self):
        task = Task("Walk", "walk", 30)
        assert task.generate_next_occurrence() is None

    def test_apply_recurring_tasks_attaches_to_pet(
        self, owner: Owner, pet_healthy: Pet
    ):
        today = date.today()
        task = Task("Feeding", "feeding", 10, is_recurring=True,
                    recurrence_pattern="daily", due_date=today)
        pet_healthy.add_task(task)
        owner.add_pet(pet_healthy)
        scheduler = DailyScheduler(owner, date.today())
        scheduler.load_from_owner()
        task.mark_as_completed()
        new_tasks = scheduler.apply_recurring_tasks()
        assert len(new_tasks) == 1
        assert new_tasks[0] in pet_healthy.tasks

    def test_apply_recurring_skips_non_recurring(
        self, owner: Owner, pet_healthy: Pet
    ):
        task = Task("Walk", "walk", 20)
        task.mark_as_completed()
        pet_healthy.add_task(task)
        owner.add_pet(pet_healthy)
        scheduler = DailyScheduler(owner, date.today())
        scheduler.load_from_owner()
        new_tasks = scheduler.apply_recurring_tasks()
        assert len(new_tasks) == 0

    def test_next_occurrence_has_new_task_id(self):
        """Next occurrence must be a distinct object, not a reference to the original."""
        today = date.today()
        task = Task("Feeding", "feeding", 10, is_recurring=True,
                    recurrence_pattern="daily", due_date=today)
        next_t = task.generate_next_occurrence()
        assert next_t.task_id != task.task_id

    def test_next_occurrence_inherits_properties(self):
        today = date.today()
        task = Task("Meds", "medication", 15, priority="critical",
                    time_slot_preference="08:00", is_recurring=True,
                    recurrence_pattern="daily", due_date=today)
        next_t = task.generate_next_occurrence()
        assert next_t.title == task.title
        assert next_t.category == task.category
        assert next_t.duration_minutes == task.duration_minutes
        assert next_t.priority == task.priority
        assert next_t.time_slot_preference == task.time_slot_preference

    def test_next_occurrence_no_due_date_falls_back_to_today(self):
        """due_date=None should use today as the base for the next occurrence."""
        from datetime import timedelta
        task = Task("Walk", "walk", 20, is_recurring=True,
                    recurrence_pattern="daily")  # no due_date
        next_t = task.generate_next_occurrence()
        assert next_t is not None
        assert next_t.due_date == date.today() + timedelta(days=1)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_pool_returns_empty_schedule(self, owner: Owner):
        scheduler = DailyScheduler(owner, date.today())
        plan = scheduler.generate_schedule()
        assert plan == []
        assert scheduler.unscheduled_tasks == []

    def test_pet_with_no_tasks_does_not_crash(self, owner: Owner, pet_healthy: Pet):
        owner.add_pet(pet_healthy)  # pet has no tasks
        scheduler = DailyScheduler(owner, date.today())
        scheduler.load_from_owner()
        plan = scheduler.generate_schedule()
        assert plan == []

    def test_owner_with_no_pets(self, owner: Owner):
        scheduler = DailyScheduler(owner, date.today())
        scheduler.load_from_owner()
        assert scheduler.task_pool == []
        plan = scheduler.generate_schedule()
        assert plan == []

    def test_budget_boundary_task_fits_exactly(self, owner: Owner, pet_healthy: Pet):
        """A task whose duration equals the remaining budget should be scheduled."""
        scheduler = DailyScheduler(owner, date.today())  # 60 min budget
        task = Task("Long walk", "walk", 60, priority="medium")
        scheduler.add_task_to_pool(task, pet_healthy)
        plan = scheduler.generate_schedule()
        assert len(plan) == 1
        assert scheduler.unscheduled_tasks == []

    def test_task_one_minute_over_budget_deferred(self, owner: Owner, pet_healthy: Pet):
        scheduler = DailyScheduler(owner, date.today())  # 60 min budget
        task = Task("Long walk", "walk", 61, priority="high")
        scheduler.add_task_to_pool(task, pet_healthy)
        scheduler.generate_schedule()
        assert len(scheduler.scheduled_tasks) == 0
        assert len(scheduler.unscheduled_tasks) == 1

    def test_conflict_cross_pet_same_hhmm_slot(
        self, owner: Owner, pet_healthy: Pet, pet_medical: Pet
    ):
        """Two different pets with the same HH:MM preference should trigger a conflict."""
        scheduler = DailyScheduler(owner, date.today())
        t1 = Task("Meds",    "medication", 10, priority="critical", time_slot_preference="09:00")
        t2 = Task("Feeding", "feeding",    10, priority="critical", time_slot_preference="09:00")
        scheduler.add_task_to_pool(t1, pet_medical)
        scheduler.add_task_to_pool(t2, pet_healthy)
        scheduler.generate_schedule()
        assert any("CONFLICT" in r for r in scheduler.get_reasoning())

    def test_sort_empty_list_returns_empty(self, owner: Owner):
        scheduler = DailyScheduler(owner, date.today())
        assert scheduler.sort_by_time([]) == []

    def test_sort_mixed_hhmm_and_named_slots(self, owner: Owner, pet_healthy: Pet):
        """HH:MM times should interleave correctly with named slots."""
        scheduler = DailyScheduler(owner, date.today())
        t1 = Task("Late eve",  "walk",       10, time_slot_preference="20:00")   # 1200 min
        t2 = Task("Morning",   "feeding",     5, time_slot_preference="morning")  # 360 min
        t3 = Task("Afternoon", "enrichment", 15, time_slot_preference="14:00")   # 840 min
        t4 = Task("Anytime",   "grooming",   20, time_slot_preference="anytime")  # 720 min
        for t in (t1, t2, t3, t4):
            scheduler.add_task_to_pool(t, pet_healthy)
        sorted_titles = [e["task"].title for e in scheduler.sort_by_time(scheduler.task_pool)]
        assert sorted_titles == ["Morning", "Anytime", "Afternoon", "Late eve"]

    def test_filter_combined_pet_and_completion(
        self, owner: Owner, pet_healthy: Pet, pet_medical: Pet
    ):
        """Filter by both pet name AND completion status simultaneously."""
        scheduler = DailyScheduler(owner, date.today())
        done = Task("Done walk", "walk", 10)
        done.mark_as_completed()
        pending = Task("Pending walk", "walk", 10)
        scheduler.add_task_to_pool(done, pet_healthy)
        scheduler.add_task_to_pool(pending, pet_healthy)
        scheduler.add_task_to_pool(Task("Meds", "medication", 5), pet_medical)
        result = scheduler.filter_tasks(pet_name=pet_healthy.name, completed=False)
        assert len(result) == 1
        assert result[0]["task"].title == "Pending walk"

    def test_sort_stable_equal_slots(self, owner: Owner, pet_healthy: Pet):
        """Tasks with identical slot values should all appear in the output."""
        scheduler = DailyScheduler(owner, date.today())
        tasks = [Task(f"Task {i}", "walk", 5, time_slot_preference="morning") for i in range(3)]
        for t in tasks:
            scheduler.add_task_to_pool(t, pet_healthy)
        sorted_entries = scheduler.sort_by_time(scheduler.task_pool)
        assert len(sorted_entries) == 3
