"""
Swimming Schedule Converter - Professional UI
AI-powered schedule extraction with clean, modern interface
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import Location, Config, CalendarFormat, Event
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine
from calendar_exporter import CalendarExporter
from cache_manager import ExtractionCache


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
    
    # Centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🏊 Swim Schedule")
        st.markdown("#### Enter password to continue")
        
        password = st.text_input("Password", type="password", label_visibility="collapsed", 
                                  placeholder="Enter password...")
        
        if st.button("Login", type="primary", use_container_width=True):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Incorrect password")
    
    return False


# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="Swim Schedule",
    page_icon="🏊",
    layout="centered",  # Changed back to centered for better readability
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main container - more breathing room */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* Compact header area */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Better text area */
    .stTextArea textarea {
        font-size: 14px;
        line-height: 1.5;
    }
    
    /* Subtle dividers */
    hr {
        margin: 1rem 0;
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Compact metrics in sidebar */
    [data-testid="stMetricValue"] {
        font-size: 1.1rem;
    }
    
    /* Event list styling */
    .event-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Download buttons - more prominent */
    .stDownloadButton button {
        font-weight: 500;
    }
    
    /* Cleaner expanders */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# Password check
if not check_password():
    st.stop()


# ============================================================================
# SESSION STATE
# ============================================================================

if 'config_manager' not in st.session_state:
    st.session_state.config_manager = ConfigManager()
    st.session_state.config = st.session_state.config_manager.load()

if 'cache' not in st.session_state:
    st.session_state.cache = ExtractionCache()

if 'events' not in st.session_state:
    st.session_state.events = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")

# Also check Streamlit secrets for API key
if not st.session_state.api_key and "GEMINI_API_KEY" in st.secrets:
    st.session_state.api_key = st.secrets["GEMINI_API_KEY"]


# ============================================================================
# SIDEBAR - Settings (collapsed by default)
# ============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # API Status
    if st.session_state.api_key:
        st.success("✓ API Connected", icon="🔑")
    else:
        st.error("✗ API Key Missing")
        st.caption("Add GEMINI_API_KEY to secrets")
    
    st.divider()
    
    # Event Settings
    st.markdown("### Event Defaults")
    config = st.session_state.config
    
    new_title = st.text_input(
        "Default Title",
        value=config.default_event_title,
        help="Default title for extracted events"
    )
    
    if new_title != config.default_event_title:
        config.default_event_title = new_title
        st.session_state.config_manager.save()
        st.toast("Title updated!")
    
    st.divider()
    
    # Cache
    st.markdown("### Cache")
    cache_stats = st.session_state.cache.get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Entries", cache_stats["entries"])
    col2.metric("Hit Rate", f"{cache_stats['hit_rate']:.0f}%")
    
    if st.button("Clear Cache", use_container_width=True):
        st.session_state.cache.clear()
        st.toast("Cache cleared!")
        st.rerun()
    
    st.divider()
    
    # Locations (collapsible)
    with st.expander("📍 Locations"):
        for name, loc in config.locations.items():
            st.markdown(f"**{name}**")
            st.caption(loc.address[:50] + "..." if len(loc.address) > 50 else loc.address)


# ============================================================================
# MAIN APP
# ============================================================================

# Compact Header
st.markdown("# 🏊 Swim Schedule Converter")

# Input Section
st.markdown("### 📝 Paste Schedule")

schedule_text = st.text_area(
    "Schedule text",
    height=200,
    placeholder="""周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午 5-7 下水
