from pawpal_system import DailyScheduler, Owner, Pet, Task
import streamlit as st
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"


def _save(owner: Owner) -> None:
    """Persist the owner graph to data.json after every mutation."""
    owner.save_to_json(DATA_FILE)

st.set_page_config(
    page_title="PawPal+ | Pet Care Planner",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .task-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
        border: 1px solid #eee;
        margin-bottom: 10px;
    }
    .timeline-time { font-weight: bold; color: #ff4b4b; font-size: 1.05em; }
    .priority-badge {
        font-size: 0.78em; padding: 3px 8px; border-radius: 15px;
        font-weight: bold; text-transform: uppercase; color: white;
    }
    .badge-critical { background-color: #d9534f; }
    .badge-high     { background-color: #f0ad4e; }
    .badge-medium   { background-color: #5bc0de; }
    .badge-low      { background-color: #777; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _build_defaults() -> Owner:
    owner = Owner("Jordan", "jordan@pawpal.io", available_hours_per_day=2.0)

    biscuit = Pet("Biscuit", "dog", "Golden Retriever", 36,
                  energy_level="high", medical_notes=["arthritis"])
    mochi = Pet("Mochi", "cat", "Siamese", 18, energy_level="medium")

    biscuit.add_task(Task("Arthritis medication", "medication", 5,
                          priority="critical", time_slot_preference="08:00",
                          is_recurring=True, recurrence_pattern="daily",
                          due_date=date.today()))
    biscuit.add_task(Task("Morning walk",   "walk",    30, priority="high",   time_slot_preference="09:00"))
    biscuit.add_task(Task("Evening walk",   "walk",    25, priority="medium", time_slot_preference="18:30"))
    biscuit.add_task(Task("Grooming",       "grooming",45, priority="low",    time_slot_preference="anytime"))

    mochi.add_task(Task("Breakfast feeding","feeding", 10, priority="critical",time_slot_preference="08:00",
                        is_recurring=True, recurrence_pattern="daily", due_date=date.today()))
    mochi.add_task(Task("Enrichment play",  "enrichment",20,priority="medium",time_slot_preference="15:00"))

    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner


def _reset():
    st.session_state.owner = _build_defaults()
    st.session_state.sched_data = None


if "owner" not in st.session_state:
    if DATA_FILE.exists():
        try:
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
            st.session_state.sched_data = None
        except Exception:
            _reset()          # corrupt file → fall back to defaults
    else:
        _reset()

owner: Owner = st.session_state.owner


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐾 PawPal+")
    st.markdown("---")
    st.subheader("Owner Profile")
    owner.name  = st.text_input("Name",  value=owner.name)
    owner.email = st.text_input("Email", value=owner.email)
    owner.available_hours_per_day = st.slider(
        "Daily Budget (hours)", 0.5, 12.0, float(owner.available_hours_per_day), 0.5
    )
    st.markdown("---")
    st.metric("Pets", len(owner.get_all_pets()))
    st.metric("Tasks", sum(len(p.get_tasks()) for p in owner.get_all_pets()))
    st.markdown("---")
    # Persist any sidebar edits (name, email, budget) immediately
    _save(owner)

    st.markdown("---")
    if st.button("🔄 Reset to demo data"):
        _reset()
        st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+ Care Dashboard")
st.caption(
    f"**{owner.name}** ({owner.email})  •  "
    f"Daily budget: **{int(owner.available_hours_per_day * 60)} min**"
)

tab1, tab2, tab3 = st.tabs(["📋 Today's Schedule", "🐾 Manage Pets", "➕ Add Tasks"])


# ---------------------------------------------------------------------------
# Tab 1 — Schedule
# ---------------------------------------------------------------------------

with tab1:
    st.subheader("Daily Schedule Planner")

    all_pets = owner.get_all_pets()
    total_tasks = sum(len(p.get_tasks()) for p in all_pets)

    if not all_pets:
        st.info("No pets registered. Go to **Manage Pets** to get started.")
    elif total_tasks == 0:
        st.info("No tasks yet. Go to **Add Tasks** to queue care activities.")
    else:
        if st.button("🚀 Generate Today's Care Plan", use_container_width=False):
            scheduler = DailyScheduler(owner, date.today())
            scheduler.load_from_owner()
            scheduler.generate_schedule()

            st.session_state.sched_data = {
                "scheduler": scheduler,
                "scheduled": scheduler.scheduled_tasks,
                "deferred":  scheduler.unscheduled_tasks,
                "reasoning": scheduler.get_reasoning(),
                "budget":    scheduler.daily_time_limit_minutes,
            }
            st.rerun()

        sched = st.session_state.get("sched_data")
        if sched:
            scheduler: DailyScheduler = sched["scheduler"]

            # ---- Conflict banners (prominent, before timeline) -----------
            conflicts = [l for l in sched["reasoning"] if "CONFLICT" in l]
            if conflicts:
                st.markdown("#### ⚠️ Scheduling Conflicts Detected")
                for c in conflicts:
                    # Strip the leading log-prefix so the message reads naturally
                    msg = c.replace("CONFLICT  ", "").replace("CONFLICT ", "")
                    st.warning(msg)
            else:
                st.success("No scheduling conflicts — all time slots are clear.")

            st.divider()

            # ---- Filter controls --------------------------------------------
            st.markdown("#### Filter Schedule View")
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                pet_names = ["All pets"] + [p.name for p in all_pets]
                filter_pet = st.selectbox("Filter by pet", pet_names, key="filter_pet")
            with filter_col2:
                filter_status = st.selectbox(
                    "Filter by status",
                    ["All tasks", "Pending only", "Completed only"],
                    key="filter_status",
                )

            # Map UI choices to filter_tasks() args
            pet_name_arg = None if filter_pet == "All pets" else filter_pet
            completed_arg = None
            if filter_status == "Pending only":
                completed_arg = False
            elif filter_status == "Completed only":
                completed_arg = True

            # Apply filter then sort chronologically via sort_by_time()
            filtered = scheduler.filter_tasks(
                pet_name=pet_name_arg,
                completed=completed_arg,
                entries=sched["scheduled"],
            )
            sorted_entries = scheduler.sort_by_time(filtered)

            st.divider()

            # ---- Timeline + Deferred columns --------------------------------
            col_timeline, col_deferred = st.columns([2, 1])

            with col_timeline:
                st.markdown(f"#### Timeline ({len(sorted_entries)} tasks)")
                if not sorted_entries:
                    st.info("No tasks match the current filter.")
                else:
                    for entry in sorted_entries:
                        task: Task = entry["task"]
                        pet:  Pet  = entry["pet"]
                        start = entry["start_minute"]
                        h, m = divmod(start, 60)
                        badge = (
                            f'<span class="priority-badge badge-{task.priority}">'
                            f'{task.priority}</span>'
                        )
                        recur_icon = " 🔁" if task.is_recurring else ""
                        st.markdown(
                            f"""
                            <div class="task-card">
                              <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div>
                                  <span class="timeline-time">{h:02d}:{m:02d}</span>&nbsp;&nbsp;
                                  <strong>{task.title}{recur_icon}</strong>
                                  ({task.duration_minutes} min) — <em>{pet.name}</em>
                                </div>
                                <div>{badge}</div>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            with col_deferred:
                st.markdown(f"#### Deferred ({len(sched['deferred'])} tasks)")
                if not sched["deferred"]:
                    st.success("All tasks fit within the daily budget! 🎉")
                else:
                    for task in sched["deferred"]:
                        badge = (
                            f'<span class="priority-badge badge-{task.priority}">'
                            f'{task.priority}</span>'
                        )
                        st.markdown(
                            f"""
                            <div class="task-card" style="border-left:4px solid #ccc;">
                              <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div><strong>{task.title}</strong> ({task.duration_minutes} min)</div>
                                <div>{badge}</div>
                              </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            st.divider()

            # ---- Decision log -----------------------------------------------
            with st.expander("🔍 Scheduler Decision Log", expanded=False):
                for line in sched["reasoning"]:
                    if "SCHEDULED" in line:
                        st.success(line, icon="✅")
                    elif "DEFERRED" in line:
                        st.warning(line, icon="⏳")
                    elif "CONFLICT" in line:
                        st.error(line, icon="⚠️")
                    elif "RECURRING" in line:
                        st.info(line, icon="🔁")
                    else:
                        st.write(f"ℹ️ {line}")


# ---------------------------------------------------------------------------
# Tab 2 — Manage Pets
# ---------------------------------------------------------------------------

with tab2:
    st.subheader("Register & Manage Pets")

    with st.form("register_pet_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            p_name    = st.text_input("Pet Name *", placeholder="e.g. Charlie")
            p_species = st.selectbox("Species *", ["dog","cat","bird","rabbit","reptile","other"])
            p_breed   = st.text_input("Breed *", placeholder="e.g. Beagle")
        with c2:
            p_age    = st.number_input("Age (months) *", 1, 360, 24)
            p_energy = st.selectbox("Energy Level *", ["high","medium","low"], index=1)
            p_meds   = st.text_area("Medical Notes", placeholder="e.g. arthritis, diabetes (comma-separated)")
        if st.form_submit_button("➕ Register Pet"):
            if not p_name or not p_breed:
                st.error("Name and Breed are required.")
            else:
                med_list = [m.strip() for m in p_meds.split(",") if m.strip()]
                owner.add_pet(Pet(p_name, p_species, p_breed, int(p_age), p_energy, med_list))
                _save(owner)
                st.success(f"{p_name} registered!")
                st.rerun()

    st.markdown("---")
    pets = owner.get_all_pets()
    if not pets:
        st.info("No pets registered yet.")
    else:
        for pet in pets:
            with st.container():
                st.markdown(
                    f'<div style="border-left:5px solid #ff4b4b;padding:10px;margin-bottom:8px;">'
                    f'<strong>🐾 {pet.name}</strong> — {pet.get_care_summary()}</div>',
                    unsafe_allow_html=True,
                )
                col_del, col_tasks = st.columns([1, 5])
                with col_del:
                    if st.button(f"Remove {pet.name}", key=f"rp_{pet.pet_id}"):
                        owner.remove_pet(pet.pet_id)
                        _save(owner)
                        st.rerun()
                with col_tasks:
                    tasks = pet.get_tasks()
                    if tasks:
                        with st.expander(f"{pet.name}'s tasks ({len(tasks)})"):
                            for t in tasks:
                                tc, td = st.columns([5, 1])
                                with tc:
                                    st.write(f"**{t.title}** · {t.category} · {t.duration_minutes}min · {t.priority}")
                                with td:
                                    if st.button("🗑️", key=f"dt_{t.task_id}"):
                                        pet.remove_task(t.task_id)
                                        _save(owner)
                                        st.rerun()


# ---------------------------------------------------------------------------
# Tab 3 — Add Tasks
# ---------------------------------------------------------------------------

with tab3:
    st.subheader("Schedule a Care Task")
    pets = owner.get_all_pets()
    if not pets:
        st.info("Register a pet first under **Manage Pets**.")
    else:
        pet_map = {p.name: p for p in pets}
        selected_name = st.selectbox("Assign to pet *", list(pet_map))
        selected_pet  = pet_map[selected_name]

        with st.form("add_task_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                t_title    = st.text_input("Task Title *", placeholder="e.g. Afternoon feeding")
                t_category = st.selectbox("Category *", ["feeding","walk","medication","grooming","enrichment","other"])
                t_duration = st.number_input("Duration (min) *", 1, 240, 20, step=5)
            with c2:
                t_priority = st.selectbox("Priority *", ["critical","high","medium","low"], index=2)
                t_slot     = st.selectbox("Time Preference *",
                                          ["morning","anytime","evening","08:00","09:00",
                                           "12:00","15:00","18:00","18:30"], index=1)
                t_recurring= st.checkbox("Recurring task?")
                t_pattern  = st.selectbox("Recurrence", ["daily","weekly"])
            if st.form_submit_button("➕ Add Task"):
                if not t_title:
                    st.error("Task title is required.")
                else:
                    selected_pet.add_task(Task(
                        title=t_title, category=t_category,
                        duration_minutes=int(t_duration), priority=t_priority,
                        time_slot_preference=t_slot,
                        is_recurring=t_recurring,
                        recurrence_pattern=t_pattern if t_recurring else None,
                        due_date=date.today() if t_recurring else None,
                    ))
                    _save(owner)
                    st.success(f"Added '{t_title}' to {selected_name}'s plan.")
                    st.rerun()
