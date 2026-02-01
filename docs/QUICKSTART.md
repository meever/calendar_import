# Quick Start Guide

## 🚀 For End Users (Desktop Launcher)

**Already have the app installed?** This is for you!

### Step 1: Double-Click Desktop Shortcut

Find this file on your desktop:
```
📁 Desktop → "Start Swimming Calendar.bat"
```

**Double-click it** - that's all! The app will:
- ✅ Start at http://localhost:8501
- ✅ Open in your browser automatically
- ✅ Run securely on localhost only
- ✅ Kill any old instances first

### Step 2: Use the App

1. **Paste your schedule** in the text area
2. **Review extracted events** in the table
3. **Edit if needed** (click on any event)
4. **Export** - Choose format and download

### Step 3: Stop the App

Close the command window or press `Ctrl+C`.

---

## 🛠️ For Developers (First Time Setup)

### Windows Setup

**1. Clone the repository**
```powershell
git clone https://github.com/your-username/swimming-schedule-converter.git
cd swimming-schedule-converter
```

**2. Create virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**3. Install dependencies**
```powershell
pip install -r requirements.txt
```

**4. Get API key**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create new API key
3. Copy the key (starts with `AIzaSy...`)

**5. Create `.env` file**
```powershell
# Create .env file in project root
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

**6. Test setup**
```powershell
# Test API connection
python tests/test_api.py

# Should show: ✓ API key loaded
```

**7. Run the app**
```powershell
streamlit run app.py
```

App opens at: http://localhost:8501

### Mac/Linux Setup

```bash
# Clone and setup
git clone https://github.com/your-username/swimming-schedule-converter.git
cd swimming-schedule-converter

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your-api-key-here" > .env

# Test and run
python tests/test_api.py
streamlit run app.py
```

---

## 📱 Usage Guide

### Input Format

Paste any swimming schedule text (Chinese/English):

```
群公告
ARCT 🏊 Junior Group 一月训练时间表：

周四 1/29 下午 6 - 8  下水+陆上 @ Regis
周五 1/30 下午 5 - 7  下水 @ Regis
周六 2/1  上午 9 - 11 下水 @ Brandeis
```

### Features

**✅ Smart Event Extraction**
- Recognizes dates, times, locations
- Combines water + dryland sessions
- Handles both Chinese and English

**✅ Location Intelligence**
- Knows swim facility addresses
- Auto-assigns based on day/context
- Weekdays → Regis, Weekends → Brandeis

**✅ Multiple Export Formats**
- `.ics` files (iPhone, Google Calendar)
- Individual or ZIP download
- Includes original text in notes

**✅ Event Validation**
- Shows warnings for past dates
- Highlights ambiguous events
- Allows manual editing

### Troubleshooting

**❌ "API key not valid"**
```powershell
# Restart the app (most common fix)
.\restart_app.ps1

# Or manually:
# Ctrl+C → streamlit run app.py
```

**❌ "No events extracted"**
- Check input contains dates and times
- Try simpler format: "Jan 29 6-8pm swim @ Regis"
- Verify text is actually a schedule (not random text)

**❌ Wrong locations**
- Edit events manually in the table
- Add explicit location: "@ Regis" or "@ Brandeis"

**❌ Missing events**
- Check for typos in dates/times
- Try separating combined sessions
- Add line breaks between events

---

## 🚀 Next Steps

**For End Users:**
- Bookmark http://localhost:8501
- Share the desktop launcher with teammates
- Export calendars regularly

**For Developers:**
- See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment
- Run `python -m pytest tests/` for full test suite
- Check [GitHub Issues](https://github.com/your-username/swimming-schedule-converter/issues) for known issues

**For Team Leads:**
- Deploy to Streamlit Cloud for team sharing
- Set up password protection for security
- Consider Linux server for production use

### Step 2: Use the App

The browser will open to `http://localhost:8501`

1. **Paste your schedule** in the text area
2. **Review extracted events** in the table
3. **Edit if needed** (click on any event)
4. **Export** - Choose format and click Export button

### Step 3: Stop the App

Close the command window, or press `Ctrl+C` in the terminal.

---

## 🔧 What the Launcher Does

The `Start Swimming Calendar.bat` file:

```batch
1. Changes to project directory: D:\code\calendar_import
2. Kills any old Python/Streamlit processes
3. Activates virtual environment
4. Runs: streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

**Security**: Binds to `127.0.0.1` (localhost) - NOT accessible from:
- Other computers on your network
- Your phone/tablet (even on same WiFi)
- The internet

Only **this computer** can access the app ✅

---

## ⚙️ Configuration (Advanced)

### Change AI Model

Edit `config.json`:
```json
{
  "gemini_model": "gemini-flash-latest"
}
```

**Options**:
- `gemini-flash-latest` ✅ **Default** - Auto-updates, FREE
- `gemini-pro-latest` - More powerful, 10x cost
- `gemini-2.5-flash` - Specific version (no auto-update)

### Change Port

Edit `config.json`:
```json
{
  "port": 8501
}
```

Then update desktop shortcut to use new port.

### Allow Network Access (NOT Recommended)

⚠️ **Warning**: This makes app accessible to anyone on your WiFi

Edit `config.json`:
```json
{
  "host": "0.0.0.0"
}
```

**Keep default** `127.0.0.1` for security ✅

---

## 🔐 API Key Security

**Where is it stored?**
- File: `D:\code\calendar_import\.env`
- Format: `GEMINI_API_KEY=AIzaSyC...`

**Is it encrypted?**
- ❌ No (stored as plain text)
- ✅ This is **standard practice** for local development
- ✅ Protected by Windows file permissions
- ✅ Never committed to Git (in `.gitignore`)
- ✅ Never sent over network (stays on your computer)

**Risk Level**: ⚠️ **Low** - Only readable by your Windows user account

See [SECURITY.md](SECURITY.md) for full details.

---

## 🆘 Troubleshooting

### Desktop Shortcut Not Working?

1. **Check path**: Open `Start Swimming Calendar.bat` in Notepad
2. **Verify line 11**: Should be `cd /d "D:\code\calendar_import"`
3. **Fix if needed**: Change to your actual project location

### App Won't Start?

```powershell
# Check if API key exists
Get-Content D:\code\calendar_import\.env

# Should show: GEMINI_API_KEY=AIzaSyC...
```

### Wrong Port?

Edit desktop shortcut `.bat` file, change port in this line:
```batch
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

### Want to Run Tests First?

Instead of desktop shortcut, use:
```powershell
cd D:\code\calendar_import
.\dev.ps1
```

This runs all tests before starting the app.

---

## 📚 More Information

- **Full documentation**: [../README.md](../README.md)
- **Security details**: [SECURITY.md](SECURITY.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Linux deployment**: [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md)
- **Cloud deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Enjoy your swimming schedule converter!** 🏊