周六 1/31 上午 9-11 @ Brandeis""",
    label_visibility="collapsed"
)

# Action buttons in a row
col_process, col_clear = st.columns([4, 1])

with col_process:
    process_disabled = not schedule_text or not st.session_state.api_key
    process_clicked = st.button(
        "🤖 Extract Events", 
        type="primary", 
        use_container_width=True, 
        disabled=process_disabled
    )

with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.events = []
        st.session_state.pop('show_downloads', None)
        st.rerun()

# Process schedule
if process_clicked:
    try:
        with st.spinner("Analyzing schedule..."):
            extractor = EventExtractor(
                api_key=st.session_state.api_key,
                config=st.session_state.config
            )
            events = extractor.extract(schedule_text)
            cache_hit = extractor.last_cache_hit
        
        if events:
            rules_engine = RulesEngine(st.session_state.config)
            events = rules_engine.apply_location_rules(events)
            events = rules_engine.merge_overlapping_events(events)
            events = rules_engine.deduplicate_events(events)
            events = rules_engine.sort_events(events)
            
            st.session_state.events = events
            st.session_state.pop('show_downloads', None)
            
            if cache_hit:
                st.toast(f"⚡ Retrieved {len(events)} events from cache!")
            else:
                st.toast(f"✓ Extracted {len(events)} events!")
            st.rerun()
        else:
            st.warning("No events found in the text")
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.divider()

# ============================================================================
# RESULTS SECTION
# ============================================================================

if st.session_state.events:
    events = st.session_state.events
    
    # Results header with export button
    col_title, col_export = st.columns([3, 1])
    
    with col_title:
        st.markdown(f"### 📅 {len(events)} Event{'s' if len(events) != 1 else ''} Found")
    
    with col_export:
        export_clicked = st.button("📥 Export", type="primary", use_container_width=True)
    
    # Show download options
    if export_clicked or st.session_state.get('show_downloads'):
        st.session_state.show_downloads = True
        
        exporter = CalendarExporter(st.session_state.config)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate exports
        ics_content = exporter.export(events, CalendarFormat.ICS)
        ics_data = ics_content.encode('utf-8-sig')
        zip_data = exporter.export_to_ics_zip(events, ics_filename=f"swim_{timestamp}.ics")
        
        # Download buttons
        dl_col1, dl_col2 = st.columns(2)
        
        with dl_col1:
            st.download_button(
                "📄 Download .ics",
                data=ics_data,
                file_name=f"swim_schedule_{timestamp}.ics",
                mime="text/calendar",
                use_container_width=True
            )
        
        with dl_col2:
            st.download_button(
                "📦 Download .zip",
                data=zip_data,
                file_name=f"swim_schedule_{timestamp}.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        st.caption("💡 Use .ics for direct import, .zip for iOS Files app")
        st.divider()
    
    # Events list - clean and scannable
    for i, event in enumerate(events):
        col_main, col_edit = st.columns([6, 1])
        
        with col_main:
            # Date and time on one line
            date_str = event.start_time.strftime("%a %m/%d")
            time_str = f"{event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}"
            loc_name = event.location.name if event.location else "?"
            
            st.markdown(f"**{date_str}** &nbsp;·&nbsp; {time_str} &nbsp;·&nbsp; 📍 {loc_name}")
            
            if event.notes:
                st.caption(event.notes[:80] + ("..." if len(event.notes) > 80 else ""))
        
        with col_edit:
            if st.button("✏️", key=f"edit_{i}", help="Edit"):
                st.session_state.editing_event = i
        
        # Inline edit form
        if st.session_state.get('editing_event') == i:
            with st.container():
                st.markdown("---")
                
                new_summary = st.text_input("Title", value=event.summary, key=f"sum_{i}")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    new_date = st.date_input("Date", value=event.start_time.date(), key=f"date_{i}")
                with c2:
                    new_start = st.time_input("Start", value=event.start_time.time(), key=f"start_{i}")
                with c3:
                    new_end = st.time_input("End", value=event.end_time.time(), key=f"end_{i}")
                with c4:
                    location_names = list(st.session_state.config.locations.keys())
                    current_loc = event.location.name if event.location else location_names[0]
                    new_loc = st.selectbox("Location", location_names, 
                                           index=location_names.index(current_loc) if current_loc in location_names else 0,
                                           key=f"loc_{i}")
                
                bc1, bc2, bc3 = st.columns([1, 1, 2])
                with bc1:
                    if st.button("💾 Save", key=f"save_{i}", type="primary", use_container_width=True):
                        st.session_state.events[i] = Event(
                            start_time=datetime.combine(new_date, new_start),
                            end_time=datetime.combine(new_date, new_end),
                            summary=new_summary,
                            location=st.session_state.config.locations[new_loc],
                            location_name=new_loc,
                            is_ambiguous=event.is_ambiguous,
                            raw_text=event.raw_text,
                            notes=event.notes
                        )
                        st.session_state.editing_event = None
                        st.rerun()
                with bc2:
                    if st.button("🗑️", key=f"del_{i}", help="Delete", use_container_width=True):
                        st.session_state.events.pop(i)
                        st.session_state.editing_event = None
                        st.rerun()
                with bc3:
                    if st.button("Cancel", key=f"cancel_{i}", use_container_width=True):
                        st.session_state.editing_event = None
                        st.rerun()
                
                st.markdown("---")
        
        # Light separator between events
        if i < len(events) - 1 and st.session_state.get('editing_event') != i:
            st.markdown("<div style='border-bottom: 1px solid rgba(255,255,255,0.05); margin: 0.5rem 0;'></div>", 
                       unsafe_allow_html=True)

else:
    # Empty state
    st.markdown("### 📅 Events")
    st.info("👆 Paste your schedule above and click **Extract Events**")
    
    with st.expander("📖 Supported Formats", expanded=False):
        st.markdown("""
        **Chinese:** `周四 1/29 下午 6-8 下水 @ Regis`
        
        **English:** `Thu Jan 29 6-8pm @ Regis`
        
        **Features:**
        - Combines water + dryland sessions automatically
        - Recognizes pool locations
        - Preserves original text in notes
        """)
