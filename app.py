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

from models import Location, Config, CalendarFormat, Event, SharedCalendar
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine
from calendar_exporter import CalendarExporter
from cache_manager import ExtractionCache
from shared_calendar_manager import SharedCalendarManager


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Swim Schedule",
    page_icon="🏊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 900px;
    }
    h1 { font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }
    hr { margin: 1rem 0; border: none; border-top: 1px solid rgba(255,255,255,0.1); }
    
    /* Calendar table styling */
    .cal-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
    .cal-table th {
        background: rgba(74, 158, 255, 0.2);
        padding: 8px 4px;
        text-align: center;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.1);
        min-width: 90px;
    }
    .cal-table td {
        padding: 6px;
        vertical-align: top;
        border: 1px solid rgba(255,255,255,0.1);
        min-height: 60px;
        background: rgba(0,0,0,0.2);
    }
    .cal-date {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.5);
        margin-bottom: 4px;
    }
    .cal-event {
        background: rgba(74, 158, 255, 0.25);
        border-radius: 3px;
        padding: 4px 6px;
        margin: 2px 0;
        font-size: 0.8rem;
        line-height: 1.3;
    }
    .cal-time {
        font-weight: 600;
        color: #4A9EFF;
    }
    .cal-loc {
        color: rgba(255,255,255,0.7);
        font-size: 0.75rem;
    }
    .cal-empty {
        color: rgba(255,255,255,0.2);
        text-align: center;
        padding: 20px 4px;
    }
    .location-footnote {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.6);
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


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

if 'config_manager' not in st.session_state:
    st.session_state.config_manager = ConfigManager()
    st.session_state.config = st.session_state.config_manager.load()

if 'events' not in st.session_state:
    st.session_state.events = []

if 'edit_history' not in st.session_state:
    st.session_state.edit_history = []  # Track edit iterations

if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

# Check Streamlit secrets for API key
if not st.session_state.api_key and "GEMINI_API_KEY" in st.secrets:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]

if 'show_export' not in st.session_state:
    st.session_state.show_export = False

if 'show_share_form' not in st.session_state:
    st.session_state.show_share_form = False


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
    
    # Cache management
    cache = ExtractionCache()
    cache_stats = cache.get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Cache", cache_stats["entries"])
    col2.metric("Hits", f"{cache_stats['hit_rate']:.0f}%")
    
    if st.button("Clear Cache", use_container_width=True):
        cache.clear()
        st.toast("Cache cleared!")
    
    st.divider()
    
    # Shared calendar management
    shared_mgr_sidebar = SharedCalendarManager()
    shared_stats = shared_mgr_sidebar.get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Shared", shared_stats["total_calendars"])
    col2.metric("Size", f"{shared_stats['total_size_kb']:.1f}KB")
    
    if shared_stats["total_calendars"] > 0:
        with st.expander("Manage Shared"):
            shared_list = shared_mgr_sidebar.list_all()
            for cal in shared_list:
                col_name, col_del = st.columns([3, 1])
                col_name.caption(cal.name[:30] + "..." if len(cal.name) > 30 else cal.name)
                if col_del.button("🗑️", key=f"del_{cal.id}"):
                    shared_mgr_sidebar.delete(cal.id)
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


# ============================================================================
# AI EDIT FUNCTION
# ============================================================================

