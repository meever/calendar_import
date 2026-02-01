"""
AI-powered event extraction from unstructured text
"""

import json
from typing import List, Dict
from google import genai
from google.genai import types
from datetime import datetime
from models import Event, Config
from cache_manager import ExtractionCache


class EventExtractor:
    """Extracts structured events from unstructured text using Gemini AI"""
    
    def __init__(self, api_key: str, config: Config, use_cache: bool = True):
        """
        Initialize the extractor
        
        Args:
            api_key: Gemini API key
            config: Application configuration
            use_cache: Whether to use caching (default True)
        """
        self.api_key = api_key
        self.config = config
        self.client = genai.Client(api_key=self.api_key)
        self.model = config.gemini_model  # Use model from config
        self.use_cache = use_cache
        self.cache = ExtractionCache() if use_cache else None
        self.last_cache_hit = False  # Track if last extraction was from cache
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with location context"""
        location_info = "\n".join([
            f"- {loc.name}: {loc.address}"
            for loc in self.config.locations.values()
        ])
        
        return f"""You are an expert at extracting structured swimming practice schedules from unstructured text.

LOCATIONS (use these exact names):
{location_info}

CRITICAL RULES:

1. **COMBINING SESSIONS (MOST IMPORTANT)**:
   - If a line mentions BOTH underwater training (下水) AND dryland training (陆上/陆上拉伸), create ONE SINGLE EVENT
   - NEVER split these into separate events!
   
   **Case A - Separate times specified**:
   - If times are clearly separated (e.g., "6~7:30pm 下水、7:30~8pm 陆上拉伸")
   - Use the full range: start at underwater start, end at dryland end
   - Example: "6~7:30pm 下水、7:30~8pm 陆上拉伸" → 6:00 PM to 8:00 PM
   
   **Case B - Combined time without separate dryland time**:
   - If ONLY one time range is given for combined session (e.g., "5~6:30 下水+陆上拉伸")
   - Automatically ADD 30 MINUTES to the end time for dryland training
   - Example: "5~6:30 下水+陆上拉伸" → 5:00 PM to 7:00 PM (6:30 + 30 min)
   - Example: "下午 6 - 8 下水+陆上" → 6:00 PM to 8:30 PM (8:00 + 30 min)
   
   **How to tell the difference**:
   - Separate times: Look for comma (、), multiple time ranges, or explicit "X~Y下水...Y~Z陆上" patterns
   - Combined time: Single time range with "下水+陆上" or "下水陆上" together

2. **REST DAYS**:
   - If text says "休息" (rest) or "闭馆" (closed), do NOT create an event
   - Skip rest days entirely

3. **LOCATION DETECTION**:
   - If the text EXPLICITLY mentions a location (e.g., "@ Regis", "@ Wightman", "@ Brandeis"), use that location name
   - If NO location is mentioned, leave location_name as null
   - Be precise - only use location if explicitly stated

4. **AMBIGUITY**:
   - Set is_ambiguous to true if you're uncertain about ANY field
   - Flag events where dates/times are unclear

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanations) with this structure:
{{
  "events": [
    {{
      "start_time": "2026-01-29T18:00:00",
      "end_time": "2026-01-29T20:00:00",
      "summary": "{self.config.default_event_title}",
      "location_name": "Regis",
      "is_ambiguous": false,
      "original_text": "周四 1/29 下午 6 - 8 下水+陆上 @ Regis"
    }}
  ]
}}

