"""
Calendar export functionality (ICS / ZIP)
"""

from typing import List
from datetime import datetime, timezone
from pathlib import Path
import io
import zipfile
from ics import Calendar, Event as IcsEvent
from zoneinfo import ZoneInfo
from models import Event, Config
from settings import CALENDAR_NAME_PREFIX, ICS_DEFAULT_FILENAME, ICS_METHOD


class CalendarExporter:
    """Exports events to various calendar formats"""
    
    def __init__(self, config: Config):
        """
        Initialize exporter
        
        Args:
            config: Application configuration
        """
        self.config = config
    
    def export_to_ics(self, events: List[Event], output_path: str = None) -> str:
        """
        Export events to ICS format
        
        Args:
            events: List of events to export
            output_path: Optional file path to save (if None, returns string)
            
        Returns:
            ICS file content as string (UTF-8 BOM added during encoding)
        """
        calendar = Calendar()
        tz = ZoneInfo(self.config.timezone)
        
        for event in events:
            ics_event = IcsEvent()
            
            # Set creation timestamp (generates DTSTAMP in UTC - RFC 5545 requirement)
            ics_event.created = datetime.now(timezone.utc)
            
            # Set times with timezone
            ics_event.begin = event.start_time.replace(tzinfo=tz)
            ics_event.end = event.end_time.replace(tzinfo=tz)
            
            # Set summary
            ics_event.name = event.summary
            
            # Set location
            if event.location:
                ics_event.location = event.location.address
            
            # Build description with original text and notes
            description_parts = []
            if event.raw_text:
                description_parts.append(f"Original: {event.raw_text}")
            if event.notes:
                description_parts.append(f"\n{event.notes}")
            if description_parts:
                ics_event.description = "".join(description_parts)
            
            calendar.events.add(ics_event)
        
        # Serialize calendar (avoid FutureWarning)
        ics_content = calendar.serialize()
        
        # Normalize to LF first (ics library may return mixed endings)
        ics_content = ics_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Add iOS-friendly calendar headers (name, method, timezone)
        timestamp = datetime.now().strftime("%Y-%m-%d")
        calendar_name = f"{CALENDAR_NAME_PREFIX} {timestamp}"
        timezone_id = self.config.timezone
        ics_lines = ics_content.split('\n')

        # Remove any existing duplicates before inserting stable headers
        filtered_lines = []
        skip_prefixes = (
            'X-WR-CALNAME:',
            'NAME:',
            'METHOD:',
            'X-WR-TIMEZONE:'
        )
        for line in ics_lines:
            if line.startswith(skip_prefixes):
                continue
            filtered_lines.append(line)

        ics_lines = filtered_lines

        # Insert headers after PRODID or VERSION if present, else after BEGIN:VCALENDAR
        insert_at = None
        for i, line in enumerate(ics_lines):
            if line.startswith('PRODID:'):
                insert_at = i + 1
                break
        if insert_at is None:
            for i, line in enumerate(ics_lines):
                if line.startswith('VERSION:'):
                    insert_at = i + 1
                    break
        if insert_at is None:
            for i, line in enumerate(ics_lines):
                if line.startswith('BEGIN:VCALENDAR'):
                    insert_at = i + 1
                    break

        if insert_at is None:
            insert_at = 0

        headers_to_insert = [
            f'METHOD:{ICS_METHOD}',
            f'X-WR-CALNAME:{calendar_name}',
            f'NAME:{calendar_name}',
            f'X-WR-TIMEZONE:{timezone_id}'
        ]
        for offset, header in enumerate(headers_to_insert):
            ics_lines.insert(insert_at + offset, header)
        
        # Use CRLF line endings (RFC 5545 standard - required for iOS compatibility)
        ics_content = '\r\n'.join(ics_lines)
        
        # Ensure ends with CRLF
        if not ics_content.endswith('\r\n'):
            ics_content += '\r\n'
        
        # Note: UTF-8 BOM will be added by utf-8-sig encoding below
        
        # Save to file if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(ics_content)
        
        return ics_content
    
    def export_to_ics_zip(self, events: List[Event], ics_filename: str = None) -> bytes:
        """
        Export events to a ZIP containing a single ICS file.

        Args:
            events: List of events to export
            ics_filename: Optional ICS filename inside the ZIP

        Returns:
            ZIP file bytes
        """
        if not ics_filename:
            ics_filename = ICS_DEFAULT_FILENAME

        ics_content = self.export_to_ics(events)
        ics_bytes = ics_content.encode("utf-8-sig")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(ics_filename, ics_bytes)

        return buffer.getvalue()