def apply_ai_edits(events, instructions):
    """Send events and edit instructions to AI, return updated events"""
    from google import genai
    
    # Convert events to simple format for AI
    events_text = []
    for i, event in enumerate(events, 1):
        loc = event.location.name if event.location else "Unknown"
        events_text.append(
            f"{i}. {event.start_time.strftime('%a %m/%d %H:%M')}-{event.end_time.strftime('%H:%M')} @ {loc}"
        )
    
    current_schedule = "\n".join(events_text)
    
    # Build locations context
    locations_info = "\n".join([
        f"- {name}: {loc.address}"
        for name, loc in st.session_state.config.locations.items()
    ])
    
    prompt = f"""You are a schedule editing assistant. Here is the current swimming schedule:

{current_schedule}

KNOWN LOCATIONS:
{locations_info}

USER'S EDIT REQUEST:
{instructions}

Apply the user's requested changes and return the COMPLETE updated schedule as JSON.
Return ONLY valid JSON (no markdown, no explanations):

{{
  "events": [
    {{
      "start_time": "2026-01-29T18:00:00",
      "end_time": "2026-01-29T20:00:00",
      "summary": "Swim Practice",
      "location_name": "Regis",
      "is_ambiguous": false
    }}
  ]
}}

Rules:
- Keep all events unless user asks to delete them
- Use ISO 8601 format for times
- Use exact location names from the list above
- If summary is not specified, use "Swim Practice"
"""
    
    client = genai.Client(api_key=st.session_state.api_key)
    
    response = client.models.generate_content(
        model=st.session_state.config.gemini_model,
        contents=prompt
    )
    
    response_text = response.text.strip()
    
    # Clean markdown
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    import json
    data = json.loads(response_text)
    
    events_data = data.get("events", data if isinstance(data, list) else [])
    
    # Convert to Event objects
    new_events = []
    for event_data in events_data:
        event = Event(
            start_time=datetime.fromisoformat(event_data["start_time"]),
            end_time=datetime.fromisoformat(event_data["end_time"]),
            summary=event_data.get("summary", "Swim Practice"),
            location_name=event_data.get("location_name"),
            is_ambiguous=event_data.get("is_ambiguous", False)
        )
        
        # Map location
        if event.location_name:
            event.location = st.session_state.config.locations.get(event.location_name)
        
        new_events.append(event)
    
    return new_events


# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("# 🏊 Swim Schedule Converter")

# ============================================================================
# SHARED CALENDAR LIBRARY (Browse before input)
# ============================================================================

shared_mgr = SharedCalendarManager()
shared_calendars = shared_mgr.list_all()

if shared_calendars:
    with st.expander(f"📚 Browse Shared Calendars ({len(shared_calendars)} available)", expanded=False):
        st.caption("These calendars were shared by other users. Click 'Use This' to load events directly.")
        
        for calendar in shared_calendars:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{calendar.name}**")
                    if calendar.description:
                        st.caption(calendar.description)
                    st.caption(f"📅 {calendar.event_count} event{'s' if calendar.event_count != 1 else ''} • "
                             f"🕒 {calendar.created_at.strftime('%m/%d/%Y')}")
                
                with col2:
                    if st.button("Use This", key=f"use_{calendar.id}", use_container_width=True):
                        # Load this calendar's events into session
                        loaded_calendar = shared_mgr.get_by_id(calendar.id, st.session_state.config.locations)
                        if loaded_calendar:
                            st.session_state.events = loaded_calendar.events
                            st.session_state.edit_history = [(f"Loaded: {calendar.name}", loaded_calendar.events.copy())]
                            st.session_state.show_export = False
                            st.session_state.show_share_form = False
                            st.toast(f"✓ Loaded {calendar.name}")
                            st.rerun()
                        else:
                            st.error("Failed to load calendar")
                
                st.divider()

# ============================================================================
# STEP 1: INPUT
# ============================================================================

st.markdown("### 📝 Paste Schedule")

schedule_text = st.text_area(
    "Schedule",
    height=150,
    placeholder="""周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午 5-7 下水
周六 1/31 上午 9-11 @ Brandeis""",
    label_visibility="collapsed",
    key="schedule_input"
)

col1, col2 = st.columns([4, 1])

with col1:
    extract_disabled = not schedule_text or not st.session_state.api_key
    if st.button("🤖 Extract Events", type="primary", use_container_width=True, disabled=extract_disabled):
        try:
            with st.spinner("Analyzing..."):
                extractor = EventExtractor(
                    api_key=st.session_state.api_key,
                    config=st.session_state.config
                )
                events = extractor.extract(schedule_text)
                
                # Apply rules
                rules_engine = RulesEngine(st.session_state.config)
                events = rules_engine.apply_location_rules(events)
                events = rules_engine.merge_overlapping_events(events)
                events = rules_engine.deduplicate_events(events)
                events = rules_engine.sort_events(events)
                
                # Ensure all events have summary
                for event in events:
                    if not event.summary:
                        event.summary = "Swim Practice"
                
                st.session_state.events = events
                st.session_state.edit_history = [("Initial extraction", events.copy())]
                st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.events = []
        st.session_state.edit_history = []
        st.rerun()

