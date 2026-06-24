"""
PawPal+ — backend scheduling engine.

Architecture: four dataclasses with clean separation of concerns.
  Task        — immutable-ish unit of care with recurrence support
  Pet         — owns its task list; drives medical-urgency ordering
  Owner       — aggregates pets and exposes the time budget
  DailyScheduler — greedy priority scheduler with sort / filter / conflict APIs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
import uuid

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIORITY_RANK: Dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# Slot names map to representative minutes-since-midnight for ordering.
_SLOT_MINUTES: Dict[str, int] = {
    "morning": 360,    # 06:00
    "anytime": 720,    # 12:00
    "evening": 1080,   # 18:00
}

_RECURRENCE_DELTA: Dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


def _slot_to_minutes(slot: str) -> int:
    """Convert a slot string ('morning' / 'evening' / 'HH:MM') to minutes since midnight."""
    if ":" in slot:
        h, m = slot.split(":", 1)
        return int(h) * 60 + int(m)
    return _SLOT_MINUTES.get(slot, 720)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single unit of pet care (walk, feeding, medication, grooming, etc.)."""

    title: str
    category: str
    duration_minutes: int
    priority: str = "medium"              # critical | high | medium | low
    time_slot_preference: str = "anytime" # morning | anytime | evening | HH:MM
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None   # daily | weekly
    due_date: Optional[date] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_completed: bool = False

    _MUTABLE = frozenset({
        "title", "category", "duration_minutes", "priority",
        "time_slot_preference", "is_recurring", "recurrence_pattern", "due_date",
    })

    def mark_as_completed(self) -> None:
        """Mark this task done. Idempotent."""
        self.is_completed = True

    def update_task_details(self, data: Dict[str, Any]) -> None:
        """Bulk-update allowed fields; silently ignores unknown/protected keys."""
        for key, value in data.items():
            if key in self._MUTABLE:
                setattr(self, key, value)

    def is_urgent(self) -> bool:
        """Return True for critical or high priority tasks."""
        return self.priority in ("critical", "high")

    def generate_next_occurrence(self) -> Optional["Task"]:
        """
        If this task is recurring and has been completed, return a fresh Task
        instance for the next due date. Returns None for non-recurring tasks.

        The new task inherits all scheduling properties; the caller is
        responsible for attaching it to the relevant Pet.
        """
        if not self.is_recurring or not self.recurrence_pattern:
            return None
        delta = _RECURRENCE_DELTA.get(self.recurrence_pattern)
        if delta is None:
            return None
        base = self.due_date or date.today()
        return Task(
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            time_slot_preference=self.time_slot_preference,
            is_recurring=self.is_recurring,
            recurrence_pattern=self.recurrence_pattern,
            due_date=base + delta,
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet under care. Holds demographics and owns its task list."""

    name: str
    species: str
    breed: str
    age_months: int
    energy_level: str = "medium"   # high | medium | low
    medical_notes: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tasks: List[Task] = field(default_factory=list)

    _MUTABLE = frozenset({
        "name", "species", "breed", "age_months",
        "energy_level", "medical_notes", "preferences",
    })

    def update_profile(self, data: Dict[str, Any]) -> None:
        """Bulk-update profile fields; silently ignores unknown keys."""
        for key, value in data.items():
            if key in self._MUTABLE:
                setattr(self, key, value)

    def get_care_summary(self) -> str:
        """Return a one-line human-readable care profile."""
        notes = ", ".join(self.medical_notes) if self.medical_notes else "None"
        return (
            f"{self.name} ({self.species}, {self.breed}) | "
            f"Age: {self.age_months}mo | Energy: {self.energy_level} | "
            f"Medical notes: {notes}"
        )

    def add_task(self, task: Task) -> None:
        """Attach a task; no-op on duplicate task_id."""
        if any(t.task_id == task.task_id for t in self.tasks):
            return
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID; no-op if not found."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> List[Task]:
        """Return a shallow copy of this pet's task list."""
        return list(self.tasks)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Primary caregiver; manages a roster of pets and a daily time budget."""

    name: str
    email: str
    available_hours_per_day: float = 4.0
    owner_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet; no-op if already registered."""
        if any(p.pet_id == pet.pet_id for p in self.pets):
            return
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Unregister a pet by ID; no-op if not found."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_all_pets(self) -> List[Pet]:
        """Return a shallow copy of the pet roster."""
        return list(self.pets)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Aggregate every task across all pets as {task, pet} dicts."""
        return [{"task": t, "pet": p} for p in self.pets for t in p.tasks]


# ---------------------------------------------------------------------------
# DailyScheduler
# ---------------------------------------------------------------------------

@dataclass
class DailyScheduler:
    """
    Greedy priority scheduler for a single day's pet-care plan.

    Pipeline:
      1. add_task_to_pool() / load_from_owner() — stage candidates
      2. generate_schedule()                     — sort, fit, log
      3. sort_by_time()                          — reorder output by slot time
      4. filter_tasks()                          — slice pool by pet / status
      5. resolve_conflicts()                     — called internally; warns on overlap
      6. apply_recurring_tasks()                 — roll over completed recurring tasks
    """

    owner: Owner
    target_date: date
    daily_time_limit_minutes: Optional[int] = None
    task_pool: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_tasks: List[Dict[str, Any]] = field(default_factory=list)
    unscheduled_tasks: List[Task] = field(default_factory=list)
    decision_log: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.daily_time_limit_minutes is None:
            self.daily_time_limit_minutes = int(self.owner.available_hours_per_day * 60)

    # ------------------------------------------------------------------
    # Pool management
    # ------------------------------------------------------------------

    def add_task_to_pool(self, task: Task, pet: Pet) -> None:
        """Stage a task for scheduling. Silently drops duplicates (same task_id)."""
        if any(e["task"].task_id == task.task_id for e in self.task_pool):
            return
        self.task_pool.append({"task": task, "pet": pet})

    def load_from_owner(self) -> None:
        """Convenience: load all tasks from every pet the owner manages."""
        for entry in self.owner.get_all_tasks():
            self.add_task_to_pool(entry["task"], entry["pet"])

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(
        self, entries: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Sort a list of {task, pet} entries by their time_slot_preference.

        Specific HH:MM slots are ordered as actual clock times; named slots
        (morning / anytime / evening) map to representative times so they
        interleave naturally with HH:MM tasks.

        Args:
            entries: list to sort; defaults to self.scheduled_tasks.

        Returns:
            New sorted list (original unchanged).
        """
        source = entries if entries is not None else self.scheduled_tasks
        return sorted(source, key=lambda e: _slot_to_minutes(e["task"].time_slot_preference))

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        entries: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter {task, pet} entries by pet name and/or completion status.

        Args:
            pet_name:  case-insensitive pet name match; None = no filter.
            completed: True = only completed, False = only pending, None = both.
            entries:   list to filter; defaults to self.task_pool.

        Returns:
            New filtered list (original unchanged).
        """
        source = entries if entries is not None else self.task_pool
        result = source
        if pet_name is not None:
            result = [e for e in result if e["pet"].name.lower() == pet_name.lower()]
        if completed is not None:
            result = [e for e in result if e["task"].is_completed == completed]
        return result

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def generate_schedule(self) -> List[Dict[str, Any]]:
        """
        Build the daily schedule using a greedy priority algorithm.

        Sort order (ascending priority value → schedules first):
          1. Priority tier (critical=0 … low=3)
          2. Medical urgency (pets with medical_notes scheduled first within tier)
          3. Time-slot preference (morning → anytime → evening)

        Tasks that exceed the remaining budget are deferred.
        Calls resolve_conflicts() at the end to annotate the decision log.
        """
        self.scheduled_tasks = []
        self.unscheduled_tasks = []
        self.decision_log = []

        def _sort_key(entry: Dict[str, Any]) -> tuple:
            t: Task = entry["task"]
            p: Pet = entry["pet"]
            return (
                PRIORITY_RANK.get(t.priority, 99),
                0 if p.medical_notes else 1,
                _slot_to_minutes(t.time_slot_preference),
            )

        time_used = 0
        for entry in sorted(self.task_pool, key=_sort_key):
            task: Task = entry["task"]
            pet: Pet = entry["pet"]

            if task.is_completed:
                self.decision_log.append(
                    f"SKIPPED   '{task.title}' [{pet.name}]: already completed."
                )
                continue

            if time_used + task.duration_minutes <= self.daily_time_limit_minutes:
                self.scheduled_tasks.append({
                    "task": task,
                    "pet": pet,
                    "start_minute": time_used,
                })
                self.decision_log.append(
                    f"SCHEDULED '{task.title}' [{pet.name}] "
                    f"priority={task.priority}, {task.duration_minutes}min, "
                    f"slot={task.time_slot_preference}, starts at min {time_used}."
                )
                time_used += task.duration_minutes
            else:
                self.unscheduled_tasks.append(task)
                self.decision_log.append(
                    f"DEFERRED  '{task.title}' [{pet.name}]: needs "
                    f"{time_used + task.duration_minutes} min total, "
                    f"limit is {self.daily_time_limit_minutes} min."
                )

        self.resolve_conflicts()
        return self.scheduled_tasks

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def resolve_conflicts(self) -> List[str]:
        """
        Detect scheduling conflicts in self.scheduled_tasks.

        Two conflict types are checked:
          1. Exact HH:MM slot collision — two tasks share an identical preferred
             clock time; the later-placed task cannot honor its preference.
          2. Duration overlap — two tasks' [start, start+duration) windows
             overlap. Because generate_schedule() packs tasks sequentially this
             will fire when fixed-time tasks are inserted out of band, or when
             the scheduler is called with pre-populated start_minute values.

        Warnings are appended to self.decision_log; the schedule is NOT
        modified so callers can decide how to resolve.

        Returns:
            List of conflict warning strings (subset of decision_log).
        """
        warnings: List[str] = []

        # --- pass 1: exact HH:MM slot collisions ---
        slot_seen: Dict[str, str] = {}
        for entry in self.scheduled_tasks:
            task: Task = entry["task"]
            pref = task.time_slot_preference
            if ":" in pref:
                if pref in slot_seen:
                    msg = (
                        f"CONFLICT  '{task.title}' requests slot {pref} already "
                        f"claimed by '{slot_seen[pref]}'; preference cannot be honored."
                    )
                    warnings.append(msg)
                    self.decision_log.append(msg)
                else:
                    slot_seen[pref] = task.title

        # --- pass 2: duration-overlap detection ---
        n = len(self.scheduled_tasks)
        for i in range(n):
            a = self.scheduled_tasks[i]
            a_start = a["start_minute"]
            a_end = a_start + a["task"].duration_minutes
            for j in range(i + 1, n):
                b = self.scheduled_tasks[j]
                b_start = b["start_minute"]
                b_end = b_start + b["task"].duration_minutes
                if a_start < b_end and b_start < a_end:
                    msg = (
                        f"CONFLICT  Duration overlap: "
                        f"'{a['task'].title}' [{a['pet'].name}] "
                        f"min {a_start}–{a_end} overlaps "
                        f"'{b['task'].title}' [{b['pet'].name}] "
                        f"min {b_start}–{b_end}."
                    )
                    warnings.append(msg)
                    self.decision_log.append(msg)

        return warnings

    # ------------------------------------------------------------------
    # Recurring task automation
    # ------------------------------------------------------------------

    def apply_recurring_tasks(self) -> List[Task]:
        """
        For every completed recurring task in the pool, generate its next
        occurrence and attach it to the owning pet.

        Should be called after generate_schedule() once tasks have been
        marked complete (e.g., at end-of-day).

        Returns:
            List of newly created Task instances.
        """
        new_tasks: List[Task] = []
        for entry in self.task_pool:
            task: Task = entry["task"]
            pet: Pet = entry["pet"]
            if task.is_completed and task.is_recurring:
                next_task = task.generate_next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                    new_tasks.append(next_task)
                    self.decision_log.append(
                        f"RECURRING '{task.title}' [{pet.name}]: "
                        f"next occurrence created for {next_task.due_date}."
                    )
        return new_tasks

    # ------------------------------------------------------------------
    # Reasoning
    # ------------------------------------------------------------------

    def get_reasoning(self) -> List[str]:
        """Return a copy of the full decision log from the last scheduling run."""
        return list(self.decision_log)
