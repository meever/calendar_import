# Swimming Schedule to Calendar Converter

**AI-powered tool to convert unstructured swimming schedules (mixed Chinese/English) into calendar files.**

🎯 **Perfect for**: Swim teams, coaches, parents managing practice schedules  
🤖 **Powered by**: Google Gemini 2.5 Flash (auto-updates)  
📱 **Mobile-friendly**: Works on desktop, tablet, and phone  
🌐 **Network-ready**: Access from any device on your local network

---

## ✨ Features

- **🤖 AI Extraction** - Understands mixed Chinese/English schedules
- **📚 Editable Knowledge Base** - Manage locations and rules via web UI
- **📊 Smart Session Merging** - Combines underwater + dryland into single events
- **📅 Multiple Formats** - Export to iOS (.ics), Google Calendar (.csv), Outlook (.csv)
- **🔒 Secure & Private** - API key never exposed, local network only
- **🏗️ Professional Architecture** - Modular, tested, production-ready

---

## 🚀 Quick Start

### Windows Desktop Launcher (Easiest)

1. **Double-click**: `Start Swimming Calendar.bat` on your desktop
2. **Access**: http://localhost:8501 or http://192.168.1.10:8501
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
- From phone/tablet: http://192.168.1.10:8501 (same WiFi)

---

## 📖 How to Use

### 1. Input Schedule
Paste your unstructured schedule text. Example:

```
周四 1/29 下午 6-8 下水+陆上 @ Regis
周五 1/30 下午5-6 下水 @ Regis
1/31 周六 6-7:30pm 下水 @ Brandeis
```

### 2. Review Events
- See extracted events in a clean table
- Check locations, times, dates
- Edit any event if needed
- Delete unwanted events

### 3. Export
Choose your format:
- **📅 iCalendar (.ics)** - Works with iOS, Mac, Outlook, most apps
- **📆 Google Calendar (.csv)** - Import to Google Calendar
- **📧 Outlook (.csv)** - For Microsoft Outlook

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
│   └── calendar_exporter.py  # Multi-format export
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

**`calendar_exporter.py`** - Multi-format export
- ICS (universal)
- Google Calendar CSV
- Outlook CSV
- Extensible for new formats

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

2. **Event Extraction** (`tests/test_extraction.py`)
   - Tests full extraction pipeline with real Chinese/English schedule
   - Validates event extraction and merging
   - Checks location assignment rules
   - Verifies business logic

3. **End-to-End Test** (`tests/test_e2e.py`)
   - Complete workflow with real schedule
   - Validates overlapping event merging
   - Checks rest day handling
   - Verifies all business rules

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
| **[LINUX_DEPLOYMENT.md](docs/LINUX_DEPLOYMENT.md)** | Deploy to Linux servers |
| **[SECURITY.md](docs/SECURITY.md)** | API key & network security details |
| **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Common issues & solutions |
| **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** | Cloud deployment (Streamlit/Docker) |

---

## ⚙️ Configuration

**Edit `config.json`** to customize:

```json
{
  "gemini_model": "gemini-flash-latest",  // Auto-updates to newest
  "host": "0.0.0.0",                      // Network access enabled
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
- **Network**: Accessible from local network only (192.168.x.x)
- **No cloud storage**: All processing local to your instance
- **Open source**: Audit the code yourself

See **[docs/SECURITY.md](docs/SECURITY.md)** for detailed security information.

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
- **Can't access from phone**: Run `.\setup_firewall.ps1` as Administrator
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
