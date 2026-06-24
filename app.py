from pawpal_system import DailyScheduler, Owner, Pet, Task
import streamlit as st
from datetime import date, datetime

# Page configuration for a premium look
st.set_page_config(
    page_title="PawPal+ | Premium Pet Care Planner",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium styling via markdown
st.markdown(
    """
    <style>
    .main {
        background-color: #fafafa;
    }
    .pet-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #ff4b4b;
        margin-bottom: 15px;
    }
    .task-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        border: 1px solid #eee;
        margin-bottom: 10px;
    }
    .timeline-time {
        font-weight: bold;
        color: #ff4b4b;
        font-size: 1.1em;
    }
    .priority-badge {
        font-size: 0.8em;
        padding: 3px 8px;
        border-radius: 15px;
        font-weight: bold;
        text-transform: uppercase;
        color: white;
    }
    .badge-critical { background-color: #d9534f; }
    .badge-high { background-color: #f0ad4e; }
    .badge-medium { background-color: #5bc0de; }
    .badge-low { background-color: #777; }
    </style>
    """,
    unsafe_allowed_html=True,
)

# ---------------------------------------------------------------------------
# Session State & Memory Management (Seed Data)
# ---------------------------------------------------------------------------

def reset_to_defaults():
    owner = Owner("Jordan", "jordan@pawpal.io", available_hours_per_day=2.0)
    
    biscuit = Pet("Biscuit", "dog", "Golden Retriever", 36, energy_level="high", medical_notes=["arthritis"])
    mochi = Pet("Mochi", "cat", "Siamese", 18, energy_level="medium")
    
    biscuit.add_task(Task("Arthritis medication", "medication", 5, priority="critical", time_slot_preference="morning"))
    biscuit.add_task(Task("Morning walk", "walk", 30, priority="high", time_slot_preference="morning"))
    biscuit.add_task(Task("Evening walk", "walk", 25, priority="medium", time_slot_preference="evening"))
    biscuit.add_task(Task("Grooming session", "grooming", 45, priority="low", time_slot_preference="anytime"))
    
    mochi.add_task(Task("Feeding", "feeding", 10, priority="critical", time_slot_preference="morning", is_recurring=True, recurrence_pattern="daily"))
    mochi.add_task(Task("Enrichment play", "enrichment", 20, priority="medium", time_slot_preference="anytime"))
    
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    
    st.session_state.owner = owner
    st.session_state.generated_schedule = None

# Initialize persistent Owner model in the vault of session state
if "owner" not in st.session_state:
    reset_to_defaults()

# Reference owner directly from memory
owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐾 PawPal+ Configuration")
    st.markdown("---")
    st.subheader("👤 Owner Profile")
    
    # Update owner properties in place
    owner.name = st.text_input("Name", value=owner.name)
    owner.email = st.text_input("Email", value=owner.email)
    
    # Hour budget selector (converted to float hours)
    budget_hours = st.slider(
        "Daily Available Time (Hours)",
        min_value=0.5,
        max_value=12.0,
        value=float(owner.available_hours_per_day),
        step=0.5
    )
    owner.available_hours_per_day = budget_hours
    
    st.markdown("---")
    st.subheader("stats Dashboard")
    st.metric("Total Pets Onboarded", len(owner.get_all_pets()))
    
    total_tasks = sum(len(p.get_tasks()) for p in owner.get_all_pets())
    st.metric("Total Tasks Tracked", total_tasks)
    
    st.markdown("---")
    if st.sidebar.button("🔄 Reset to Default Seed Data"):
        reset_to_defaults()
        st.success("State reset successfully!")
        st.rerun()

# ---------------------------------------------------------------------------
# Main App Layout
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+ Care Dashboard")
st.caption(f"Logged in as **{owner.name}** ({owner.email}) • Daily Care Budget: **{int(owner.available_hours_per_day * 60)} minutes**")

tab1, tab2, tab3 = st.tabs(["📋 Today's Schedule", "🐾 Manage Pets", "➕ Add Tasks"])

# ---------------------------------------------------------------------------
# Tab 1: Today's Schedule Generation & Timeline View
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("⏰ Daily Schedule Planner")
    
    if len(owner.get_all_pets()) == 0:
        st.info("You don't have any pets onboarded. Head over to the **Manage Pets** tab to get started!")
    elif total_tasks == 0:
        st.info("No tasks scheduled yet. Head over to the **Add Tasks** tab to queue some care activities!")
    else:
        col_ctrl, col_status = st.columns([1, 3])
        with col_ctrl:
            if st.button("🚀 Generate Today's Care Plan", use_container_width=True):
                # Instantiate scheduler
                scheduler = DailyScheduler(owner, date.today())
                scheduler.load_from_owner()
                scheduler.generate_schedule()
                
                # Cache results in session state to persist through UI interactions
                st.session_state.generated_schedule = {
                    "scheduled": scheduler.scheduled_tasks,
                    "deferred": scheduler.unscheduled_tasks,
                    "reasoning": scheduler.get_reasoning(),
                    "total_budget": scheduler.daily_time_limit_minutes,
                }
                st.success("Care schedule generated!")
        
        # Display the schedule plan if cached in session state
        if st.session_state.generated_schedule:
            sched_data = st.session_state.generated_schedule
            
            st.divider()
            
            col_schedule, col_deferred = st.columns([2, 1])
            
            with col_schedule:
                st.markdown("### 📅 Timeline View")
                if not sched_data["scheduled"]:
                    st.warning("No tasks were scheduled. Check priorities or daily budget limit.")
                else:
                    for entry in sched_data["scheduled"]:
                        task: Task = entry["task"]
                        pet: Pet = entry["pet"]
                        start = entry["start_minute"]
                        h, m = divmod(start, 60)
                        
                        # Priority styling
                        p_badge = f'<span class="priority-badge badge-{task.priority}">{task.priority}</span>'
                        
                        st.markdown(
                            f"""
                            <div class="task-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span class="timeline-time">{h:02d}:{m:02d}</span> &nbsp;&nbsp;
                                        <strong>{task.title}</strong> ({task.duration_minutes} min) — <em>{pet.name} ({pet.species})</em>
                                    </div>
                                    <div>{p_badge}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allowed_html=True
                        )
            
            with col_deferred:
                st.markdown("### ⏳ Deferred Tasks")
                if not sched_data["deferred"]:
                    st.success("All tasks scheduled! No tasks deferred. 🎉")
                else:
                    for task in sched_data["deferred"]:
                        p_badge = f'<span class="priority-badge badge-{task.priority}">{task.priority}</span>'
                        st.markdown(
                            f"""
                            <div class="task-card" style="border-left: 5px solid #777;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong>{task.title}</strong> ({task.duration_minutes} min)
                                    </div>
                                    <div>{p_badge}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allowed_html=True
                        )
            
            st.divider()
            with st.expander("🔍 Scheduler Decision Logs & Reasoning", expanded=True):
                for log_line in sched_data["reasoning"]:
                    if "SCHEDULED" in log_line:
                        st.write(f"✅ {log_line}")
                    elif "DEFERRED" in log_line:
                        st.write(f"⚠️ {log_line}")
                    else:
                        st.write(f"ℹ️ {log_line}")

# ---------------------------------------------------------------------------
# Tab 2: Manage Pets
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("🐾 Register & Onboard Your Pets")
    
    # Form to register a new pet
    with st.form("register_pet_form", clear_on_submit=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            new_pet_name = st.text_input("Pet Name*", placeholder="e.g. Charlie")
            new_pet_species = st.selectbox("Species*", ["dog", "cat", "bird", "rabbit", "reptile", "other"])
            new_pet_breed = st.text_input("Breed / Breed Mix*", placeholder="e.g. Beagle")
        with col_p2:
            new_pet_age = st.number_input("Age (Months)*", min_value=1, max_value=360, value=24)
            new_pet_energy = st.selectbox("Energy Level*", ["high", "medium", "low"], index=1)
            new_pet_meds = st.text_area("Medical Notes / Conditions", placeholder="e.g. arthritis, daily insulin (separate multiple with commas)")
            
        submitted_pet = st.form_submit_button("➕ Onboard Pet")
        
        if submitted_pet:
            if not new_pet_name or not new_pet_breed:
                st.error("Please fill in all required fields marked with *.")
            else:
                med_list = [m.strip() for m in new_pet_meds.split(",") if m.strip()]
                new_pet = Pet(
                    name=new_pet_name,
                    species=new_pet_species,
                    breed=new_pet_breed,
                    age_months=int(new_pet_age),
                    energy_level=new_pet_energy,
                    medical_notes=med_list
                )
                owner.add_pet(new_pet)
                st.success(f"Registered {new_pet_name} successfully!")
                st.rerun()

    st.markdown("---")
    st.subheader("🐾 Registered Roster")
    
    pets_list = owner.get_all_pets()
    if not pets_list:
        st.info("No pets registered yet. Onboard one using the form above.")
    else:
        # Display pet cards
        for pet in pets_list:
            st.markdown(
                f"""
                <div class="pet-card">
                    <h3>🐾 {pet.name}</h3>
                    <p><strong>Profile:</strong> {pet.get_care_summary()}</p>
                </div>
                """,
                unsafe_allowed_html=True
            )
            
            # Sub-display details and removal of tasks / pets
            col_pet_del, col_task_view = st.columns([1, 5])
            with col_pet_del:
                if st.button(f"🗑️ Remove {pet.name}", key=f"remove_pet_{pet.pet_id}"):
                    owner.remove_pet(pet.pet_id)
                    st.success(f"Removed {pet.name} from the roster.")
                    st.rerun()
            with col_task_view:
                pet_tasks = pet.get_tasks()
                if pet_tasks:
                    with st.expander(f"📋 {pet.name}'s Tasks ({len(pet_tasks)})"):
                        for t in pet_tasks:
                            col_t_desc, col_t_del = st.columns([5, 1])
                            with col_t_desc:
                                st.write(f"- **{t.title}** ({t.category}) • {t.duration_minutes} min • priority: {t.priority}")
                            with col_t_del:
                                if st.button("🗑️", key=f"del_task_{t.task_id}"):
                                    pet.remove_task(t.task_id)
                                    st.success(f"Removed task '{t.title}'")
                                    st.rerun()

# ---------------------------------------------------------------------------
# Tab 3: Add Tasks
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("➕ Schedule Pet Care Tasks")
    
    pets_list = owner.get_all_pets()
    if not pets_list:
        st.info("Please register at least one pet under the **Manage Pets** tab before scheduling tasks.")
    else:
        # Select pet to add task to
        pet_options = {pet.name: pet for pet in pets_list}
        selected_pet_name = st.selectbox("Select Pet*", list(pet_options.keys()))
        selected_pet = pet_options[selected_pet_name]
        
        with st.form("add_task_form", clear_on_submit=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                task_title = st.text_input("Task Title*", placeholder="e.g. Afternoon feeding")
                task_category = st.selectbox("Category*", ["feeding", "walk", "medication", "grooming", "enrichment", "other"])
                task_duration = st.number_input("Duration (Minutes)*", min_value=1, max_value=240, value=20, step=5)
            with col_t2:
                task_priority = st.selectbox("Priority*", ["critical", "high", "medium", "low"], index=2)
                task_slot = st.selectbox("Time Preference*", ["morning", "anytime", "evening", "08:00", "12:00", "18:00"], index=1)
                task_recurring = st.checkbox("Is recurring?")
                task_pattern = st.selectbox("Recurrence Pattern", ["daily", "weekly"], index=0)
                
            submitted_task = st.form_submit_button("➕ Schedule Task")
            
            if submitted_task:
                if not task_title:
                    st.error("Please enter a task title.")
                else:
                    new_task = Task(
                        title=task_title,
                        category=task_category,
                        duration_minutes=int(task_duration),
                        priority=task_priority,
                        time_slot_preference=task_slot,
                        is_recurring=task_recurring,
                        recurrence_pattern=task_pattern if task_recurring else None
                    )
                    selected_pet.add_task(new_task)
                    st.success(f"Added task '{task_title}' to {selected_pet_name}'s schedule!")
                    st.rerun()
