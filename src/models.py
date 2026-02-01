"""
Data models for the swimming schedule converter
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


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
            raw_text=data.get("raw_text")
        )


@dataclass
class Config:
    """Application configuration"""
    locations: Dict[str, Location] = field(default_factory=dict)
    timezone: str = "America/New_York"
    default_weekday_location: Optional[str] = "Regis"
    default_weekend_location: Optional[str] = "Brandeis"
    default_event_title: str = "Tyler Swim Practice"  # Default title for events
    api_key: Optional[str] = None
    gemini_model: str = "gemini-flash-latest"  # Auto-updates to newest flash model
    host: str = "0.0.0.0"  # Accessible from local network (192.168.x.x)
    port: int = 8501
    gemini_model: str = "gemini-flash-latest"  # Auto-updates to newest flash model
    host: str = "127.0.0.1"  # localhost only - not accessible from network
    port: int = 8501
    
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
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "locations": {
                name: {
                    "name": loc.name,
                    "address": loc.address,
                    "is_default_weekday": loc.is_default_weekday,
                    "is_default_weekend": loc.is_default_weekend
                }
                for name, loc in self.locations.items()
            },
            "timezone": self.timezone,
            "default_weekday_location": self.default_weekday_location,
            "default_weekend_location": self.default_weekend_location,
            "gemini_model": self.gemini_model,
            "host": self.host,
            "port": self.port
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Config':
        """Create Config from dictionary"""
        config = cls(
            timezone=data.get("timezone", "America/New_York"),
            default_weekday_location=data.get("default_weekday_location", "Regis"),
            default_weekend_location=data.get("default_weekend_location", "Brandeis"),
            gemini_model=data.get("gemini_model", "gemini-flash-latest"),
            host=data.get("host", "127.0.0.1"),
            port=data.get("port", 8501)
        )
        
        # Load locations
        for name, loc_data in data.get("locations", {}).items():
            location = Location(
                name=loc_data["name"],
                address=loc_data["address"],
                is_default_weekday=loc_data.get("is_default_weekday", False),
                is_default_weekend=loc_data.get("is_default_weekend", False)
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
            is_default_weekday=True
        ))
        
        config.add_location(Location(
            name="Brandeis",
            address="Gosman Sports and Convocation Center, 415 South St, Waltham, MA",
            is_default_weekend=True
        ))
        
        config.add_location(Location(
            name="Wightman",
            address="Wightman Tennis Center, 100 Brown St, Weston, MA"
        ))
        
        return config