**IMPORTANT**: Include "original_text" field with the EXACT original text snippet from the input that corresponds to this event. 
- Use the exact characters from input (don't rephrase)
- If multiple input lines create one event, include all lines separated by " | "
- If event is inferred and has no direct text, set to null

EXAMPLES OF CORRECT EXTRACTION:
Input: "2/2 周一 6~7:30pm 下水、7:30~8pm 陆上拉伸"
Output: Single event 2026-02-02T18:00:00 to 2026-02-02T20:00:00, original_text: "2/2 周一 6~7:30pm 下水、7:30~8pm 陆上拉伸" (NOT two events!)

Input: "2/6 周五 休息 ♨️ 场馆闭馆"
Output: NO EVENT (rest day)

Input: "1/31 周六 6-7:30pm 下水 + 7:30~8pm 陆上拉伸 @ Brandeis"
Output: Single event 2026-01-31T18:00:00 to 2026-01-31T20:00:00, location "Brandeis"

IMPORTANT:
- Use ISO 8601 format for dates/times (YYYY-MM-DDTHH:MM:SS)
- Assume year is 2026 if not specified
- Extract all events except rest days
- Be precise with times and dates
"""
    
    def extract(self, raw_text: str) -> List[Event]:
        """
        Extract events from raw text
        
        Args:
            raw_text: Unstructured schedule text
            
        Returns:
            List of Event objects
            
        Raises:
            ValueError: If input is not a calendar or no events extracted
            Exception: If API call fails or response cannot be parsed
        """
        # Input validation
        if not raw_text or len(raw_text.strip()) < 10:
            raise ValueError("Input text is too short or empty")
        
        # Check cache first
        if self.use_cache and self.cache:
            cached_events = self.cache.get(raw_text, self.config)
            if cached_events is not None:
                self.last_cache_hit = True
                print(f"✓ Cache hit! Retrieved {len(cached_events)} events from cache")
                return cached_events
            else:
                self.last_cache_hit = False
        
        # Cache miss - call AI
        prompt = f"{self._build_system_prompt()}\n\nEXTRACT EVENTS FROM THIS TEXT:\n{raw_text}"
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            response_text = response.text.strip()
            
            # Clean markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"AI returned invalid JSON: {e}")
            
            # Handle both list and dict responses
            if isinstance(data, list):
                events_data = data
            elif isinstance(data, dict) and "events" in data:
                events_data = data["events"]
            else:
                raise ValueError("AI response must be a list or dict with 'events' field")
            
            # Check if any events were found
            if not events_data or len(events_data) == 0:
                raise ValueError(
                    "No calendar events found in the input text. "
                    "Please ensure your input contains schedule information with dates and times. "
                    "Supported formats: dates (1/29, 周四), times (6-8pm, 下午6-8), locations (@Regis)."
                )
            
            # Convert to Event objects
            events = []
            for event_data in events_data:
                try:
                    # Validate required fields
                    if "start_time" not in event_data or "end_time" not in event_data:
                        continue
                    
                    # Get original text snippet from AI response, or mark as inferred
                    original_snippet = event_data.get("original_text")
                    if not original_snippet:
                        original_snippet = "(Inferred from schedule)"
                    
                    event = Event(
                        start_time=datetime.fromisoformat(event_data["start_time"]),
                        end_time=datetime.fromisoformat(event_data["end_time"]),
                        summary=event_data.get("summary", self.config.default_event_title),
                        location_name=event_data.get("location_name"),
                        is_ambiguous=event_data.get("is_ambiguous", False),
                        raw_text=original_snippet
                    )
                    
                    # Validate event times
                    if event.start_time >= event.end_time:
                        continue  # Skip invalid time ranges
                    
                    # Map location name to Location object if available
                    if event.location_name:
                        event.location = self.config.locations.get(event.location_name)
                    
                    events.append(event)
                except Exception as e:
                    print(f"Warning: Failed to parse event: {e}")
                    continue
            
            # Final validation - ensure we got valid events
            if not events or len(events) == 0:
                raise ValueError(
                    "Could not extract any valid calendar events from the input. "
                    "Please check that your text contains schedule information."
                )
            
            # Store in cache for future use
            if self.use_cache and self.cache:
                self.cache.set(raw_text, self.config, events)
                print(f"✓ Cached {len(events)} events for future use")
            
            return events
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"AI response was not valid JSON - input may not be a calendar. "
                f"Please provide schedule text with dates and times."
            )
        except ValueError:
            # Re-raise ValueError with our custom messages
            raise
        except Exception as e:
            raise Exception(f"Failed to extract events: {e}")
