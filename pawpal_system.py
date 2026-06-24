from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Any
import uuid

PRIORITY_RANK: Dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_SLOT_RANK: Dict[str, int] = {"morning": 0, "anytime": 1, "evening": 2}


@dataclass
class Task:
    """A single unit of pet care to be scheduled (walk, feeding, medication, etc.)."""

    title: str
    category: str
    duration_minutes: int
    priority: str = "medium"            # critical | high | medium | low
    time_slot_preference: str = "anytime"   # morning | anytime | evening | HH:MM
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily | weekly
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_completed: bool = False

    _MUTABLE = frozenset({
        "title", "category", "duration_minutes", "priority",
        "time_slot_preference", "is_recurring", "recurrence_pattern",
    })

    def mark_as_completed(self) -> None:
        """Mark this task done; idempotent."""
        self.is_completed = True

    def update_task_details(self, data: Dict[str, Any]) -> None:
        """Bulk-update allowed fields; silently ignores unknown keys."""
        for key, value in data.items():
            if key in self._MUTABLE:
                setattr(self, key, value)

    def is_urgent(self) -> bool:
        """Return True for critical or high priority tasks."""
        return self.priority in ("critical", "high")


@dataclass
class Pet:
    """A pet under care. Holds demographics and owns its task list."""

    name: str
    species: str
    breed: str
    age_months: int
    energy_level: str = "medium"        # high | medium | low
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
        """Attach a task to this pet. No-op on duplicate task_id."""
        if any(t.task_id == task.task_id for t in self.tasks):
            return
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by ID; no-op if not found."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> List[Task]:
        """Return a shallow copy of this pet's task list."""
        return list(self.tasks)


@dataclass
class Owner:
    """The primary caregiver; manages a roster of pets and daily time budget."""

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


@dataclass
class DailyScheduler:
    """
    Scheduling engine — pulls tasks from pets, enforces the owner's daily time
    budget, orders by priority and medical urgency, and emits a decision log.
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
    # Scheduling
    # ------------------------------------------------------------------

    def generate_schedule(self) -> List[Dict[str, Any]]:
        """
        Build the daily schedule.

        Sort order (ascending): priority tier → medical urgency (pets with
        medical notes first) → time-slot preference (morning → anytime → evening).
        Tasks exceeding the remaining budget are deferred.
        """
        self.scheduled_tasks = []
        self.unscheduled_tasks = []
        self.decision_log = []

        def _sort_key(entry: Dict[str, Any]):
            task: Task = entry["task"]
            pet: Pet = entry["pet"]
            return (
                PRIORITY_RANK.get(task.priority, 99),
                0 if pet.medical_notes else 1,
                _SLOT_RANK.get(task.time_slot_preference, 1),
            )

        time_used = 0
        for entry in sorted(self.task_pool, key=_sort_key):
            task: Task = entry["task"]
            pet: Pet = entry["pet"]

            if task.is_completed:
                self.decision_log.append(
                    f"SKIPPED  '{task.title}' [{pet.name}]: already completed."
                )
                continue

            fits = time_used + task.duration_minutes <= self.daily_time_limit_minutes
            if fits:
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

    def resolve_conflicts(self) -> None:
        """
        Flag tasks that share an exact HH:MM slot preference; sequential
        scheduling prevents true time overlap, but strict slot fidelity
        cannot be honored for the second claimant.
        """
        seen: Dict[str, str] = {}
        for entry in self.scheduled_tasks:
            task: Task = entry["task"]
            pref = task.time_slot_preference
            if ":" in pref:
                if pref in seen:
                    self.decision_log.append(
                        f"CONFLICT  '{task.title}' wants slot {pref} already "
                        f"claimed by '{seen[pref]}'; preference cannot be honored."
                    )
                else:
                    seen[pref] = task.title

    def get_reasoning(self) -> List[str]:
        """Return the full decision log produced by the last generate_schedule call."""
        return list(self.decision_log)