st.divider()

# ============================================================================
# STEP 2: CALENDAR VIEW & EDITING
# ============================================================================

if st.session_state.events:
    events = st.session_state.events
    
    # Header with export
    col_title, col_export = st.columns([3, 1])
    
    with col_title:
        st.markdown(f"### 📅 {len(events)} Event{'s' if len(events) != 1 else ''}")
    
    with col_export:
        if st.button("📥 Export", type="primary", use_container_width=True):
            st.session_state.show_export = True
    
    # Export section
    if st.session_state.get('show_export'):
        exporter = CalendarExporter(st.session_state.config)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        ics_content = exporter.export(events, CalendarFormat.ICS)
        ics_data = ics_content.encode('utf-8-sig')
        zip_data = exporter.export_to_ics_zip(events, ics_filename=f"swim_{timestamp}.ics")
        
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("📄 .ics", data=ics_data, 
                             file_name=f"swim_{timestamp}.ics", mime="text/calendar",
                             use_container_width=True)
        with dl2:
            st.download_button("📦 .zip", data=zip_data,
                             file_name=f"swim_{timestamp}.zip", mime="application/zip", 
                             use_container_width=True)
        
        # Share calendar option (after export)
        st.divider()
        
        if not st.session_state.get('show_share_form'):
            if st.button("📤 Share This Calendar", use_container_width=True):
                st.session_state.show_share_form = True
                st.rerun()
        
        if st.session_state.get('show_share_form'):
            st.markdown("**Share with others:**")
            st.caption("Make this calendar publicly available so others can use it without the original text")
            
            share_name = st.text_input("Calendar Name*", placeholder="e.g., MIT Team Practice Schedule - Feb 2026", key="share_name")
            share_desc = st.text_area("Description (optional)", placeholder="Weekly practice schedule for MIT team, February 2026", 
                                     height=60, key="share_desc")
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                if st.button("✓ Share", type="primary", use_container_width=True, disabled=not share_name):
                    try:
                        shared_calendar = shared_mgr.save(share_name, share_desc, events)
                        st.success(f"✓ Shared as: {share_name}")
                        st.session_state.show_share_form = False
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to share: {str(e)}")
            
            with col_cancel:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_share_form = False
                    st.rerun()
        
        st.divider()
    
    # Calendar view
    render_calendar_view(events)
    
    st.divider()
    
    # AI Edit section
    st.markdown("### ✏️ Edit with AI")
    st.caption("Describe changes in natural language")
    
    edit_instructions = st.text_area(
        "Edit instructions",
        height=80,
        placeholder="Examples:\n- Delete the Saturday event\n- Move Friday to 5:30-7:30pm\n- Change all locations to Brandeis",
        label_visibility="collapsed",
        key="edit_instructions"
    )
    
    if st.button("🤖 Apply Changes", disabled=not edit_instructions, use_container_width=True):
        try:
            with st.spinner("Applying edits..."):
                new_events = apply_ai_edits(st.session_state.events, edit_instructions)
                
                # Apply rules
                rules_engine = RulesEngine(st.session_state.config)
                new_events = rules_engine.sort_events(new_events)
                
                st.session_state.events = new_events
                st.session_state.edit_history.append((edit_instructions, new_events.copy()))
                st.toast(f"✓ Applied: {edit_instructions[:30]}...")
                st.rerun()
        except Exception as e:
            st.error(f"Edit failed: {str(e)}")
    
    # Edit history
    if len(st.session_state.edit_history) > 1:
        with st.expander("📜 Edit History"):
            for i, (action, _) in enumerate(st.session_state.edit_history):
                st.caption(f"{i+1}. {action[:50]}...")

else:
    # Empty state
    st.markdown("### 📅 Calendar")
    st.info("👆 Paste your schedule and click **Extract Events**")
    
    with st.expander("Supported formats"):
        st.markdown("""
        **Chinese:** `周四 1/29 下午 6-8 下水 @ Regis`
        
        **English:** `Thu Jan 29 6-8pm @ Regis`
        """)
