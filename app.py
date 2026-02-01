"""
Streamlit Web Interface for Swimming Schedule Converter - Refactored
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

from models import Location, Config, CalendarFormat
from config_manager import ConfigManager
from extractor import EventExtractor
from rules_engine import RulesEngine
from calendar_exporter import CalendarExporter
from cache_manager import ExtractionCache


def check_password():
    """
    Password gatekeeper for Streamlit Cloud deployment.
    
    If APP_PASSWORD is set in st.secrets, requires user to enter password.
    If not set (local development), allows access without password.
    
    Returns:
        bool: True if access is granted, False otherwise
    """
    # Check if password protection is enabled
    if "APP_PASSWORD" not in st.secrets:
        # No password set - allow access (local development mode)
        return True
    
    # Password is set - require authentication
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    
    if st.session_state.password_correct:
        return True
    
    # Show password input in sidebar
    with st.sidebar:
        st.header("🔐 Login Required")
        password = st.text_input("Enter password:", type="password", key="password_input")
        
        if st.button("Login", type="primary"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        
        st.info("This app is password-protected. Please enter the password to continue.")
    
    return False


# Page config
st.set_page_config(
    page_title="Swim Schedule",
    page_icon="🏊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Password check - must be after page config but before app content
if not check_password():
    st.title("🏊 Swim Schedule Converter")
    st.warning("Please enter the password in the sidebar to access the app.")
    st.stop()

# Initialize session state
if 'config_manager' not in st.session_state:
    st.session_state.config_manager = ConfigManager()
    st.session_state.config = st.session_state.config_manager.load()

if 'cache' not in st.session_state:
    st.session_state.cache = ExtractionCache()

if 'events' not in st.session_state:
    st.session_state.events = []

if 'validated_events' not in st.session_state:
    st.session_state.validated_events = []

if 'last_cache_hit' not in st.session_state:
    st.session_state.last_cache_hit = False


def render_sidebar():
    """Render sidebar with configuration"""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key from environment only - reload each time
        load_dotenv(override=True)  # Force reload
        st.session_state.api_key = os.getenv("GEMINI_API_KEY", "")
        
        if not st.session_state.api_key:
            st.error("⚠️ API key not found")
            st.info("Add GEMINI_API_KEY to .env file and restart app")
        else:
            st.success("✓ API key configured")
        
        # Event Title Configuration
        st.header("📝 Event Settings")
        config = st.session_state.config
        
        new_title = st.text_input(
            "Default Event Title",
            value=config.default_event_title,
            help="This title will be used for all new events"
        )
        
        if new_title != config.default_event_title:
            if st.button("Update Title", type="secondary"):
                config.default_event_title = new_title
                st.session_state.config_manager.save()
                st.success(f"✓ Default title updated to: {new_title}")
                st.rerun()
        
        # Cache Statistics and Controls
        st.header("⚡ Cache")
        
        cache_stats = st.session_state.cache.get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Entries", cache_stats["entries"])
            st.metric("Hits", cache_stats["hits"])
        with col2:
            st.metric("Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
            st.metric("Size", f"{cache_stats['total_size_kb']:.1f} KB")
        
        st.caption(f"TTL: {cache_stats['ttl_days']} days")
        
        col_cache1, col_cache2 = st.columns(2)
        with col_cache1:
            if st.button("🧹 Clear Cache", type="secondary", use_container_width=True):
                count = st.session_state.cache.clear()
                st.success(f"✓ Cleared {count} cache entries")
                st.rerun()
        
        with col_cache2:
            if st.button("🗑️ Cleanup Expired", type="secondary", use_container_width=True):
                count = st.session_state.cache.cleanup_expired()
                if count > 0:
                    st.success(f"✓ Removed {count} expired entries")
                else:
                    st.info("No expired entries found")
                st.rerun()
        
        # Knowledge Base Section
        st.header("📚 Locations")
        
        tab1, tab2 = st.tabs(["View/Edit", "Rules"])
        
        with tab1:
            st.subheader("Locations")
            
            config = st.session_state.config
            
            # Display existing locations
            for i, (name, location) in enumerate(config.locations.items()):
                with st.expander(f"📍 {name}", expanded=False):
                    new_name = st.text_input("Name", value=location.name, key=f"loc_name_{i}")
                    new_address = st.text_area("Address", value=location.address, key=f"loc_addr_{i}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        is_weekday_default = st.checkbox(
                            "Weekday Default",
                            value=location.is_default_weekday,
                            key=f"loc_wd_{i}"
                        )
                    with col2:
                        is_weekend_default = st.checkbox(
                            "Weekend Default",
                            value=location.is_default_weekend,
                            key=f"loc_we_{i}"
                        )
                    
                    if st.button("Update", key=f"update_{i}"):
                        updated_location = Location(
                            name=new_name,
                            address=new_address,
                            is_default_weekday=is_weekday_default,
                            is_default_weekend=is_weekend_default
                        )
                        # Remove old if name changed
                        if new_name != name:
                            del config.locations[name]
                        config.add_location(updated_location)
                        st.session_state.config_manager.save()
                        st.success(f"Updated {new_name}")
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_{i}", type="secondary"):
                        del config.locations[name]
                        st.session_state.config_manager.save()
                        st.success(f"Deleted {name}")
                        st.rerun()
            
            # Add new location
            st.markdown("---")
            st.subheader("Add New Location")
            with st.form("add_location"):
                new_loc_name = st.text_input("Name")
                new_loc_address = st.text_area("Address")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_wd = st.checkbox("Weekday Default")
                with col2:
                    new_we = st.checkbox("Weekend Default")
                
                if st.form_submit_button("Add Location"):
                    if new_loc_name and new_loc_address:
                        new_location = Location(
                            name=new_loc_name,
                            address=new_loc_address,
                            is_default_weekday=new_wd,
                            is_default_weekend=new_we
                        )
                        config.add_location(new_location)
                        st.session_state.config_manager.save()
                        st.success(f"Added {new_loc_name}")
                        st.rerun()
        
        with tab2:
            st.markdown("""
            **Rules:**
            1. Explicit location → use it
            2. Weekdays → {0}
            3. Weekends → {1}
            """.format(
                config.default_weekday_location or 'None',
                config.default_weekend_location or 'None'
            ))


def render_main():
    """Render main content area - 3 column layout"""
    st.markdown("### 🏊 Swimming Schedule Converter")
    
    # Export section at the top - clean layout
    if st.session_state.events:
        col_exp1, col_exp2 = st.columns([4, 1])
        
        with col_exp1:
            export_format = st.selectbox(
                "📥 Export Format",
                [CalendarFormat.ICS, CalendarFormat.GOOGLE, CalendarFormat.OUTLOOK],
                format_func=lambda x: {
                    CalendarFormat.ICS: "iCalendar (.ics) - iOS/Mac/Generic",
                    CalendarFormat.GOOGLE: "Google Calendar (.csv)",
                    CalendarFormat.OUTLOOK: "Outlook (.csv)"
                }[x],
                label_visibility="visible"
            )
        
        with col_exp2:
            st.markdown("&nbsp;")  # Spacer for alignment
            if st.button("Export", type="primary", use_container_width=True):
                export_calendar(export_format)
        
        st.divider()
    
    # 3-Column Layout: Input | Review | Edit
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    # Column 1: Input
    with col1:
        st.markdown("#### 📝 Input")
        schedule_text = st.text_area(
            "Raw Schedule",
            height=400,
            placeholder="""周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午 5-7 下水
