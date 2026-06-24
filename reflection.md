# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- **Three Core Actions Identifed:**
  1. **Profile Management (Owner & Pet Onboarding)**: Register owners with specific availability limits and pets with unique attributes (species, breed, age, energy levels, and medical conditions/requirements).
  2. **Task Creation & Configuration**: Add or edit tasks with parameters including category, duration, priority level, frequency (recurrence), and time-of-day preferences.
  3. **Automated Daily Schedule Generation & Conflict Resolution**: Process the pool of tasks to output a structured daily agenda within the owner's constraints, providing clear text reasoning for prioritization or deferral decisions.

- **Initial UML Design Details:**
  - `Owner`: Manages the profile metadata of the human caregiver (e.g., name, contact details, total daily availability) and maintains the list of associated pets.
  - `Pet`: Holds specific, detailed information about each pet (e.g., species, breed, age, energy level, medical needs, activity preferences) which influences task selection and sequencing.
  - `Task`: Represents an individual unit of care (e.g., walk, medicine, feeding) with its duration, priority, preference settings, recurrence, and execution/completion state.
  - `DailyScheduler`: Serves as the core engine responsible for compiling tasks, enforcing owner constraints (like maximum daily care time), ordering by priority/urgency, resolving timing conflicts, and outputting the final daily agenda with natural language reasoning logs.


**b. Design changes**

Yes. During implementation `DailyScheduler` required an explicit `task_pool` collection (a list of `{task, pet}` dicts) that the initial UML omitted. Without it, `add_task_to_pool` had nowhere to store candidates before `generate_schedule` ran. Adding `task_pool` made the staged "pool → schedule" flow explicit and allowed duplicate-task detection at insertion time. The UML (`uml_draft.mmd`) was updated to include this attribute.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
