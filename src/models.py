"""
Data models for the swimming schedule converter
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from settings import (
    DEFAULT_EVENT_TITLE,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TIMEZONE,
    DEFAULT_WEEKDAY_LOCATION,
    DEFAULT_WEEKEND_LOCATION,
)


class DayType(Enum):
    """Day type classification"""
    WEEKDAY = "weekday"
    WEEKEND = "weekend"


class CalendarFormat(Enum):
    """Supported calendar export formats"""
    ICS = "ics"
    GOOGLE = "google_calendar"
    OUTLOOK = "outlook"


@dataclass
class Location:
    """Represents a physical location"""
    name: str
    address: str
    is_default_weekday: bool = False
    is_default_weekend: bool = False
    aliases: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.name}: {self.address}"


@dataclass
class Event:
    """Represents a calendar event"""
    start_time: datetime
    end_time: datetime
    summary: str
    location: Optional[Location] = None
    location_name: Optional[str] = None  # Raw location name before mapping
    is_ambiguous: bool = False
    raw_text: Optional[str] = None  # Original text that generated this event
    notes: Optional[str] = None  # Additional notes (e.g., merged groups)
    
    @property
    def day_type(self) -> DayType:
        """Determine if this is a weekday or weekend event"""
        if self.start_time.weekday() < 5:  # Monday=0, Friday=4
            return DayType.WEEKDAY
        return DayType.WEEKEND
    
    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "summary": self.summary,
            "location_name": self.location_name or (self.location.name if self.location else None),
            "location_address": self.location.address if self.location else None,
            "is_ambiguous": self.is_ambiguous,
            "raw_text": self.raw_text,
            "notes": self.notes,
            "day_type": self.day_type.value,
            "duration_minutes": self.duration_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict, locations: Dict[str, Location]) -> 'Event':
        """Create Event from dictionary"""
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = datetime.fromisoformat(data["end_time"])
        location_name = data.get("location_name")
        
        return cls(
            start_time=start_time,
            end_time=end_time,
            summary=data["summary"],
            location=locations.get(location_name) if location_name else None,
            location_name=location_name,
            is_ambiguous=data.get("is_ambiguous", False),
            raw_text=data.get("raw_text"),
            notes=data.get("notes")
        )


@dataclass
class Config:
    """Application configuration"""
    locations: Dict[str, Location] = field(default_factory=dict)
    timezone: str = DEFAULT_TIMEZONE
    default_weekday_location: Optional[str] = DEFAULT_WEEKDAY_LOCATION
    default_weekend_location: Optional[str] = DEFAULT_WEEKEND_LOCATION
    default_event_title: str = DEFAULT_EVENT_TITLE  # Default title for events (AI provides this, fallback only)
    api_key: Optional[str] = None
    gemini_model: str = DEFAULT_GEMINI_MODEL  # Auto-updates to newest flash model
    host: str = DEFAULT_HOST  # localhost only - not accessible from network
    port: int = DEFAULT_PORT
    
    def get_default_location(self, day_type: DayType) -> Optional[Location]:
        """Get default location for a given day type"""
        if day_type == DayType.WEEKDAY and self.default_weekday_location:
            return self.locations.get(self.default_weekday_location)
        elif day_type == DayType.WEEKEND and self.default_weekend_location:
            return self.locations.get(self.default_weekend_location)
        return None
    
    def add_location(self, location: Location) -> None:
        """Add or update a location"""
        self.locations[location.name] = location
        
        # Update defaults if marked
        if location.is_default_weekday:
            self.default_weekday_location = location.name
        if location.is_default_weekend:
            self.default_weekend_location = location.name
    
    def resolve_location(self, name: str) -> Optional[Location]:
        """
        Resolve a location name or alias to a Location object.
        
        Lookup order:
        1. Exact match on canonical location name
        2. Case-insensitive match on canonical location name
        3. Case-insensitive match on any alias
        
        Args:
            name: Location name, abbreviation, or alias to resolve
            
        Returns:
            Matching Location or None if not found
        """
        if not name:
            return None
        
        # 1. Exact match on canonical name
        if name in self.locations:
            return self.locations[name]
        
        # 2. Case-insensitive match on canonical name
        name_lower = name.lower()
        for loc in self.locations.values():
            if loc.name.lower() == name_lower:
                return loc
        
        # 3. Case-insensitive match on aliases
        for loc in self.locations.values():
            for alias in loc.aliases:
                if alias.lower() == name_lower:
                    return loc
        
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "locations": {
                name: {
                    "name": loc.name,
                    "address": loc.address,
                    "is_default_weekday": loc.is_default_weekday,
                    "is_default_weekend": loc.is_default_weekend,
                    "aliases": loc.aliases
                }
                for name, loc in self.locations.items()
            },
            "timezone": self.timezone,
            "default_weekday_location": self.default_weekday_location,
            "default_weekend_location": self.default_weekend_location,
            "default_event_title": self.default_event_title,
            "gemini_model": self.gemini_model,
            "host": self.host,
            "port": self.port
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Config':
        """Create Config from dictionary"""
        config = cls(
            timezone=data.get("timezone", DEFAULT_TIMEZONE),
            default_weekday_location=data.get("default_weekday_location", DEFAULT_WEEKDAY_LOCATION),
            default_weekend_location=data.get("default_weekend_location", DEFAULT_WEEKEND_LOCATION),
            default_event_title=data.get("default_event_title", DEFAULT_EVENT_TITLE),
            gemini_model=data.get("gemini_model", DEFAULT_GEMINI_MODEL),
            host=data.get("host", DEFAULT_HOST),
            port=data.get("port", DEFAULT_PORT)
        )
        
        # Load locations
        for name, loc_data in data.get("locations", {}).items():
            location = Location(
                name=loc_data["name"],
                address=loc_data["address"],
                is_default_weekday=loc_data.get("is_default_weekday", False),
                is_default_weekend=loc_data.get("is_default_weekend", False),
                aliases=loc_data.get("aliases", [])
            )
            config.add_location(location)
        
        return config
    
    @classmethod
    def get_default_config(cls) -> 'Config':
        """Get default configuration with predefined locations"""
        config = cls()
        
        # Default locations
        config.add_location(Location(
            name="Regis",
            address="Regis College Athletic Facility, 235 Wellesley St, Weston, MA",
            is_default_weekday=True,
            aliases=["regis college"]
        ))
        
        config.add_location(Location(
            name="Brandeis",
            address="Gosman Sports and Convocation Center, 415 South St, Waltham, MA",
            is_default_weekend=True,
            aliases=["gosman"]
        ))
        
        config.add_location(Location(
            name="Wightman",
            address="Wightman Tennis Center, 100 Brown St, Weston, MA",
            aliases=["wightman tennis"]
        ))
        
        config.add_location(Location(
            name="MIT",
            address="MIT Zesiger Center, 120 Vassar St, Cambridge, MA 02139",
            aliases=["mit pool", "zesiger", "zesiger center"]
        ))
        
        return config


@dataclass
class SharedCalendar:
    """Represents a publicly shared calendar with name and description"""
    id: str  # Unique identifier
    name: str  # User-provided name
    description: str  # User-provided description
    events: List[Event]  # List of events in this calendar
    created_at: datetime  # When this was shared
    event_count: int = 0  # Number of events (denormalized for quick display)
    
    def __post_init__(self):
        """Calculate event count after initialization"""
        if self.event_count == 0:
            self.event_count = len(self.events)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "event_count": self.event_count,
            "events": [event.to_dict() for event in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: Dict, locations: Dict[str, Location]) -> 'SharedCalendar':
        """Create SharedCalendar from dictionary"""
        events = [Event.from_dict(e, locations) for e in data["events"]]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            events=events,
            created_at=datetime.fromisoformat(data["created_at"]),
            event_count=data.get("event_count", len(events))
        )
