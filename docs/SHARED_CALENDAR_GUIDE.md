# Shared Calendar Library Guide

## Overview

The Shared Calendar Library feature allows users to save and share extracted calendars so others can use them without needing the original schedule text.

---

## 📚 How It Works

### Traditional Flow (Before)
```
User 1: Paste schedule → Extract → Export
User 2: Paste SAME schedule → Extract → Export
                ⬆️
         Must have original text
```

### New Flow (With Shared Library)
```
User 1: Paste schedule → Extract → Export → Share (with name)
                                               ↓
                                    [Shared Calendar Library]
                                               ↓
User 2: Browse library → Use calendar → Export
                ⬆️
          No original text needed!
```

---

## 🎯 Use Cases

### 1. Team Coaches
Share weekly practice schedules so team members can import without coordination:
- Coach: Create & share "MIT Team - March 2026"
- Team: Browse library → Load → Import to phone

### 2. Recurring Schedules
Save commonly used schedules for quick access:
- "Weekend Practice Schedule"
- "Competition Week Schedule"
- "Summer Training Camp"

### 3. Template Calendars
Create template schedules for different groups:
- "Beginner Group - Monday/Wednesday"
- "Advanced Group - Full Week"
- "Masters Schedule"

---

## 📖 User Guide

### Browsing Shared Calendars

1. **Open the app** - Go to http://localhost:8501
2. **Expand library** - Click "📚 Browse Shared Calendars (N available)"
3. **Review options** - See calendar name, description, event count, date
4. **Load calendar** - Click "Use This" on any calendar

**What happens:**
- Events load into the calendar view immediately
- You can edit, modify, or export them
- No AI extraction needed (saves API quota!)

---

### Sharing Your Calendar

1. **Extract events** - Paste schedule → Click "🤖 Extract Events"
2. **Review & edit** - Check events, make any changes needed
3. **Export first** - Click "📥 Export" to see download options
4. **Share** - Click "📤 Share This Calendar"
5. **Fill form:**
   - **Name** (required): Descriptive name, e.g., "MIT Team - March 2026"
   - **Description** (optional): Brief explanation, e.g., "Mon/Wed/Fri practices"
6. **Confirm** - Click "✓ Share"

**What happens:**
- Calendar saved to `shared_calendars/` directory
- Appears in library for all users
- Others can load and export without original text

---

### Managing Shared Calendars

**Sidebar Controls:**
- **Shared**: Count of shared calendars
- **Size**: Total storage used
- **Manage Shared**: Expander to delete calendars

**To delete:**
1. Open sidebar → Click "Manage Shared"
2. Find calendar to delete
3. Click "🗑️" trash icon
4. Confirm deletion

---

## 🗂️ Storage Details

### File Structure
```
shared_calendars/
├── a1b2c3d4.json   # Calendar 1
├── e5f6g7h8.json   # Calendar 2
└── ...
```

### JSON Format
```json
{
  "id": "a1b2c3d4",
  "name": "MIT Team - March 2026",
  "description": "Monday/Wednesday/Friday practices",
  "created_at": "2026-03-01T10:30:00",
  "event_count": 3,
  "events": [
    {
      "start_time": "2026-03-03T18:00:00",
      "end_time": "2026-03-03T20:00:00",
      "summary": "Swim Practice",
      "location_name": "Regis",
      "location_address": "Regis College Athletic Facility...",
      "is_ambiguous": false,
      "day_type": "weekday",
      "duration_minutes": 120
    }
  ]
}
```

### Storage Location
- **Local dev**: `calendar_import/shared_calendars/`
- **Gitignored**: Not committed to repository
- **Per-instance**: Each deployment has its own library

---

## 🔒 Security & Privacy

### What's Stored
- ✅ Event dates, times, locations
- ✅ User-provided calendar name/description
- ✅ Created timestamp

### What's NOT Stored
- ❌ User identity (anonymous sharing)
- ❌ Original schedule text (only events)
- ❌ API keys or credentials
- ❌ Personal information

### Access Control
- **Local deployment**: Only users on local network can access
- **Cloud deployment**: Protected by Streamlit Cloud authentication
- **File system**: Standard OS file permissions apply

---

## 🎨 UI Design Principles

### Browse Before Input
- Library shown **before** schedule input
- Encourages browsing before creating new
- Reduces duplicate calendars

### Optional Workflow
- Sharing is **opt-in** (not automatic)
- Users choose what to share
- No pressure to share private schedules

### Minimal Friction
- One-click loading ("Use This")
- Simple form (name + optional description)
- No login required for local use

---

## 🧪 Testing

Run the test suite:

```bash
# Test SharedCalendarManager
python tests/test_shared_calendars.py

# Test complete workflow
python tests/test_shared_calendar_e2e.py
```

**No API calls required** - These tests use pre-created events.

---

## 🚀 Advanced: Programmatic Usage

```python
from shared_calendar_manager import SharedCalendarManager
from models import Event, Config
from datetime import datetime

# Initialize
manager = SharedCalendarManager()
config = Config.get_default_config()

# Create events
events = [
    Event(
        start_time=datetime(2026, 3, 10, 18, 0),
        end_time=datetime(2026, 3, 10, 20, 0),
        summary="Swim Practice",
        location=config.locations["Regis"],
        location_name="Regis"
    )
]

# Share
shared_cal = manager.save(
    name="My Schedule",
    description="Weekly practice",
    events=events
)

# Browse
all_calendars = manager.list_all()
for cal in all_calendars:
    print(f"{cal.name}: {cal.event_count} events")

# Load
loaded = manager.get_by_id(shared_cal.id, config.locations)

# Delete
manager.delete(shared_cal.id)
```

---

## 🔮 Future Enhancements

Potential features for v2:
- 🔍 Search/filter shared calendars by keyword
- ⭐ Rating/favorite system
- 🏷️ Tags/categories (Beginner, Advanced, Competition, etc.)
- 📊 Usage statistics (most popular calendars)
- 💬 Comments/feedback on shared calendars
- 🔄 Calendar updates/versioning
- 🌐 Cloud sync across instances

---

## ❓ FAQ

**Q: Can I share calendars anonymously?**  
A: Yes! No login required for local deployments. Calendars are anonymous by default.

**Q: How long do shared calendars last?**  
A: Forever, until manually deleted. No automatic expiration.

**Q: Can I edit a shared calendar?**  
A: Not directly. Load it, make your changes with AI editing, then share as a new calendar.

**Q: What if two calendars have the same name?**  
A: Allowed! Each has a unique ID. Names are for human readability only.

**Q: Can I share to other instances?**  
A: Not automatically. Each instance has its own library. Export/import JSON files manually if needed.

**Q: Does this use AI/API calls?**  
A: No! Browsing and loading shared calendars is instant and free (no API calls).

---

## 🐛 Troubleshooting

**Library shows 0 calendars**
- No one has shared yet - be the first!
- Check if `shared_calendars/` directory exists

**"Use This" button doesn't work**
- Check browser console for errors
- Verify events have valid location names
- Reload the page

**Can't share calendar**
- Calendar name is required
- Must have events loaded first
- Check write permissions to `shared_calendars/`

**Shared calendar missing after restart**
- Check if `shared_calendars/` is gitignored (not committed)
- Verify files exist in the directory
- Check file permissions

---

**Need help?** Open an issue on GitHub with your question!
