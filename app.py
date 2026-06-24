from pawpal_system import DailyScheduler, Owner, Pet, Task
import streamlit as st
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"


def _save(owner: Owner) -> None:
    """Persist the owner graph to data.json after every mutation."""
    owner.save_to_json(DATA_FILE)


def clean_html(html: str) -> str:
    """Helper to minify HTML/SVG strings, preventing Streamlit/Markdown code-block parsing bugs."""
    return "".join(line.strip() for line in html.splitlines())


st.set_page_config(
    page_title="PawPal+ | Pet Care Planner",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# SVG and Sticker Asset Helpers
# ---------------------------------------------------------------------------

def get_mascot_svg() -> str:
    svg = """
    <svg viewBox="0 0 100 100" width="100" height="100" style="display: block; margin: 0 auto;">
        <circle cx="50" cy="50" r="46" fill="#FFF0E6" stroke="#FFE5D9" stroke-width="2"/>
        <path class="wag-tail" d="M30,55 Q15,45 25,35 Q35,45 32,54" fill="#FFA585" />
        <circle cx="50" cy="65" r="22" fill="#FF7A60"/>
        <ellipse cx="50" cy="68" rx="12" ry="15" fill="#FFFDFB"/>
        <g class="bob-head">
            <path d="M32,38 Q22,20 38,26 Z" fill="#E05B43" />
            <path d="M68,38 Q78,20 62,26 Z" fill="#E05B43" />
            <path d="M34,36 Q26,24 38,29 Z" fill="#FFB3A6" />
            <path d="M66,36 Q74,24 62,29 Z" fill="#FFB3A6" />
            <circle cx="50" cy="40" r="18" fill="#FF7A60"/>
            <ellipse cx="50" cy="46" rx="9" ry="7" fill="#FFFDFB"/>
            <polygon points="47,43 53,43 50,46" fill="#4A3E3D" />
            <path d="M48,48 Q50,51 52,48" stroke="#4A3E3D" stroke-width="1.5" fill="none" stroke-linecap="round"/>
            <circle cx="43" cy="37" r="2.5" fill="#4A3E3D"/>
            <circle cx="57" cy="37" r="2.5" fill="#4A3E3D"/>
            <circle cx="44" cy="36" r="0.8" fill="#FFFDFB"/>
            <circle cx="58" cy="36" r="0.8" fill="#FFFDFB"/>
            <ellipse cx="37" cy="42" rx="3" ry="2" fill="#FF9F8E" opacity="0.6"/>
            <ellipse cx="63" cy="42" rx="3" ry="2" fill="#FF9F8E" opacity="0.6"/>
        </g>
        <ellipse cx="42" cy="80" rx="5" ry="4" fill="#FFA585"/>
        <ellipse cx="58" cy="80" rx="5" ry="4" fill="#FFA585"/>
    </svg>
    """
    return clean_html(svg)


def get_category_svg(category: str) -> str:
    cat = category.lower()
    if cat == "feeding":
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <path d="M6,44 C6,44 10,56 32,56 C54,56 58,44 58,44 L52,28 C52,28 48,24 32,24 C16,24 12,28 12,28 Z" fill="#FFE5D9" stroke="#FF7A60" stroke-width="2.5" stroke-linejoin="round"/>
            <ellipse cx="32" cy="28" rx="20" ry="4" fill="#FFB3A6"/>
            <circle cx="32" cy="42" r="5" fill="#FF7A60"/>
        </svg>
        """
    elif cat == "walk":
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <path d="M32,28 C24,28 20,36 20,44 C20,52 26,56 32,56 C38,56 44,52 44,44 C44,36 40,28 32,28 Z" fill="#E6F9F3" stroke="#4BD3A6" stroke-width="2.5"/>
            <ellipse cx="16" cy="26" rx="5" ry="7" fill="#4BD3A6"/>
            <ellipse cx="27" cy="16" rx="5" ry="7" fill="#4BD3A6"/>
            <ellipse cx="37" cy="16" rx="5" ry="7" fill="#4BD3A6"/>
            <ellipse cx="48" cy="26" rx="5" ry="7" fill="#4BD3A6"/>
        </svg>
        """
    elif cat == "medication":
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <rect x="12" y="24" width="40" height="16" rx="8" transform="rotate(-45 32 32)" fill="#E8E5FF" stroke="#9C8DFB" stroke-width="2.5"/>
            <path d="M20.6,37.4 L43.4,14.6" stroke="#9C8DFB" stroke-width="2.5"/>
            <circle cx="23" cy="41" r="3" fill="#9C8DFB"/>
            <circle cx="41" cy="23" r="3" fill="#ffffff"/>
        </svg>
        """
    elif cat == "grooming":
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <path d="M12,20 L52,20 L52,28 L12,28 Z" fill="#FFF0F5" stroke="#FF85B3" stroke-width="2.5"/>
            <path d="M16,28 L16,48 M24,28 L24,48 M32,28 L32,48 M40,28 L40,48 M48,28 L48,48" stroke="#FF85B3" stroke-width="2.5"/>
            <circle cx="28" cy="12" r="4" fill="#FF85B3" opacity="0.6"/>
            <circle cx="40" cy="8" r="3" fill="#FF85B3" opacity="0.4"/>
        </svg>
        """
    elif cat == "enrichment":
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <circle cx="32" cy="32" r="20" fill="#FFFBE6" stroke="#FFC93C" stroke-width="2.5"/>
            <path d="M16,32 Q32,16 48,32 Q32,48 16,32" stroke="#FFC93C" stroke-width="2" fill="none"/>
            <path d="M32,16 Q16,32 32,48 Q48,32 32,16" stroke="#FFC93C" stroke-width="2" fill="none"/>
        </svg>
        """
    else:
        svg = """
        <svg viewBox="0 0 64 64" width="40" height="40" style="vertical-align: middle;">
            <path d="M32,54 C32,54 8,38 8,22 C8,12 18,6 26,12 C30,15 32,18 32,18 C32,18 34,15 38,12 C46,6 56,12 56,22 C56,38 32,54 32,54 Z" fill="#FFEAE6" stroke="#FF5757" stroke-width="2.5"/>
        </svg>
        """
    return clean_html(svg)


def get_empty_schedule_svg() -> str:
    svg = """
    <div style="text-align: center; padding: 40px 20px;">
        <svg viewBox="0 0 100 100" width="120" height="120" style="display: block; margin: 0 auto; animation: head-bob 2.5s ease-in-out infinite;">
            <circle cx="50" cy="50" r="40" fill="#FFF0E6" stroke="#FFE5D9" stroke-width="2" stroke-dasharray="4,4"/>
            <path d="M30,45 C25,40 15,45 20,50 C15,55 25,60 30,55 L70,55 C75,60 85,55 80,50 C85,45 75,40 70,45 Z" fill="#FFFDFB" stroke="#FF7A60" stroke-width="2.5" transform="rotate(-15 50 50)"/>
        </svg>
        <h3 style="font-family: 'Fredoka', sans-serif; color: #8B7775; margin-top: 15px;">No Care Plan Generated Yet</h3>
        <p style="font-family: 'Quicksand', sans-serif; color: #A6918F; font-size: 0.95em;">Ready to plan the perfect day for your furry friends? Let's compile their tasks!</p>
    </div>
    """
    return clean_html(svg)


def get_species_svg(species: str) -> str:
    spec = species.lower()
    if spec == "dog":
        svg = """
        <svg viewBox="0 0 64 64" width="48" height="48">
            <circle cx="32" cy="32" r="28" fill="#FFE5D9" stroke="#FF7A60" stroke-width="2"/>
            <circle cx="24" cy="28" r="3" fill="#4A3E3D"/>
            <circle cx="40" cy="28" r="3" fill="#4A3E3D"/>
            <ellipse cx="32" cy="35" rx="4" ry="3" fill="#E05B43"/>
            <path d="M12,24 C8,16 18,12 22,18" fill="none" stroke="#FF7A60" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M52,24 C56,16 46,12 42,18" fill="none" stroke="#FF7A60" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
        """
    elif spec == "cat":
        svg = """
        <svg viewBox="0 0 64 64" width="48" height="48">
            <circle cx="32" cy="32" r="28" fill="#FFF2CC" stroke="#F1C232" stroke-width="2"/>
            <polygon points="18,18 25,10 27,22" fill="#F1C232"/>
            <polygon points="46,18 39,10 37,22" fill="#F1C232"/>
            <circle cx="24" cy="30" r="3" fill="#4A3E3D"/>
            <circle cx="40" cy="30" r="3" fill="#4A3E3D"/>
            <polygon points="30,36 34,36 32,39" fill="#E05B43"/>
        </svg>
        """
    else:
        svg = """
        <svg viewBox="0 0 64 64" width="48" height="48">
            <circle cx="32" cy="32" r="28" fill="#E6F9F3" stroke="#4BD3A6" stroke-width="2"/>
            <path d="M32,18 C24,18 20,24 20,32 C20,40 24,46 32,46 C40,46 44,40 44,32 C44,24 40,18 32,18 Z" fill="#ffffff" opacity="0.6"/>
            <path d="M32,36 C32,36 24,30 24,25 C24,21 27,19 30,21 C31,22 32,23 32,23 C32,23 33,22 34,21 C37,19 40,21 40,25 C40,30 32,36 32,36 Z" fill="#4BD3A6"/>
        </svg>
        """
    return clean_html(svg)


# Inject Design Tokens and Global Custom CSS Overrides
st.markdown(
    clean_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@300..700&family=Quicksand:wght@300..700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Quicksand', sans-serif !important;
        background: radial-gradient(circle at 0% 0%, #FFFDFB 0%, #FFF5F0 50%, #FAF0E6 100%) !important;
    }

    h1, h2, h3, h4, h5, h6, .stSubheader, .stTitle {
        font-family: 'Fredoka', sans-serif !important;
        color: #4A3E3D !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFF0E6 0%, #FFE5D9 100%) !important;
        border-right: 3px solid #FFD8C9 !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h3 {
        color: #FF5757 !important;
    }

    /* Style sidebar widgets natively as cards */
    [data-testid="stSidebar"] [data-testid="metric-container"],
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stSlider {
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 20px !important;
        padding: 12px 18px !important;
        border: 2px solid #FFF0E6 !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 12px rgba(255, 122, 96, 0.04) !important;
    }

    .custom-card {
        background: #ffffff;
        border-radius: 24px;
        border: 2px solid #FFF0E6;
        padding: 16px 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 20px rgba(255, 122, 96, 0.03);
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    .custom-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 15px 30px rgba(255, 122, 96, 0.1);
        border-color: #FFB3A6;
    }

    .priority-badge {
        font-size: 0.8em;
        padding: 5px 12px;
        border-radius: 50px;
        font-weight: 700;
        text-transform: uppercase;
        color: white;
        display: inline-block;
    }
    .badge-critical { background: linear-gradient(135deg, #FF5757 0%, #FF2A2A 100%); }
    .badge-high     { background: linear-gradient(135deg, #FF9F43 0%, #FF7B00 100%); }
    .badge-medium   { background: linear-gradient(135deg, #9C8DFB 0%, #7663FA 100%); }
    .badge-low      { background: linear-gradient(135deg, #4BD3A6 0%, #1AC08E 100%); }

    .custom-warning {
        background: #FFF9E6;
        border-left: 6px solid #FFC93C;
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(255, 201, 60, 0.08);
    }
    .custom-success {
        background: #EAFBF5;
        border-left: 6px solid #4BD3A6;
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(75, 211, 166, 0.08);
    }

    .timeline-time {
        font-family: 'Fredoka', sans-serif;
        font-weight: bold;
        color: #FF7A60;
        font-size: 1.15em;
        background: #FFEFEA;
        padding: 3px 10px;
        border-radius: 12px;
    }
    .task-title {
        font-family: 'Fredoka', sans-serif;
        font-size: 1.1em;
        color: #4A3E3D;
        margin-left: 8px;
    }

    /* Global inputs/text fields rounded SOTA overrides */
    .stApp input[type="text"], .stApp input[type="number"], .stApp textarea {
        border-radius: 16px !important;
        border: 2px solid #FFF0E6 !important;
        background-color: #FFFDFB !important;
        font-family: 'Quicksand', sans-serif !important;
        color: #4A3E3D !important;
        padding: 10px 16px !important;
        transition: all 0.25s ease !important;
    }
    .stApp input[type="text"]:focus, .stApp input[type="number"]:focus, .stApp textarea:focus {
        border-color: #FF7A60 !important;
        box-shadow: 0 0 0 3px rgba(255, 122, 96, 0.15) !important;
        background-color: #ffffff !important;
    }

    /* Style selectbox input containers globally */
    div[data-baseweb="select"] > div {
        border-radius: 16px !important;
        border: 2px solid #FFF0E6 !important;
        background-color: #FFFDFB !important;
        font-family: 'Quicksand', sans-serif !important;
        color: #4A3E3D !important;
        padding: 2px 8px !important;
        transition: all 0.25s ease !important;
    }
    div[data-baseweb="select"]:focus-within > div, div[data-baseweb="select"]:hover > div {
        border-color: #FF7A60 !important;
        background-color: #ffffff !important;
    }

    div[data-testid="stTabBar"] {
        background: #FFF5F0 !important;
        border-radius: 24px !important;
        padding: 6px !important;
        gap: 8px !important;
        border: 2px solid #FFF0E6 !important;
    }
    div[data-testid="stTabBar"] button {
        font-family: 'Fredoka', sans-serif !important;
        font-size: 15px !important;
        border-radius: 18px !important;
        color: #8B7775 !important;
        background: transparent !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    div[data-testid="stTabBar"] button[aria-selected="true"] {
        background: #ffffff !important;
        color: #FF7A60 !important;
        box-shadow: 0 4px 12px rgba(255, 122, 96, 0.1) !important;
    }

    /* BUTTON CUSTOM OVERRIDES VIA SIBLING MARKERS */
    
    /* Primary buttons (Generate Plan, Register Pet, Add Task) */
    div:has(.primary-btn-marker) + div .stButton > button {
        background: linear-gradient(135deg, #FF7A60 0%, #FF5757 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 12px 28px !important;
        font-family: 'Fredoka', sans-serif !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        box-shadow: 0 6px 18px rgba(255, 87, 87, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        width: 100% !important;
    }
    div:has(.primary-btn-marker) + div .stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 10px 25px rgba(255, 87, 87, 0.4) !important;
        color: white !important;
    }

    /* Done Checklist button styling */
    div:has(.done-btn-marker) + div .stButton > button {
        background: linear-gradient(135deg, #4BD3A6 0%, #1AC08E 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        box-shadow: 0 4px 12px rgba(75, 211, 166, 0.2) !important;
        padding: 8px 16px !important;
        font-family: 'Fredoka', sans-serif !important;
        font-weight: bold;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div:has(.done-btn-marker) + div .stButton > button:hover {
        box-shadow: 0 8px 20px rgba(75, 211, 166, 0.35) !important;
        transform: translateY(-2px) scale(1.02) !important;
        color: white !important;
    }

    /* Danger Remove button styling */
    div:has(.danger-btn-marker) + div .stButton > button {
        background: linear-gradient(135deg, #FF9F8E 0%, #FF5757 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 12px rgba(255, 87, 87, 0.15) !important;
        padding: 8px 16px !important;
        font-family: 'Fredoka', sans-serif !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div:has(.danger-btn-marker) + div .stButton > button:hover {
        box-shadow: 0 8px 20px rgba(255, 87, 87, 0.3) !important;
        transform: translateY(-2px) !important;
        color: white !important;
    }

    /* Trash button styling */
    div:has(.trash-btn-marker) + div .stButton > button {
        background: #F8F5F2 !important;
        color: #A6918F !important;
        border: 1px solid #FFE5D9 !important;
        box-shadow: none !important;
        border-radius: 12px !important;
        padding: 6px 10px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
        width: auto !important;
    }
    div:has(.trash-btn-marker) + div .stButton > button:hover {
        background: #FFEBEA !important;
        color: #FF5757 !important;
        border-color: #FFC5BB !important;
        transform: translateY(-1px) !important;
    }

    /* Recalculate button styling */
    div:has(.recalc-btn-marker) + div .stButton > button {
        background: linear-gradient(135deg, #FF9F43 0%, #FF7B00 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 15px rgba(255, 123, 0, 0.2) !important;
        font-family: 'Fredoka', sans-serif !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    div:has(.recalc-btn-marker) + div .stButton > button:hover {
        box-shadow: 0 8px 25px rgba(255, 123, 0, 0.35) !important;
        transform: translateY(-2px) !important;
        color: white !important;
    }

    /* Reset button styling */
    div:has(.reset-btn-marker) + div .stButton > button {
        background: transparent !important;
        color: #FF5757 !important;
        border: 2px solid #FFD8C9 !important;
        box-shadow: none !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-family: 'Fredoka', sans-serif !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div:has(.reset-btn-marker) + div .stButton > button:hover {
        background: #FFE5D9 !important;
        color: #E05B43 !important;
        border-color: #FFB3A6 !important;
        transform: translateY(-2px) !important;
    }

    .pet-mascot-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 15px;
    }
    @keyframes tail-wag {
        0% { transform: rotate(0deg); }
        25% { transform: rotate(10deg); }
        50% { transform: rotate(-10deg); }
        75% { transform: rotate(10deg); }
        100% { transform: rotate(0deg); }
    }
    .wag-tail {
        animation: tail-wag 1.5s ease-in-out infinite;
        transform-origin: 32px 52px;
    }
    @keyframes head-bob {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-3px); }
    }
    .bob-head {
        animation: head-bob 3s ease-in-out infinite;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .animated-card {
        animation: fadeInUp 0.5s ease-out both;
    }

    .progress-container {
        background: #FFF0E6;
        border-radius: 50px;
        height: 28px;
        position: relative;
        overflow: hidden;
        border: 2px solid #FFE5D9;
        margin: 15px 0;
    }
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #FF7A60 0%, #FF9F43 100%);
        border-radius: 50px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 15px;
        color: white;
        font-size: 0.9em;
        font-weight: bold;
    }
    </style>
    """),
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
    st.markdown(
        clean_html(f'<div class="pet-mascot-container">{get_mascot_svg()}</div>'),
        unsafe_allow_html=True
    )
    st.markdown(clean_html("<h2 style='text-align: center; margin-top: 0; font-family: Fredoka;'>PawPal+</h2>"), unsafe_allow_html=True)
    
    st.subheader("Owner Profile")
    owner.name  = st.text_input("Name",  value=owner.name)
    owner.email = st.text_input("Email", value=owner.email)
    owner.available_hours_per_day = st.slider(
        "Daily Budget (hours)", 0.5, 12.0, float(owner.available_hours_per_day), 0.5
    )
    
    st.subheader("Quick Stats")
    sc1, sc2 = st.columns(2)
    with sc1:
        st.metric("Pets", len(owner.get_all_pets()))
    with sc2:
        st.metric("Tasks", sum(len(p.get_tasks()) for p in owner.get_all_pets()))
    
    # Persist any sidebar edits (name, email, budget) immediately
    _save(owner)

    st.markdown(clean_html('<div class="reset-btn-marker"></div>'), unsafe_allow_html=True)
    if st.button("Reset to demo data"):
        _reset()
        st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    clean_html(f"""
    <div style='background: linear-gradient(135deg, #FFE5D9 0%, #FFF0E6 100%); padding: 25px; border-radius: 24px; border: 2px solid #FFF0E6; margin-bottom: 25px;'>
        <h1 style='margin: 0; font-family: "Fredoka", sans-serif; color: #FF7A60;'>🐾 {owner.name}'s Care Dashboard</h1>
        <p style='margin: 5px 0 0 0; font-family: "Quicksand", sans-serif; color: #8B7775; font-size: 1.1em;'>
            Managing schedule for <strong>{len(owner.get_all_pets())} pets</strong> • Daily time budget: <strong>{int(owner.available_hours_per_day * 60)} minutes</strong>
        </p>
    </div>
    """),
    unsafe_allow_html=True
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
        sched = st.session_state.get("sched_data")
        if not sched:
            st.markdown(get_empty_schedule_svg(), unsafe_allow_html=True)
            st.markdown(clean_html('<div class="primary-btn-marker"></div>'), unsafe_allow_html=True)
            if st.button("🚀 Generate Today's Care Plan", use_container_width=True):
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

        if sched:
            scheduler: DailyScheduler = sched["scheduler"]
            
            # ---- Budget Gauge -----------------------------------------------
            time_limit = sched["budget"]
            time_used = sum(entry["task"].duration_minutes for entry in sched["scheduled"])
            percentage = min(100, int((time_used / time_limit) * 100)) if time_limit > 0 else 0
            
            st.markdown(clean_html(f"""
            <h4 style='font-family: Fredoka, sans-serif; color: #4A3E3D; margin-bottom: 5px;'>Daily Time Budget Utilization</h4>
            <div class="progress-container">
                <div class="progress-bar-fill" style="width: {percentage}%;">
                    {time_used} / {time_limit} min ({percentage}%)
                </div>
            </div>
            """), unsafe_allow_html=True)

            # ---- Conflict banners -------------------------------------------
            conflicts = [l for l in sched["reasoning"] if "CONFLICT" in l]
            if conflicts:
                st.markdown("#### ⚠️ Scheduling Conflicts Detected")
                for c in conflicts:
                    msg = c.replace("CONFLICT  ", "").replace("CONFLICT ", "")
                    st.markdown(clean_html(f"""
                    <div class="custom-warning">
                        <strong>⚠️ Conflict:</strong> {msg}
                    </div>
                    """), unsafe_allow_html=True)
            else:
                st.markdown(clean_html("""
                <div class="custom-success">
                    <strong>✨ Clear Schedule:</strong> No conflicts detected for today's plan!
                </div>
                """), unsafe_allow_html=True)

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
                    st.info("No pending tasks match the current filter.")
                else:
                    for entry in sorted_entries:
                        task: Task = entry["task"]
                        pet:  Pet  = entry["pet"]
                        start = entry["start_minute"]
                        h, m = divmod(start, 60)
                        
                        col_card, col_action = st.columns([5, 1.2])
                        with col_card:
                            icon_html = get_category_svg(task.category)
                            badge_html = f'<span class="priority-badge badge-{task.priority}">{task.priority}</span>'
                            recur_badge = '<span style="background: #E8E5FF; color: #7663FA; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; margin-left: 5px;">🔁 Recurring</span>' if task.is_recurring else ''
                            st.markdown(
                                clean_html(f"""
                                <div class="custom-card priority-{task.priority} animated-card" style="display: flex; align-items: center; gap: 15px; margin-bottom: 12px; padding: 16px;">
                                    <div style="flex-shrink: 0;">{icon_html}</div>
                                    <div style="flex-grow: 1;">
                                        <div style="display: flex; align-items: center; justify-content: space-between;">
                                            <div>
                                                <span class="timeline-time">{h:02d}:{m:02d}</span>
                                                <span class="task-title"><strong>{task.title}</strong></span>
                                                {recur_badge}
                                            </div>
                                            <div>{badge_html}</div>
                                        </div>
                                        <div style="color: #8B7775; font-size: 0.9em; margin-top: 5px;">
                                            ⏰ {task.duration_minutes} min &nbsp;•&nbsp; 🐾 <strong>{pet.name}</strong> ({pet.breed}) &nbsp;•&nbsp; Preferred: {task.time_slot_preference}
                                        </div>
                                    </div>
                                </div>
                                """),
                                unsafe_allow_html=True,
                            )
                        with col_action:
                            st.markdown(clean_html('<div class="done-btn-marker" style="margin-top: 25px;"></div>'), unsafe_allow_html=True)
                            if st.button("Done", key=f"comp_{task.task_id}"):
                                task.mark_as_completed()
                                if task.is_recurring:
                                    next_task = task.generate_next_occurrence()
                                    if next_task:
                                        pet.add_task(next_task)
                                _save(owner)
                                
                                # Regenerate schedule
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

            with col_deferred:
                st.markdown(f"#### Deferred ({len(sched['deferred'])} tasks)")
                if not sched["deferred"]:
                    st.markdown(clean_html("""
                    <div class="custom-success" style="padding: 20px; text-align: center; border-left: none;">
                        <h4 style="margin: 0 0 5px 0; color: #1AC08E; font-family: Fredoka;">Perfect fit!</h4>
                        <p style="margin: 0; color: #8B7775; font-size: 0.9em;">All tasks fit within the daily budget!</p>
                    </div>
                    """), unsafe_allow_html=True)
                else:
                    for task in sched["deferred"]:
                        pet = next((e["pet"] for e in scheduler.task_pool if e["task"].task_id == task.task_id), None)
                        pet_name = pet.name if pet else "Pet"
                        icon_html = get_category_svg(task.category)
                        badge_html = f'<span class="priority-badge badge-{task.priority}">{task.priority}</span>'
                        st.markdown(
                            clean_html(f"""
                            <div class="custom-card priority-deferred animated-card" style="padding: 15px; margin-bottom: 10px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div style="flex-shrink: 0; opacity: 0.7;">{icon_html}</div>
                                    <div style="flex-grow: 1;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <span style="font-family: Fredoka; font-size: 1em; color: #8B7775; text-decoration: line-through;"><strong>{task.title}</strong></span>
                                            {badge_html}
                                        </div>
                                        <div style="color: #A6918F; font-size: 0.85em; margin-top: 4px;">
                                            ⏳ {task.duration_minutes} min &nbsp;•&nbsp; 🐾 <strong>{pet_name}</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """),
                            unsafe_allow_html=True,
                        )

            # ---- Completed Tasks History ------------------------------------
            completed_entries = []
            for pet in owner.get_all_pets():
                for task in pet.get_tasks():
                    if task.is_completed:
                        completed_entries.append((task, pet))
            
            if completed_entries:
                st.markdown("---")
                st.markdown("<h3 style='font-family: Fredoka; color: #1AC08E; margin-top: 20px;'>🎉 Completed Tasks Today</h3>", unsafe_allow_html=True)
                
                if pet_name_arg:
                    completed_entries = [e for e in completed_entries if e[1].name.lower() == pet_name_arg.lower()]
                
                if not completed_entries:
                    st.info("No completed tasks match the current pet filter.")
                else:
                    comp_cols = st.columns(3)
                    for idx, (task, pet) in enumerate(completed_entries):
                        with comp_cols[idx % 3]:
                            icon_html = get_category_svg(task.category)
                            st.markdown(
                                clean_html(f"""
                                <div class="custom-card animated-card" style="border: 2px solid #4BD3A6; background: #FAFDFB; padding: 15px; margin-bottom: 10px;">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <div style="flex-shrink: 0;">{icon_html}</div>
                                        <div>
                                            <div style="font-family: Fredoka; font-weight: bold; color: #2E7D32;">{task.title}</div>
                                            <div style="font-size: 0.85em; color: #666;">🐾 {pet.name} &nbsp;•&nbsp; ✅ Completed</div>
                                        </div>
                                    </div>
                                </div>
                                """),
                                unsafe_allow_html=True
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

            st.markdown(clean_html('<div class="recalc-btn-marker"></div>'), unsafe_allow_html=True)
            if st.button("Recalculate & Sync Plan"):
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
        
        st.markdown(clean_html('<div class="primary-btn-marker"></div>'), unsafe_allow_html=True)
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
            icon_html = get_species_svg(pet.species)
            notes_str = ", ".join(pet.medical_notes) if pet.medical_notes else "None"
            
            st.markdown(
                clean_html(f"""
                <div class="custom-card pet-card animated-card" style="margin-bottom: 20px; background: #ffffff;">
                    <div style="display: flex; align-items: center; gap: 20px;">
                        <div style="flex-shrink: 0;">{icon_html}</div>
                        <div style="flex-grow: 1;">
                            <h3 style="margin: 0; font-family: Fredoka, sans-serif; color: #FF7A60;">🐾 {pet.name}</h3>
                            <div style="font-size: 0.95em; color: #8B7775; margin-top: 5px;">
                                <strong>Breed:</strong> {pet.breed} &nbsp;•&nbsp; 
                                <strong>Age:</strong> {pet.age_months} months &nbsp;•&nbsp; 
                                <strong>Energy:</strong> <span style="text-transform: capitalize;">{pet.energy_level}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #FF5757; margin-top: 5px;">
                                <strong>⚠️ Medical Notes:</strong> {notes_str}
                            </div>
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )
            
            col_del, col_tasks = st.columns([1, 4])
            with col_del:
                st.markdown(clean_html('<div class="danger-btn-marker"></div>'), unsafe_allow_html=True)
                if st.button(f"Remove {pet.name}", key=f"rp_{pet.pet_id}"):
                    owner.remove_pet(pet.pet_id)
                    _save(owner)
                    st.rerun()
            with col_tasks:
                tasks = pet.get_tasks()
                if tasks:
                    with st.expander(f"View & Manage {pet.name}'s Tasks ({len(tasks)})"):
                        for t in tasks:
                            tc, td = st.columns([5, 1])
                            with tc:
                                t_icon = get_category_svg(t.category)
                                status_label = "✅ Done" if t.is_completed else "⏳ Pending"
                                status_color = "#1AC08E" if t.is_completed else "#9C8DFB"
                                st.markdown(
                                    clean_html(f"""
                                    <div style="display: flex; align-items: center; gap: 10px; padding: 6px 0;">
                                        <div style="flex-shrink: 0;">{t_icon}</div>
                                        <div>
                                            <strong>{t.title}</strong> · {t.category} · {t.duration_minutes} min · 
                                            <span class="priority-badge badge-{t.priority}">{t.priority}</span> ·
                                            <span style="color: {status_color}; font-weight: bold; font-size: 0.9em;">{status_label}</span>
                                        </div>
                                    </div>
                                    """),
                                    unsafe_allow_html=True
                                )
                            with td:
                                st.markdown(clean_html('<div class="trash-btn-marker"></div>'), unsafe_allow_html=True)
                                if st.button("🗑️", key=f"dt_{t.task_id}"):
                                    pet.remove_task(t.task_id)
                                    _save(owner)
                                    st.rerun()


# ---------------------------------------------------------------------------
# Tab 3 — Add Tasks
# ---------------------------------------------------------------------------

with tab3:
    st.markdown("<h3 style='font-family: Fredoka; color: #FF7A60;'>Schedule a Care Task</h3>", unsafe_allow_html=True)
    pets = owner.get_all_pets()
    if not pets:
        st.info("Register a pet first under **Manage Pets**.")
    else:
        pet_map = {p.name: p for p in pets}
        selected_name = st.selectbox("Select Pet *", list(pet_map))
        selected_pet  = pet_map[selected_name]

        st.markdown("<div class='custom-card pet-card' style='background: #FFFFFF;'>", unsafe_allow_html=True)
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
            
            st.markdown(clean_html('<div class="primary-btn-marker"></div>'), unsafe_allow_html=True)
            submit_btn = st.form_submit_button("➕ Add Task to Plan")
            if submit_btn:
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
                    
                    if st.session_state.get("sched_data"):
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
                    
                    st.success(f"Successfully added '{t_title}' to {selected_name}'s schedule!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
