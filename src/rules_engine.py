"""
Business rules engine for event processing
"""

from typing import List, Dict
from datetime import timedelta
from models import Event, Config, DayType


class RulesEngine:
    """Applies business rules to events"""
    
    def __init__(self, config: Config):
        """
        Initialize rules engine
        
        Args:
            config: Application configuration
        """
        self.config = config
    
    def apply_location_rules(self, events: List[Event]) -> List[Event]:
        """
        Apply location detection rules to events
        
        Rule 1: If location is explicitly set, keep it
        Rule 2: For weekdays without location, use default weekday location
        Rule 3: For weekends without location, use default weekend location
        
        Args:
            events: List of events to process
            
        Returns:
            Events with locations assigned
        """
        for event in events:
            # Skip if location already set
            if event.location is not None:
                continue
            
            # Apply default location based on day type
            default_location = self.config.get_default_location(event.day_type)
            if default_location:
                event.location = default_location
                if not event.location_name:
                    event.location_name = default_location.name
        
        return events
    
    def validate_events(self, events: List[Event]) -> List[Dict]:
        """
        Validate events and return validation results
        
        Args:
            events: List of events to validate
            
        Returns:
            List of validation issues (empty if all valid)
        """
        issues = []
        
        for i, event in enumerate(events):
            # Check if location is missing
            if event.location is None:
                issues.append({
                    "event_index": i,
                    "event_summary": event.summary,
                    "issue": "Missing location",
                    "severity": "warning"
                })
            
            # Check if times are valid
            if event.start_time >= event.end_time:
                issues.append({
                    "event_index": i,
                    "event_summary": event.summary,
                    "issue": "Start time is after or equal to end time",
                    "severity": "error"
                })
            
            # Check if event is in the past
            from datetime import datetime, timezone
            if event.start_time.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                issues.append({
                    "event_index": i,
                    "event_summary": event.summary,
                    "issue": "Event is in the past",
                    "severity": "info"
                })
            
            # Check if marked as ambiguous
            if event.is_ambiguous:
                issues.append({
                    "event_index": i,
                    "event_summary": event.summary,
                    "issue": "Event flagged as ambiguous by AI",
                    "severity": "warning"
                })
        
        return issues
    
    def merge_overlapping_events(self, events: List[Event]) -> List[Event]:
        """
        Merge overlapping events on the same day at the same location
        
        Example: Two groups (5-6pm and 5-7pm) on same day → Single event 5-7pm with notes
        
        Args:
            events: List of events to process
            
        Returns:
            Events with overlaps merged
        """
        if not events:
            return events
        
        # Sort by date and location
        sorted_events = sorted(events, key=lambda e: (e.start_time.date(), 
                                                        e.location.name if e.location else "",
                                                        e.start_time))
        
        merged = []
        i = 0
        
        while i < len(sorted_events):
            current = sorted_events[i]
            overlapping = [current]
            
            # Find all events on same day at same location that overlap
            j = i + 1
            while j < len(sorted_events):
                next_event = sorted_events[j]
                
                # Check if same day and location
                same_day = current.start_time.date() == next_event.start_time.date()
                same_location = (
                    (current.location and next_event.location and 
                     current.location.name == next_event.location.name) or
                    (not current.location and not next_event.location)
                )
                
                if same_day and same_location:
                    # Check if times overlap or are adjacent
                    overlaps = (
                        next_event.start_time < current.end_time or
                        next_event.start_time == current.end_time  # Adjacent
                    )
                    
                    if overlaps:
                        overlapping.append(next_event)
                        j += 1
                    else:
                        break
                else:
                    break
            
            # If multiple overlapping events, merge them
            if len(overlapping) > 1:
                # Use earliest start and latest end
                merged_start = min(e.start_time for e in overlapping)
                merged_end = max(e.end_time for e in overlapping)
                
                # Concatenate all original text snippets
                merged_snippets = []
                for e in overlapping:
                    if e.raw_text and e.raw_text != "(Inferred from schedule)":
                        merged_snippets.append(e.raw_text.strip())
                
                # Join with separator if multiple snippets found
                merged_raw_text = " | ".join(merged_snippets) if merged_snippets else "(Inferred from schedule)"
                
                # Create notes about merged groups
                notes_parts = []
                for e in overlapping:
                    time_range = f"{e.start_time.strftime('%H:%M')}-{e.end_time.strftime('%H:%M')}"
                    if e.raw_text and len(e.raw_text) < 100:
                        notes_parts.append(f"• {time_range}: {e.raw_text.strip()}")
                    else:
                        notes_parts.append(f"• Group: {time_range}")
                
                notes = f"Combined {len(overlapping)} groups:\n" + "\n".join(notes_parts)
                
                # Create merged event
                merged_event = Event(
                    start_time=merged_start,
                    end_time=merged_end,
                    summary=current.summary,
                    location=current.location,
                    location_name=current.location_name,
                    is_ambiguous=any(e.is_ambiguous for e in overlapping),
                    raw_text=merged_raw_text,
                    notes=notes
                )
                merged.append(merged_event)
                i = j  # Skip all merged events
            else:
                # No overlap, keep as is
                merged.append(current)
                i += 1
        
        return merged
    
    def deduplicate_events(self, events: List[Event]) -> List[Event]:
        """
        Remove duplicate events based on time and summary
        
        Args:
            events: List of events
            
        Returns:
            Deduplicated events
        """
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a signature for the event
            signature = (
                event.start_time,
                event.end_time,
                event.summary.lower().strip()
            )
            
            if signature not in seen:
                seen.add(signature)
                unique_events.append(event)
        
        return unique_events
    
    def sort_events(self, events: List[Event]) -> List[Event]:
        """Sort events by start time"""
        return sorted(events, key=lambda e: e.start_time)
