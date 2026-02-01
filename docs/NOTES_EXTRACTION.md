# Event Notes - Original Text Extraction

## Overview
Each calendar event now includes the exact original text snippet from the input schedule in its notes field, making it easy to trace back to the source.

## How It Works

### 1. Individual Event Snippets
The AI extracts the specific text snippet for each event and stores it in the `raw_text` field.

**Example:**
```
Input: "周四 1/29 下午 6 - 8 下水+陆上 @ Regis"
Event Notes: "周四 1/29 下午 6 - 8 下水+陆上 @ Regis"
```

### 2. Merged Event Snippets
When multiple overlapping events are merged, both original snippets are preserved and joined with " | ".

**Example:**
```
Input: 
  "参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis"
  "不参加 Silvers 的队员照常训练 下午 5 - 7 下水"

Merged Event Notes: 
  "参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis | 不参加 Silvers 的队员照常训练 下午 5 - 7 下水"
```

### 3. Inferred Events
For events that the AI infers but cannot map to specific text (rare), the notes will show:
```
"(Inferred from schedule)"
```

## Implementation Details

### AI Prompt
The AI is instructed to:
- Extract the **exact original text** for each event (no rephrasing)
- Use exact characters from the input (preserve Chinese/English/punctuation)
- For merged events, join snippets with " | " separator
- Return `null` for `original_text` if the event is inferred

### JSON Response Format
```json
{
  "date": "2026-01-29",
  "start_time": "18:00",
  "end_time": "20:00",
  "summary": "Swim Practice",
  "location": "Regis",
  "original_text": "周四 1/29 下午 6 - 8 下水+陆上 @ Regis"
}
```

### Event Merging Logic
When overlapping events are merged:
1. Collect all `raw_text` snippets from merged events
2. Filter out "(Inferred from schedule)" placeholder
3. Join remaining snippets with " | " separator
4. Store result in merged event's `raw_text` field
5. Add merge details to `notes` field

## Benefits

1. **Traceability**: Easy to see exactly what input text generated each event
2. **Verification**: Quickly verify AI extraction accuracy
3. **Context**: Understand special instructions or conditions from original text
4. **Debugging**: Identify extraction issues or ambiguities

## Calendar Export

The `raw_text` snippet is included in calendar exports:

### ICS Files
```
DESCRIPTION: 周四 1/29 下午 6 - 8 下水+陆上 @ Regis
```

### CSV Files
The snippet appears in the "Description" column.

For merged events, both the snippet and merge information are included:
```
DESCRIPTION: 参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis | 不参加 Silvers 的队员照常训练 下午 5 - 7 下水

NOTE: Combined 2 groups:
• 17:00-18:00: 参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis
• 17:00-19:00: 不参加 Silvers 的队员照常训练 下午 5 - 7 下水
```

## Technical Architecture

### Code Locations

**AI Extraction** (`src/extractor.py`):
- Lines 40-95: System prompt with `original_text` field specification
- Lines 138-150: JSON response parsing (handles both list and dict formats)
- Lines 175-180: Event creation with snippet extraction

**Event Merging** (`src/rules_engine.py`):
- Lines 156-165: Snippet concatenation logic for merged events
- Lines 167-175: Notes generation showing merge details

**Calendar Export** (`src/calendar_exporter.py`):
- ICS export includes `raw_text` in DESCRIPTION field
- CSV exports include snippet in Description column

## Testing

All test suites verify snippet extraction:

**Test Files**:
- `tests/test_extraction.py`: Individual snippet extraction (12 events)
- `tests/test_e2e.py`: Merged event snippets (11 events after merging)

**Test Coverage**:
- ✅ Individual event snippets extracted correctly
- ✅ Merged event snippets concatenated with " | "
- ✅ Events with underwater + dryland in one line preserved as-is
- ✅ Fallback to "(Inferred from schedule)" works

**Run Tests**:
```powershell
.\run_tests.ps1
```

## Example Output

### Single Event
```
Event: 2026-01-29 18:00 - Swim Practice @ Regis
Snippet: 周四 1/29 下午 6 - 8 下水+陆上 @ Regis
```

### Merged Event
```
Event: 2026-01-30 17:00 - Swim Practice @ Regis
Snippet: 参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis | 不参加 Silvers 的队员照常训练 下午 5 - 7 下水
Notes: Combined 2 groups:
  • 17:00-18:00: 参加比赛但没有比赛项目的队员 下午5 - 6 下水 @ Regis
  • 17:00-19:00: 不参加 Silvers 的队员照常训练 下午 5 - 7 下水
```

### Combined Session (Underwater + Dryland)
```
Event: 2026-01-31 18:00 - Swim Practice @ Brandeis
Snippet: 1/31 周六 6-7:30pm 下水 + 7:30~8pm 陆上拉伸 @ Brandeis ⚠️
```

## Configuration

No configuration needed. The feature is automatic and works for all events.

## Version History

- **2026-01-31**: Implemented individual snippet extraction
  - AI prompt updated to request `original_text` field
  - Event creation uses individual snippets instead of full input
  - Merge logic concatenates snippets with " | " separator
  - All tests updated and passing
