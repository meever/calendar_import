"""
Manages publicly shared calendars

Allows users to save extracted calendars with names/descriptions and
browse/export them without needing the original text.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from models import SharedCalendar, Event, Config


class SharedCalendarManager:
    """Manages storage and retrieval of shared calendars"""
    
    def __init__(self, storage_dir: str = "shared_calendars"):
        """
        Initialize shared calendar manager
        
        Args:
            storage_dir: Directory to store shared calendar files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save(self, name: str, description: str, events: List[Event]) -> SharedCalendar:
        """
        Save a new shared calendar
        
        Args:
            name: User-provided name for the calendar
            description: User-provided description
            events: List of events to share
            
        Returns:
            SharedCalendar object with generated ID
        """
        # Generate unique ID
        calendar_id = str(uuid.uuid4())[:8]
        
        shared_calendar = SharedCalendar(
            id=calendar_id,
            name=name,
            description=description,
            events=events,
            created_at=datetime.now()
        )
        
        # Save to file
        file_path = self.storage_dir / f"{calendar_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(shared_calendar.to_dict(), f, indent=2, ensure_ascii=False)
        
        return shared_calendar
    
    def list_all(self) -> List[SharedCalendar]:
        """
        List all shared calendars
        
        Returns:
            List of SharedCalendar objects, sorted by created_at (newest first)
        """
        calendars = []
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # We'll need locations to reconstruct Event objects
                # For now, use empty dict - events will have location_name stored
                calendar = SharedCalendar.from_dict(data, {})
                calendars.append(calendar)
                
            except Exception as e:
                print(f"Warning: Failed to load shared calendar {file_path.name}: {e}")
                continue
        
        # Sort by created_at, newest first
        calendars.sort(key=lambda c: c.created_at, reverse=True)
        return calendars
    
    def get_by_id(self, calendar_id: str, locations: Dict[str, 'Location']) -> Optional[SharedCalendar]:
        """
        Get a specific shared calendar by ID
        
        Args:
            calendar_id: Unique calendar identifier
            locations: Location mapping for reconstructing events
            
        Returns:
            SharedCalendar object if found, None otherwise
        """
        file_path = self.storage_dir / f"{calendar_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return SharedCalendar.from_dict(data, locations)
        
        except Exception as e:
            print(f"Warning: Failed to load shared calendar {calendar_id}: {e}")
            return None
    
    def delete(self, calendar_id: str) -> bool:
        """
        Delete a shared calendar
        
        Args:
            calendar_id: Unique calendar identifier
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.storage_dir / f"{calendar_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """
        Get shared calendar statistics
        
        Returns:
            Dict with stats about shared calendars
        """
        calendar_files = list(self.storage_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in calendar_files)
        
        return {
            "total_calendars": len(calendar_files),
            "total_size_kb": total_size / 1024
        }
