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
