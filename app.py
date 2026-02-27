"""
Swimming Schedule Converter - Calendar View with AI Editing
Paste schedule → AI extracts → View calendar → Edit with AI → Export
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from collections import defaultdict

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import CalendarFormat
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine
from calendar_exporter import CalendarExporter
from shared_calendar_manager import SharedCalendarManager
from pipeline import process_schedule
from settings import DEFAULT_EVENT_TITLE


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Swim Schedule",
    page_icon="🏊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def load_css() -> None:
    """Load static app styles."""
    css_path = Path(__file__).parent / "static" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


load_css()


# ============================================================================
# PASSWORD PROTECTION
# ============================================================================

def check_password():
    """Password gatekeeper for Streamlit Cloud deployment."""
    if "APP_PASSWORD" not in st.secrets:
        return True
    
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct:
        return True
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🏊 Swim Schedule")
        st.markdown("#### Enter password")
        
        password = st.text_input("Password", type="password", label_visibility="collapsed", 
                                  placeholder="Password...")
        
        if st.button("Login", type="primary", use_container_width=True):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Incorrect password")
    
    return False

if not check_password():
    st.stop()


# ============================================================================
# SESSION STATE
# ============================================================================

def init_session_state() -> None:
    """Initialize Streamlit session state keys used by the app."""
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
        st.session_state.config = st.session_state.config_manager.load()

    if 'events' not in st.session_state:
        st.session_state.events = []

    if 'edit_history' not in st.session_state:
        st.session_state.edit_history = []

    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

    if not st.session_state.api_key and "GEMINI_API_KEY" in st.secrets:
        st.session_state.api_key = st.secrets["GEMINI_API_KEY"]

    if 'show_export_create' not in st.session_state:
        st.session_state.show_export_create = False

    if 'show_export_shared' not in st.session_state:
        st.session_state.show_export_shared = False

    if 'show_share_form_context' not in st.session_state:
        st.session_state.show_share_form_context = None

    if 'selected_shared_calendar_name' not in st.session_state:
        st.session_state.selected_shared_calendar_name = None


init_session_state()

shared_mgr = SharedCalendarManager()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis if longer than max_length"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


# ============================================================================
# SIDEBAR - Minimal
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    if st.session_state.api_key:
        st.success("✓ API Connected", icon="🔑")
    else:
        st.error("✗ API Key Missing")
    
    st.divider()

    # Shared calendar management
    shared_stats = shared_mgr.get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Shared", shared_stats["total_calendars"])
    col2.metric("Size", f"{shared_stats['total_size_kb']:.1f}KB")
    
    if shared_stats["total_calendars"] > 0:
        with st.expander("Manage Shared"):
            shared_list = shared_mgr.list_all()
            for cal in shared_list:
                col_name, col_del = st.columns([3, 1])
                col_name.caption(truncate_text(cal.name, 30))
                if col_del.button("🗑️", key=f"del_{cal.id}"):
                    shared_mgr.delete(cal.id)
                    st.toast(f"Deleted {cal.name}")
                    st.rerun()


# ============================================================================
# CALENDAR VIEW - Weekly Grid
# ============================================================================

def get_week_bounds(dates):
    """Get the Monday-Sunday bounds for all weeks containing events"""
    if not dates:
        return []
    
    min_date = min(dates)
    max_date = max(dates)
    
    # Find Monday of first week
    start_monday = min_date - timedelta(days=min_date.weekday())
    # Find Sunday of last week  
    end_sunday = max_date + timedelta(days=(6 - max_date.weekday()))
    
    weeks = []
    current = start_monday
    while current <= end_sunday:
        weeks.append(current)
        current += timedelta(days=7)
    
    return weeks

def render_calendar_view(events):
    """Render events in a weekly calendar grid table"""
    if not events:
        return
    
    # Group events by date
    events_by_date = defaultdict(list)
    for event in events:
        date_key = event.start_time.date()
        events_by_date[date_key].append(event)
    
    # Get week boundaries
    all_dates = list(events_by_date.keys())
    week_mondays = get_week_bounds(all_dates)
    
    # Days of week headers
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Build HTML table
    html = '<table class="cal-table">'
    html += '<tr>'
    for day in days:
        html += f'<th>{day}</th>'
    html += '</tr>'
    
    # Render each week as a row
    for monday in week_mondays:
        html += '<tr>'
        for i in range(7):
            current_date = monday + timedelta(days=i)
            day_events = events_by_date.get(current_date, [])
            
            html += '<td>'
            html += f'<div class="cal-date">{current_date.strftime("%m/%d")}</div>'
            
            if day_events:
                for event in sorted(day_events, key=lambda e: e.start_time):
                    time_str = f"{event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}"
                    loc_name = event.location.name if event.location else "?"
                    html += f'<div class="cal-event"><span class="cal-time">{time_str}</span><br><span class="cal-loc">{loc_name}</span></div>'
            else:
                html += '<div class="cal-empty">-</div>'
            
            html += '</td>'
        html += '</tr>'
    
    html += '</table>'
    
    st.markdown(html, unsafe_allow_html=True)


def clear_current_events():
    """Clear active events and related UI state."""
    st.session_state.events = []
    st.session_state.edit_history = []
    st.session_state.selected_shared_calendar_name = None
    st.session_state.show_export_create = False
    st.session_state.show_export_shared = False
    st.session_state.show_share_form_context = None


def render_ai_edit_section(key_prefix: str):
    """Render AI edit controls for current events."""
    st.markdown("### ✏️ Edit with AI")
    instructions = st.text_area(
        "Edit instructions",
        height=80,
        placeholder="Examples:\n- Delete the Saturday event\n- Move Friday to 5:30-7:30pm\n- Change all locations to Brandeis",
        label_visibility="collapsed",
        key=f"edit_instructions_{key_prefix}"
    )

    if st.button("🤖 Apply Changes", disabled=not instructions, use_container_width=True, key=f"apply_changes_{key_prefix}"):
        try:
            with st.spinner("Applying edits..."):
                extractor = EventExtractor(
                    api_key=st.session_state.api_key,
                    config=st.session_state.config
                )
                new_events = extractor.edit(st.session_state.events, instructions)
                rules_engine = RulesEngine(st.session_state.config)
                new_events = rules_engine.sort_events(new_events)

                st.session_state.events = new_events
                st.session_state.edit_history.append((instructions, new_events.copy()))
                st.rerun()
        except Exception as e:
            st.error(f"Edit failed: {str(e)}")

    if len(st.session_state.edit_history) > 1:
        with st.expander("📜 Edit History"):
            for i, (action, _) in enumerate(st.session_state.edit_history):
                st.caption(f"{i + 1}. {action[:50]}...")


def render_export_section(events, key_prefix: str, show_shared_label: bool = False):
    """Render export/download and share controls for current events."""
    show_export_key = f"show_export_{key_prefix}"

    if show_shared_label and st.session_state.selected_shared_calendar_name:
        st.caption(f"Using shared calendar: {st.session_state.selected_shared_calendar_name}")

    if st.button("📥 Export", type="primary", use_container_width=True, key=f"export_{key_prefix}"):
        st.session_state[show_export_key] = True

    if not st.session_state.get(show_export_key):
        return

    exporter = CalendarExporter(st.session_state.config)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    ics_content = exporter.export(events, CalendarFormat.ICS)
    ics_data = ics_content.encode('utf-8-sig')
    zip_data = exporter.export_to_ics_zip(events, ics_filename=f"swim_{timestamp}.ics")

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "📄 .ics",
            data=ics_data,
            file_name=f"swim_{timestamp}.ics",
            mime="text/calendar",
            use_container_width=True,
            key=f"download_ics_{key_prefix}"
        )
    with dl2:
        st.download_button(
            "📦 .zip",
            data=zip_data,
            file_name=f"swim_{timestamp}.zip",
            mime="application/zip",
            use_container_width=True,
            key=f"download_zip_{key_prefix}"
        )

    st.divider()

    if st.session_state.show_share_form_context != key_prefix:
        if st.button("📤 Share This Calendar", use_container_width=True, key=f"share_open_{key_prefix}"):
            st.session_state.show_share_form_context = key_prefix
            st.rerun()

    if st.session_state.show_share_form_context == key_prefix:
        st.markdown("**Share with others:**")
        st.caption("Make this calendar publicly available so others can use it without the original text")

        share_name = st.text_input(
            "Calendar Name*",
            placeholder="e.g., MIT Team Practice Schedule - Feb 2026",
            key=f"share_name_{key_prefix}"
        )
        share_desc = st.text_area(
            "Description (optional)",
            placeholder="Weekly practice schedule for MIT team, February 2026",
            height=60,
            key=f"share_desc_{key_prefix}"
        )

        col_save, col_cancel = st.columns(2)

        with col_save:
            if st.button("✓ Share", type="primary", use_container_width=True, disabled=not share_name, key=f"share_confirm_{key_prefix}"):
                try:
                    shared_mgr.save(share_name, share_desc, events)
                    st.success(f"✓ Shared as: {share_name}")
                    st.session_state.show_share_form_context = None
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to share: {str(e)}")

        with col_cancel:
            if st.button("Cancel", use_container_width=True, key=f"share_cancel_{key_prefix}"):
                st.session_state.show_share_form_context = None
                st.rerun()


def render_review_section(events):
    """Render calendar review section for current events."""
    st.markdown("### 📅 Review")
    st.caption(f"{len(events)} event{'s' if len(events) != 1 else ''}")
    render_calendar_view(events)


# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("# 🏊 Swim Schedule Converter")

tab_create, tab_shared, tab_howto = st.tabs(["🆕 Create New", "📚 Use Shared", "❓ How To"])

with tab_create:
    st.markdown("### 📝 Paste Schedule")
    schedule_text = st.text_area(
        "Schedule",
        height=150,
        placeholder="""周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午 5-7 下水
