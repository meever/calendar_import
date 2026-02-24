# Swimming Schedule to Calendar Converter

**AI-powered tool to convert unstructured swimming schedules (mixed Chinese/English) into calendar files.**

🎯 **Perfect for**: Swim teams, coaches, parents managing practice schedules  
🤖 **Powered by**: Google Gemini 2.5 Flash (auto-updates)  
📱 **Mobile-friendly**: Works on desktop, tablet, and phone  
🔒 **Local-first**: Runs on localhost by default

---

## ✨ Features

- **🤖 AI Extraction** - Understands mixed Chinese/English schedules
- **📚 Shared Calendar Library** - Browse and use calendars shared by others
- **📤 Share Your Calendars** - Save calendars with names for others to use
- **📊 Smart Session Merging** - Combines underwater + dryland into single events
- **✏️ AI-Powered Editing** - Modify events with natural language instructions
- **📅 One-Click Downloads** - Export as iCalendar (.ics) or ZIP package (.zip)
- **🔒 Secure & Private** - API key never exposed, local network only
- **🏗️ Professional Architecture** - Modular, tested, production-ready

---

## 🚀 Quick Start

### Windows Desktop Launcher (Easiest)

1. **Double-click**: `Start Swimming Calendar.bat` on your desktop
2. **Access**: http://localhost:8501
3. **Done!** App runs automatically

See **[docs/QUICKSTART.md](docs/QUICKSTART.md)** for details.

### Manual Setup

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd calendar_import
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup API key
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# Edit .env and add: GEMINI_API_KEY=your-key-here
# Get key from: https://aistudio.google.com/app/apikey

# 4. Run tests
.\run_tests.ps1  # Windows (recommended)

# 5. Start app
.\dev.ps1  # Windows (runs tests first)
# Or: streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Access**:
- This computer: http://localhost:8501

---

## 📖 How to Use

### 1. Use the Tabs
- **🆕 Create New**: paste schedule → extract → edit with AI → review → export
- **📚 Use Shared**: pick a shared calendar → review → edit with AI → export
- **❓ How To**: quick steps and minimal examples for both workflows

### 3. Input Schedule Example
Paste your unstructured schedule text. Example:

```
周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午5-6 下水 @ Regis
1/31 周六 6-7:30pm 下水 @ Brandeis
```

### 4. Export
Click **"📥 Export"** to show download options:
- **📅 iCalendar (.ics)** - Works with iOS, Mac, Outlook, most apps
- **📦 ZIP (.zip)** - Contains .ics file for iOS Files app

In **📚 Use Shared**, selecting and loading a shared calendar opens these same download options and shows which shared calendar is being used.

### 5. Share (Optional)
- Click **"📤 Share This Calendar"** after exporting
- Give it a name and description
- Others can browse and use it without the original text!

**iPhone note:** Mobile Safari may not show a direct download option for .ics files. If you can't save the file to Files, use the ZIP download option and unzip in Files.

---

## 🏗️ Architecture

```
calendar_import/
├── app.py                    # Streamlit web interface
├── src/
│   ├── models.py             # Data models (Event, Location, Config)
│   ├── config_manager.py     # Configuration persistence
│   ├── extractor.py          # AI extraction via Gemini
│   ├── rules_engine.py       # Business logic & validation
│   └── calendar_exporter.py  # Calendar export utilities
├── config.json               # Persistent configuration (auto-generated)
├── .env                      # API key (create this!)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Core Components

**`models.py`** - Type-safe data structures
- `Event`: Calendar event with validation
- `Location`: Physical location with defaults
- `Config`: App configuration with persistence
- Enums for DayType and CalendarFormat

**`extractor.py`** - AI-powered extraction
- Gemini 2.5 Flash integration
- Context-aware prompting with location knowledge
- JSON schema validation

**`rules_engine.py`** - Business logic
- **Rule 1**: Explicit location mentions override defaults
- **Rule 2**: Weekday events → Regis (default)
- **Rule 3**: Weekend events → Brandeis (default)
- Event validation, deduplication, sorting

**`calendar_exporter.py`** - Export services
- ICS generation (iOS-compatible)
- ZIP packaging for safer mobile download flow

---

## ⚙️ Configuration

### Knowledge Base (Editable via UI)

Manage locations in the sidebar:
- Add/edit/delete locations
- Set weekday/weekend defaults
- Update addresses

### Default Locations

```json
{
  "Regis": {
    "address": "Regis College Athletic Facility, 235 Wellesley St, Weston, MA",
    "is_default_weekday": true
  },
  "Brandeis": {
    "address": "Gosman Sports and Convocation Center, 415 South St, Waltham, MA",
    "is_default_weekend": true
  },
  "Wightman": {
    "address": "Wightman Tennis Center, 100 Brown St, Weston, MA"
  }
}
```

All configuration is saved to `config.json` automatically.

---

## 🧪 Testing

### Run All Tests

```powershell
# Windows PowerShell
.\run_tests.ps1
```

```bash
# Mac/Linux
python tests/test_api.py && python tests/test_extraction.py && python tests/test_e2e.py
```

### Test Suite Includes:

1. **API Key Validation** (`tests/test_api.py`)
   - Verifies Gemini API key is valid
   - Lists available models
   - Tests basic API connectivity

1. **Event Extraction** (`tests/test_extraction.py`)
   - Tests full extraction pipeline with real Chinese/English schedule
   - Validates event extraction and merging
   - Checks location assignment rules
   - Verifies business logic

1. **Combined Sessions** (`tests/test_combined_sessions.py`)
   - Validates underwater + dryland merge rules
   - Verifies duration/combining behavior

1. **ICS Encoding** (`tests/test_ics_encoding.py`)
   - Validates iOS-friendly ICS formatting
   - Ensures encoding and calendar headers are correct

1. **ICS ZIP** (`tests/test_ics_zip.py`)
   - Validates ZIP package generation for .ics export

1. **End-to-End Test** (`tests/test_e2e.py`)
   - Complete workflow with real schedule
   - Validates overlapping event merging
   - Checks rest day handling
   - Verifies all business rules

1. **Shared Calendar CRUD** (`tests/test_shared_calendars.py`)
   - Verifies save/list/load/delete flows for shared calendars

1. **Shared Calendar E2E** (`tests/test_shared_calendar_e2e.py`)
   - Verifies browse → use → export-ready workflow

### Test Case (Preserved)

```text
周四 1/29 下午 6 - 8 下水+陆上 @ Regis
周五 1/30 下午 6 - 8 下水 @ Regis
周六 1/31 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/1 上午 9 - 11 下水 @ Wightman