周六 1/31 上午 9-11 @ Brandeis""",
            label_visibility="collapsed"
        )
        
        if st.button("🤖 Process", type="primary", disabled=not schedule_text or not st.session_state.api_key, use_container_width=True):
            process_schedule(schedule_text)
        
        if st.button("🔄 Clear", type="secondary", use_container_width=True):
            st.session_state.events = []
            st.session_state.validated_events = []
            st.rerun()
    
    # Column 2: Review (Table View)
    with col2:
        st.markdown("#### 📊 Review")
        
        if st.session_state.events:
            # Add a checkbox to select events for deletion
            if 'events_to_delete' not in st.session_state:
                st.session_state.events_to_delete = []
            
            # Create table view with checkboxes
            events_data = []
            for i, event in enumerate(st.session_state.events):
                events_data.append({
                    "Select": False,  # Placeholder, will be checkbox
                    "#": i + 1,
                    "Date": event.start_time.strftime("%m/%d"),
                    "Time": f"{event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}",
                    "Location": event.location.name if event.location else "?",
                    "Notes": event.notes[:30] + "..." if event.notes and len(event.notes) > 30 else (event.notes or "")
                })
            
            # Display events with selection checkboxes
            st.markdown(f"**{len(st.session_state.events)} event(s) found**")
            
            # Select all / Clear selection buttons
            col_sel1, col_sel2, col_sel3 = st.columns(3)
            with col_sel1:
                if st.button("Select All", key="select_all", use_container_width=True):
                    st.session_state.events_to_delete = list(range(len(st.session_state.events)))
                    st.rerun()
            with col_sel2:
                if st.button("Clear", key="clear_selection", use_container_width=True):
                    st.session_state.events_to_delete = []
                    st.rerun()
            with col_sel3:
                if st.button("🗑️ Delete Selected", key="bulk_delete", type="secondary", use_container_width=True, disabled=len(st.session_state.events_to_delete) == 0):
                    # Delete selected events (reverse order to avoid index issues)
                    for idx in sorted(st.session_state.events_to_delete, reverse=True):
                        st.session_state.events.pop(idx)
                    st.session_state.events_to_delete = []
                    st.success(f"✓ Deleted events!")
                    st.rerun()
            
            # Display events with checkboxes
            for i, event in enumerate(st.session_state.events):
                is_selected = i in st.session_state.events_to_delete
                
                col_check, col_info = st.columns([0.5, 4])
                with col_check:
                    if st.checkbox(f"Select event {i+1}", value=is_selected, key=f"check_{i}", label_visibility="collapsed"):
                        if i not in st.session_state.events_to_delete:
                            st.session_state.events_to_delete.append(i)
                    else:
                        if i in st.session_state.events_to_delete:
                            st.session_state.events_to_delete.remove(i)
                
                with col_info:
                    st.markdown(f"**#{i+1}** {event.start_time.strftime('%m/%d %H:%M')}-{event.end_time.strftime('%H:%M')} @ {event.location.name if event.location else '?'}")
                    if event.notes:
                        st.caption(event.notes)
        else:
            st.info("No events to display. Paste schedule and click Process.")
    
    # Column 3: Edit
    with col3:
        st.markdown("#### ✏️ Edit")
        
        if st.session_state.events:
            event_to_edit = st.selectbox(
                "Select Event",
                range(len(st.session_state.events)),
                format_func=lambda i: f"#{i+1} - {st.session_state.events[i].start_time.strftime('%m/%d %H:%M')}",
                label_visibility="collapsed",
                key="event_selector"
            )
            
            if event_to_edit is not None:
                event = st.session_state.events[event_to_edit]
                
                st.markdown(f"**Event #{event_to_edit + 1}**")
                
                # Use unique timestamp-based key to avoid conflicts
                base_key = f"edit_{event_to_edit}_{hash(str(event.start_time))}"
                
                # Edit fields
                new_summary = st.text_input("Title", value=event.summary, key=f"{base_key}_summary")
                
                col_date, col_time = st.columns(2)
                with col_date:
                    new_date = st.date_input("Date", value=event.start_time.date(), key=f"{base_key}_date")
                
                with col_time:
                    new_start = st.time_input("Start", value=event.start_time.time(), key=f"{base_key}_start")
                    new_end = st.time_input("End", value=event.end_time.time(), key=f"{base_key}_end")
                
                # Location dropdown
                location_names = list(st.session_state.config.locations.keys())
                current_loc = event.location.name if event.location else location_names[0]
                new_location_name = st.selectbox(
                    "Location",
                    location_names,
                    index=location_names.index(current_loc) if current_loc in location_names else 0,
                    key=f"{base_key}_loc"
                )
                
                # Notes
                if event.notes:
                    with st.expander("📝 Notes"):
                        st.text(event.notes)
                
                # Update button
                if st.button("💾 Update", key=f"{base_key}_update", use_container_width=True):
                    from datetime import datetime
                    st.session_state.events[event_to_edit] = Event(
                        start_time=datetime.combine(new_date, new_start),
                        end_time=datetime.combine(new_date, new_end),
                        summary=new_summary,
                        location=st.session_state.config.locations[new_location_name],
                        location_name=new_location_name,
                        is_ambiguous=event.is_ambiguous,
                        raw_text=event.raw_text,
                        notes=event.notes
                    )
                    st.success("✓ Updated!")
                    st.rerun()
                
                # Delete button
                if st.button("🗑️ Delete", key=f"{base_key}_delete", type="secondary", use_container_width=True):
                    st.session_state.events.pop(event_to_edit)
                    st.success("✓ Deleted!")
                    st.rerun()
        else:
            st.info("No events to edit.")


def process_schedule(schedule_text):
    """Process schedule text with AI"""
    try:
        with st.spinner("🤖 Extracting events from text..."):
            extractor = EventExtractor(
                api_key=st.session_state.api_key,
                config=st.session_state.config
            )
            events = extractor.extract(schedule_text)
            
            # Track cache hit/miss
            st.session_state.last_cache_hit = extractor.last_cache_hit
        
        if not events:
            st.warning("No events could be extracted from the text")
            return
        
        # Show cache hit message
        if st.session_state.last_cache_hit:
            st.success(f"⚡ Cache hit! Instantly retrieved {len(events)} event(s)")
        else:
            st.success(f"✓ Extracted {len(events)} event(s) from AI")
        
        with st.spinner("📍 Applying rules..."):
            rules_engine = RulesEngine(st.session_state.config)
            events = rules_engine.apply_location_rules(events)
            events = rules_engine.merge_overlapping_events(events)  # Merge overlapping events
            events = rules_engine.deduplicate_events(events)
            events = rules_engine.sort_events(events)
        
        st.session_state.events = events
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())


def export_calendar(format: CalendarFormat):
    """Export calendar in selected format"""
    try:
        exporter = CalendarExporter(st.session_state.config)
        
        content = exporter.export(st.session_state.events, format)
        
        extension = exporter.get_file_extension(format)
        mime_type = exporter.get_mime_type(format)
        
        filename = f"swimming_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        # Encode content to bytes with UTF-8-BOM for ICS (iOS compatibility)
        # CSV formats use UTF-8 without BOM
        if format == CalendarFormat.ICS:
            data = content.encode('utf-8-sig')
        else:
            data = content.encode('utf-8')
        
        st.download_button(
            label=f"📥 Download {filename}",
            data=data,
            file_name=filename,
            mime=mime_type,
            type="primary"
        )

        if format == CalendarFormat.ICS:
            zip_filename = f"swimming_schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            zip_data = exporter.export_to_ics_zip(st.session_state.events, ics_filename=filename)
            st.download_button(
                label="📦 Download ZIP (iOS Files)",
                data=zip_data,
                file_name=zip_filename,
                mime="application/zip",
                type="secondary"
            )
        
        st.success("✅ Calendar file generated successfully!")
        
        # Show import instructions
        with st.expander("📱 Import Instructions"):
            if format == CalendarFormat.ICS:
                st.markdown("""
                **iOS/Mac:**
                1. Download the .ics file
                2. Open the file to import into Calendar
                
                **Any Calendar App:**
                - Most calendar apps support .ics import
                """)
            elif format == CalendarFormat.GOOGLE:
                st.markdown("""
                **Google Calendar:**
                1. Open Google Calendar on desktop
                2. Click ⚙️ Settings → Import & Export
                3. Select the .csv file
                4. Choose destination calendar
                """)
            elif format == CalendarFormat.OUTLOOK:
                st.markdown("""
                **Outlook:**
                1. Open Outlook
                2. File → Import/Export
                3. Select "Import from another program or file"
                4. Choose "Comma Separated Values"
                5. Select the .csv file
                """)
        
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")


# Main app
def main():
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
