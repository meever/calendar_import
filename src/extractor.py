"""
AI-powered event extraction from unstructured text
"""

import json
from typing import List
import time
import logging
from google import genai
from datetime import datetime
from models import Event, Config
from settings import (
    AI_INFERRED_FROM_SCHEDULE,
    AI_MAX_RETRY_ATTEMPTS,
    AI_MIN_INPUT_LENGTH,
    AI_RETRY_WAIT_MULTIPLIER_SECONDS,
    AI_TRANSIENT_ERROR_KEYWORDS,
    current_schedule_year,
)


class EventExtractor:
    """Extracts structured events from unstructured text using Gemini AI"""

    logger = logging.getLogger(__name__)
    
    def __init__(self, api_key: str, config: Config):
        """
        Initialize the extractor
        
        Args:
            api_key: Gemini API key
            config: Application configuration
        """
        self.api_key = api_key
        self.config = config
        self.client = genai.Client(api_key=self.api_key)
        self.model = config.gemini_model  # Use model from config
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with location context"""
        location_lines = []
        for loc in self.config.locations.values():
            alias_text = ""
            if loc.aliases:
                alias_text = f" (also known as: {', '.join(loc.aliases)})"
            location_lines.append(f"- {loc.name}{alias_text}: {loc.address}")
        location_info = "\n".join(location_lines)
        inferred_year = current_schedule_year()
        
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

   **Case B - Single time specified**:
   - If ONLY one time range is given (e.g., "6-8pm 下水+陆上")
   - Use EXACTLY the specified time range for the entire event
   - **DO NOT** add extra time for dryland if not explicitly stated
   - Example: "周四 1/29 下午 6-8 下水+陆上" → 18:00 to 20:00 (NOT 20:30)
   
   **How to tell the difference**:
   - Separate times: Look for comma (、), multiple time ranges, or explicit "X~Y下水...Y~Z陆上" patterns
   - Combined time: Single time range with "下水+陆上" or "下水陆上" together

2. **REST DAYS**:
   - If text says "休息" (rest) or "闭馆" (closed), do NOT create an event
   - Skip rest days entirely

3. **LOCATION DETECTION**:
   - If the text EXPLICITLY mentions a location (e.g., "@ Regis", "@ Wightman", "@ Brandeis", "@ MIT"), use that location's canonical name from the list above
   - If a location alias or abbreviation is used (e.g., "@ mit", "@ zesiger"), use the canonical name it maps to
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
- Assume year is {inferred_year} if not specified
- Extract all events except rest days
- Be precise with times and dates
"""

    def _generate_with_retry(self, prompt: str, max_attempts: int = AI_MAX_RETRY_ATTEMPTS) -> str:
        """Generate model response with retry for transient API failures."""
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as error:
                last_error = error
                error_text = str(error)
                is_transient = (
                    AI_TRANSIENT_ERROR_KEYWORDS[0] in error_text
                    or AI_TRANSIENT_ERROR_KEYWORDS[1] in error_text
                    or AI_TRANSIENT_ERROR_KEYWORDS[2] in error_text
                    or AI_TRANSIENT_ERROR_KEYWORDS[3] in error_text.lower()
                    or AI_TRANSIENT_ERROR_KEYWORDS[4] in error_text.lower()
                )

                if attempt >= max_attempts or not is_transient:
                    raise

                wait_seconds = attempt * AI_RETRY_WAIT_MULTIPLIER_SECONDS
                self.logger.warning(
                    "Transient API error, retrying in %ss (attempt %s/%s)",
                    wait_seconds,
                    attempt,
                    max_attempts,
                )
                time.sleep(wait_seconds)

        if last_error:
            raise last_error

        raise RuntimeError("Failed to generate content")

    def _clean_response_text(self, response_text: str) -> str:
        """Strip markdown code block wrappers from model response."""
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _parse_events_from_response(self, response_text: str, fallback_summary: str) -> List[Event]:
        """Parse model response JSON into Event objects."""
        cleaned_text = self._clean_response_text(response_text)

        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as error:
            raise ValueError(f"AI returned invalid JSON: {error}")

        if isinstance(data, list):
            events_data = data
        elif isinstance(data, dict) and "events" in data:
            events_data = data["events"]
        else:
            raise ValueError("AI response must be a list or dict with 'events' field")

        parsed_events = []
        for event_data in events_data:
            try:
                if "start_time" not in event_data or "end_time" not in event_data:
                    continue

                original_snippet = event_data.get("original_text")
                if not original_snippet:
                    original_snippet = AI_INFERRED_FROM_SCHEDULE

                event = Event(
                    start_time=datetime.fromisoformat(event_data["start_time"]),
                    end_time=datetime.fromisoformat(event_data["end_time"]),
                    summary=event_data.get("summary", fallback_summary),
                    location_name=event_data.get("location_name"),
                    is_ambiguous=event_data.get("is_ambiguous", False),
                    raw_text=original_snippet,
                    notes=event_data.get("notes")
                )

                if event.start_time >= event.end_time:
                    continue

                if event.location_name:
                    resolved = self.config.resolve_location(event.location_name)
                    if resolved:
                        event.location = resolved
                        event.location_name = resolved.name
                    else:
                        self.logger.warning(
                            "Unknown location '%s' — will fall back to day-type default",
                            event.location_name,
                        )

                parsed_events.append(event)
            except Exception as error:
                self.logger.warning("Failed to parse event: %s", error)
                continue

        return parsed_events
    
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
        if not raw_text or len(raw_text.strip()) < AI_MIN_INPUT_LENGTH:
            raise ValueError("Input text is too short or empty")
        
        prompt = f"{self._build_system_prompt()}\n\nEXTRACT EVENTS FROM THIS TEXT:\n{raw_text}"
        
        try:
            response_text = self._generate_with_retry(prompt)

            parsed_events = self._parse_events_from_response(
                response_text=response_text,
                fallback_summary=self.config.default_event_title,
            )

            if not parsed_events:
                raise ValueError(
                    "No calendar events found in the input text. "
                    "Please ensure your input contains schedule information with dates and times. "
                    "Supported formats: dates (1/29, 周四), times (6-8pm, 下午6-8), locations (@Regis)."
                )

            return parsed_events
            
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

    def edit(self, events: List[Event], instructions: str) -> List[Event]:
        """
        Apply natural-language edits to existing events using Gemini.
        """
        events_text = []
        for index, event in enumerate(events, start=1):
            location_name = event.location.name if event.location else "Unknown"
            events_text.append(
                f"{index}. {event.start_time.strftime('%a %m/%d %H:%M')}-{event.end_time.strftime('%H:%M')} @ {location_name}"
            )

        current_schedule = "\n".join(events_text)
        locations_lines = []
        for name, location in self.config.locations.items():
            alias_text = ""
            if location.aliases:
                alias_text = f" (also known as: {', '.join(location.aliases)})"
            locations_lines.append(f"- {name}{alias_text}: {location.address}")
        locations_info = "\n".join(locations_lines)

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
            "summary": "{self.config.default_event_title}",
      "location_name": "Regis",
      "is_ambiguous": false
    }}
  ]
}}

Rules:
- Keep all events unless user asks to delete them
- Use ISO 8601 format for times
- Use exact location names from the list above
- If summary is not specified, use "{self.config.default_event_title}"
"""

        response_text = self._generate_with_retry(prompt)
        edited_events = self._parse_events_from_response(
            response_text=response_text,
            fallback_summary=self.config.default_event_title,
        )

        if not edited_events:
            raise ValueError("AI edit returned no valid events")

        return edited_events