周四 2/5 下午 6 - 8 下水+陆上 @ Regis
周五 2/6 下午 6 - 8 下水 @ Regis
周六 2/7 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/8 上午 9 - 11 下水 @ Brandeis

周四 2/12 下午 6 - 8 下水+陆上 @ Regis
周五 2/13 下午 6 - 8 下水 @ Regis
周六 2/14 上午 9 - 11 下水+陆上 @ Brandeis
周日 2/15 上午 9 - 11 下水 @ Brandeis
```

**Expected Result**: 12 events with correct dates, times, and locations

### Before Any Code Changes

**Always run tests first!** This ensures:
- API key is working
- Core extraction logic is intact
- Business rules haven't broken
- No regressions introduced

---

## 🔧 Development

### Project Structure

- **Data Layer**: `models.py` - Type-safe dataclasses
- **Business Logic**: `rules_engine.py` - Pure functions
- **External Services**: `extractor.py`, `calendar_exporter.py`
- **Infrastructure**: `config_manager.py` - Persistence
- **Presentation**: `app.py` - Streamlit UI

### Adding New Features

**New Export Format**:
1. Add format to `CalendarFormat` enum in `models.py`
2. Implement export method in `calendar_exporter.py`
3. Update UI in `app.py`

**New Business Rule**:
1. Add logic to `rules_engine.py`
2. Update validation in `validate_events()`

**New Location**:
- Just use the web UI! No code changes needed.

---

## 🌐 Deployment Options

### Streamlit Community Cloud (FREE)

Perfect for personal/team use - **5 minute setup**:

**Quick Steps**:
1. Push to GitHub: `git remote add origin <url>` → `git push -u origin main`
2. Deploy at [share.streamlit.io](https://share.streamlit.io) → "New app"
3. Add secrets: `GEMINI_API_KEY = "your-key-here"` (in Advanced settings → Secrets)
4. Share URL: `https://your-app.streamlit.app` ✅

**Full detailed guide**: See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for step-by-step instructions with screenshots, troubleshooting, and security info.

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t swim-calendar .
docker run -p 8501:8501 -e GEMINI_API_KEY=your-key swim-calendar
```

### Render/Railway/Fly.io

All support Python apps. Add `GEMINI_API_KEY` environment variable.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](docs/QUICKSTART.md)** | Desktop launcher & quick access guide |
| **[SHARED_CALENDAR_GUIDE.md](docs/SHARED_CALENDAR_GUIDE.md)** | Shared calendar library workflow |
| **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Common issues & solutions |
| **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Cloud deployment (Streamlit/Docker) |
| **[NOTES_EXTRACTION.md](docs/NOTES_EXTRACTION.md)** | Original-text extraction notes |

---

## ⚙️ Configuration

**Edit `config.json`** to customize:

```json
{
  "gemini_model": "gemini-flash-latest",  // Auto-updates to newest
  "host": "127.0.0.1",                    // Localhost only
  "port": 8501,
  "timezone": "America/New_York",
  "locations": { ... }
}
```

**Available models**:
- `gemini-flash-latest` ✅ **Recommended** - Auto-updates, FREE (1500 req/day)
- `gemini-pro-latest` - More powerful, 10x cost
- `gemini-2.5-flash` - Pinned version (no auto-update)

**Cost**: FREE tier 1500 requests/day, or $0.075 per 1M tokens (~$0.0001 per schedule)

---

## 🔒 Security & Privacy

- **API key**: Stored in `.env` (gitignored, never committed)
- **Network**: Runs on localhost by default (`127.0.0.1`)
- **No cloud storage**: All processing local to your instance
- **Open source**: Audit the code yourself

---


## 📋 Dependencies

```
google-genai     # Gemini API (new package)
ics              # Calendar file generation
streamlit        # Web interface
python-dotenv    # Environment management
pandas           # Data handling
```

---

## 🐛 Troubleshooting

**Quick fixes**:
- **API key not found**: Check `.env` file exists with `GEMINI_API_KEY=...`
- **Tests fail**: Ensure `.env` has valid API key
- **Wrong timezone**: Edit `config.json` → `"timezone": "Your/Timezone"`

See **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** for detailed solutions.

---

## 📄 License

MIT License - Use freely for personal or commercial purposes.

---

## 🤝 Contributing

Contributions welcome! This is a well-architected codebase:
- Clean separation of concerns
- Type hints throughout
- Modular design
- Easy to extend

---

## 🌟 Credits

Built with:
- [Streamlit](https://streamlit.io) - Web framework
- [Google Gemini](https://ai.google.dev) - AI model
- [python-ics](https://github.com/C4ptainCrunch/ics.py) - Calendar generation

---

**Made with ❤️ for swimmers and coaches**
