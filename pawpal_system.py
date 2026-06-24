from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Any
import uuid

PRIORITY_RANK: Dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_SLOT_RANK: Dict[str, int] = {"morning": 0, "anytime": 1, "evening": 2}


@dataclass
class Pet:
    """
    Represents a pet receiving care. Holds demographic, health, and preference details.
    """
    name: str
    species: str
    breed: str
    age_months: int
    energy_level: str = "medium"
    medical_notes: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    _MUTABLE_FIELDS = frozenset({
        "name", "species", "breed", "age_months",
        "energy_level", "medical_notes", "preferences"
    })

    def update_profile(self, data: Dict[str, Any]) -> None:
        """Updates the pet's profile details with provided dictionary data."""
        for key, value in data.items():
            if key in self._MUTABLE_FIELDS:
                setattr(self, key, value)

    def get_care_summary(self) -> str:
        """Returns a human-readable summary of the pet's characteristics and care needs."""
        notes = ", ".join(self.medical_notes) if self.medical_notes else "None"
        return (
            f"{self.name} ({self.species}, {self.breed}) | "
            f"Age: {self.age_months}mo | Energy: {self.energy_level} | "
            f"Medical notes: {notes}"
        )


@dataclass
class Owner:
    """
    Represents the pet owner / primary caregiver.
    """
    name: str
    email: str
    available_hours_per_day: float = 4.0
    owner_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Registers a new pet to this owner. No-op if the pet is already registered."""
        if any(p.pet_id == pet.pet_id for p in self.pets):
            return
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Removes a pet from the owner's profile by their unique ID."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_all_pets(self) -> List[Pet]:
        """Returns all registered pets."""
        return list(self.pets)


@dataclass
class Task:
    """
    Represents a single care task to be scheduled and performed for a specific pet.
    """
    title: str
    category: str
    duration_minutes: int
    priority: str = "medium"
    time_slot_preference: str = "anytime"
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_completed: bool = False

    _MUTABLE_FIELDS = frozenset({
        "title", "category", "duration_minutes", "priority",
        "time_slot_preference", "is_recurring", "recurrence_pattern"
    })

    def mark_as_completed(self) -> None:
        """Marks this task as successfully completed."""
        self.is_completed = True

    def update_task_details(self, data: Dict[str, Any]) -> None:
        """Updates task properties dynamically."""
        for key, value in data.items():
            if key in self._MUTABLE_FIELDS:
                setattr(self, key, value)

    def is_urgent(self) -> bool:
        """Returns True if the task has a 'critical' or 'high' priority rating."""
        return self.priority in ("critical", "high")


@dataclass
class DailyScheduler:
    """
    Schedules daily care tasks for the owner's pets, considering resource constraints,
    priorities, and preferences, and maintains a decision reasoning log.
    """
    owner: Owner
    target_date: date
    daily_time_limit_minutes: Optional[int] = None
    task_pool: List[Dict[str, Any]] = field(default_factory=list)
    scheduled_tasks: List[Dict[str, Any]] = field(default_factory=list)
    unscheduled_tasks: List[Task] = field(default_factory=list)
    decision_log: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize daily_time_limit_minutes if not provided."""
        if self.daily_time_limit_minutes is None:
            self.daily_time_limit_minutes = int(self.owner.available_hours_per_day * 60)

    def add_task_to_pool(self, task: Task, pet: Pet) -> None:
        """
        Adds a task associated with a pet to the scheduling candidate pool.
        Silently ignores duplicates (same task_id).
        """
        if any(e["task"].task_id == task.task_id for e in self.task_pool):
            return
        self.task_pool.append({"task": task, "pet": pet})

    def generate_schedule(self) -> List[Dict[str, Any]]:
        """
        Constructs a daily schedule based on time constraints, pet medical needs, and priority.
        Sorting: critical tasks first, then high/medium/low; within a priority tier,
        morning-preference tasks are placed before anytime, then evening.
        Populates self.scheduled_tasks, self.unscheduled_tasks, and self.decision_log.
        """
        self.scheduled_tasks = []
        self.unscheduled_tasks = []
        self.decision_log = []

        # Medical-need pets get their tasks pushed to the front of same-priority bucket.
        def sort_key(entry: Dict[str, Any]):
            task: Task = entry["task"]
            pet: Pet = entry["pet"]
            has_medical = 1 if not pet.medical_notes else 0  # medical pets sort first (0 < 1)
            return (
                PRIORITY_RANK.get(task.priority, 99),
                has_medical,
                _SLOT_RANK.get(task.time_slot_preference, 1),
            )

        candidates = sorted(self.task_pool, key=sort_key)

        time_used = 0
        for entry in candidates:
            task: Task = entry["task"]
            pet: Pet = entry["pet"]

            if task.is_completed:
                self.decision_log.append(
                    f"SKIPPED '{task.title}' for {pet.name}: already completed."
                )
                continue

            if time_used + task.duration_minutes <= self.daily_time_limit_minutes:
                self.scheduled_tasks.append({
                    "task": task,
                    "pet": pet,
                    "start_minute": time_used,
                })
                self.decision_log.append(
                    f"SCHEDULED '{task.title}' for {pet.name} "
                    f"[priority={task.priority}, {task.duration_minutes}min, "
                    f"slot={task.time_slot_preference}] at minute {time_used}."
                )
                time_used += task.duration_minutes
            else:
                self.unscheduled_tasks.append(task)
                self.decision_log.append(
                    f"DEFERRED '{task.title}' for {pet.name}: would require "
                    f"{time_used + task.duration_minutes} min total, "
                    f"exceeding {self.daily_time_limit_minutes} min daily limit."
                )

        self.resolve_conflicts()
        return self.scheduled_tasks

    def resolve_conflicts(self) -> None:
        """
        Identifies tasks that share an exact HH:MM time-slot preference and logs a
        conflict warning for every task beyond the first in that slot.
        (Sequential scheduling in generate_schedule prevents true time overlap;
        this catches cases where strict slot fidelity cannot be honored.)
        """
        slot_seen: Dict[str, str] = {}  # slot -> first task title
        for entry in self.scheduled_tasks:
            task: Task = entry["task"]
            pref = task.time_slot_preference
            if ":" in pref:  # specific clock time e.g. "08:00"
                if pref in slot_seen:
                    self.decision_log.append(
                        f"CONFLICT: '{task.title}' requested slot {pref} already "
                        f"claimed by '{slot_seen[pref]}'; slot preference cannot be "
                        f"strictly honored for this task."
                    )
                else:
                    slot_seen[pref] = task.title

    def get_reasoning(self) -> List[str]:
        """Returns the list of reasoning steps explaining why tasks were scheduled or skipped."""
        return list(self.decision_log)