周六 1/31 上午 9-11 @ Brandeis""",
        label_visibility="collapsed",
        key="schedule_input_create"
    )

    action_col1, action_col2 = st.columns([4, 1])
    with action_col1:
        extract_disabled = not schedule_text or not st.session_state.api_key
        if st.button("🤖 Extract Events", type="primary", use_container_width=True, disabled=extract_disabled, key="extract_create"):
            try:
                with st.spinner("Analyzing..."):
                    events = process_schedule(
                        raw_text=schedule_text,
                        api_key=st.session_state.api_key,
                        config=st.session_state.config,
                    )

                    for event in events:
                        if not event.summary:
                            event.summary = DEFAULT_EVENT_TITLE

                    st.session_state.events = events
                    st.session_state.edit_history = [("Initial extraction", events.copy())]
                    st.session_state.selected_shared_calendar_name = None
                    st.session_state.show_export_create = False
                    st.session_state.show_export_shared = False
                    st.session_state.show_share_form_context = None
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with action_col2:
        if st.button("Clear", use_container_width=True, key="clear_create"):
            clear_current_events()
            st.rerun()

    if st.session_state.events:
        render_ai_edit_section("create")
        render_review_section(st.session_state.events)
        render_export_section(st.session_state.events, "create")
    else:
        st.info("Paste a schedule to create, review, and export a calendar.")

with tab_shared:
    st.markdown("### 📚 Pick Shared Calendar")
    shared_calendars = shared_mgr.list_all()

    if not shared_calendars:
        st.info("No shared calendars yet.")
    else:
        calendar_options = {
            f"{calendar.name} • {calendar.event_count} event{'s' if calendar.event_count != 1 else ''} • {calendar.created_at.strftime('%m/%d/%Y')}": calendar.id
            for calendar in shared_calendars
        }

        selected_label = st.selectbox(
            "Choose a shared calendar",
            options=list(calendar_options.keys()),
            key="shared_picker"
        )

        if st.button("Use Selected", type="primary", use_container_width=True, key="use_shared_selected"):
            calendar_id = calendar_options[selected_label]
            try:
                loaded_calendar = shared_mgr.get_by_id(calendar_id, st.session_state.config.locations)
                if loaded_calendar and loaded_calendar.events:
                    st.session_state.events = loaded_calendar.events
                    st.session_state.edit_history = [(f"Loaded: {loaded_calendar.name}", loaded_calendar.events.copy())]
                    st.session_state.selected_shared_calendar_name = loaded_calendar.name
                    st.session_state.show_export_shared = True
                    st.session_state.show_export_create = False
                    st.session_state.show_share_form_context = None
                    st.toast(f"✓ Loaded {loaded_calendar.name}")
                    st.rerun()
                else:
                    st.error("Calendar has no events or failed to load")
            except Exception as e:
                st.error(f"Failed to load calendar: {str(e)}")

    if st.session_state.events:
        render_review_section(st.session_state.events)
        render_ai_edit_section("shared")
        render_export_section(st.session_state.events, "shared", show_shared_label=True)
    else:
        st.info("Pick a shared calendar to review, edit, and export.")

with tab_howto:
    st.markdown("### Quick Guide")
    st.markdown("**Create New**")
    st.markdown("1. Paste schedule text")
    st.markdown("2. Click **🤖 Extract Events**")
    st.markdown("3. (Optional) Edit with AI")
    st.markdown("4. Review and export as .ics or .zip")

    st.markdown("**Use Shared**")
    st.markdown("1. Pick a shared calendar")
    st.markdown("2. Click **Use Selected**")
    st.markdown("3. Review, edit if needed, then export")

    with st.expander("Minimal examples"):
        st.markdown("**Create New input:**")
        st.code("周四 1/29 下午 6-8 下水+陆上 @ Regis", language="text")
        st.markdown("**AI edit instruction:**")
        st.code("Move Friday to 5:30-7:30pm", language="text")
