# Troubleshooting Guide

## ❌ \"API key not valid\" Error

**Most Common Cause:** Streamlit app started before `.env` file was created.

**Quick Fix:**
```powershell
# Restart the app
.\restart_app.ps1

# Or manually: Ctrl+C → streamlit run app.py
```

**Verify API key works:**
```powershell
python tests/test_api.py
# Should show: ✓ API key loaded
```

**Check `.env` format:**
```bash
# Correct format (no spaces around =)
GEMINI_API_KEY=GOOGLE_API_KEY_PREFIX_C...

# Wrong format
GEMINI_API_KEY = your-key  ❌
GEMINI_API_KEY="your-key"  ❌
```

---

## ❌ \"No events extracted\"

**Check input format:**
- Must contain dates and times
- Try: \"Jan 29 6-8pm swim @ Regis\"
- Separate events with line breaks

**Test with simple example:**
```
周四 1/29 下午 6-8 下水 @ Regis
周五 1/30 下午 5-7 下水 @ Regis
```

---

## ❌ Wrong locations assigned

**Fix in UI:**
1. Click on event in results table
2. Edit location dropdown
3. Click \"Update Event\"

**Fix in input:**
Add explicit location mentions:
```
# Good
周四 1/29 6-8pm @ Regis
周五 1/30 5-7pm @ Brandeis

# Less clear
周四 1/29 6-8pm 下水
```

---

## ❌ iOS Calendar won't import .ics file

**Solution:** Use ZIP download instead:
1. Export as \"ZIP Package\"
2. Save to iPhone Files app
3. Extract and open individual .ics files

**Alternative:** Email .ics file to yourself and open from Mail app.

---

## ❌ App won't start

**Check Python environment:**
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify installation
pip list | Select-String streamlit
# Should show: streamlit x.x.x

# Reinstall if missing
pip install -r requirements.txt
```

**Check port conflicts:**
```powershell
# Kill any Python processes
Get-Process python | Stop-Process -Force

# Try different port
streamlit run app.py --server.port 8502
```

---

## ❌ Rate limit errors (Gemini API)

**Symptom:** \"Quota exceeded\" or \"Too many requests\"

**Free tier limits:**
- 15 requests per minute
- 1,500 requests per day

**Solutions:**
- Wait 1 minute between large extractions
- Cache works - identical inputs reuse results
- Consider upgrading to Gemini Pro

---

## ❌ Development Issues

**Tests failing:**
```powershell
# Run specific test
python tests/test_api.py
python tests/test_extraction.py

# Full test suite (wait 30s between runs)
.\run_tests.ps1
```

**Cache issues:**
```powershell
# Clear cache if results seem stale
Remove-Item cache\*.json -Force
```

**Virtual environment issues:**
```powershell
# Recreate venv
Remove-Item venv -Recurse -Force
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🌐 Network & Security Issues

**Can't access app from phone/tablet:**
- **Expected behavior** - app runs on localhost (127.0.0.1)
- For network access, use: `streamlit run app.py --server.address 0.0.0.0`
- **Security warning:** Only use 0.0.0.0 on trusted networks

**Firewall blocking app:**
```powershell
# Windows - allow Streamlit through firewall
.\setup_firewall.ps1
```

---

## 🔍 Getting More Help

**Gather information:**
1. **Python version:** `python --version`
2. **Streamlit version:** `streamlit version`
3. **Error messages:** Copy full error text
4. **Input sample:** Share problematic schedule text

**Check logs:**
```powershell
# Streamlit shows errors in terminal
# Look for red error messages

# Test each component
python tests/test_api.py      # API connection
python tests/test_extraction.py  # Event extraction
```

**Common solutions first:**
1. ⟲ **Restart the app** (fixes 80% of issues)
2. ⟲ **Check `.env` file** exists and format is correct
3. ⟲ **Test API key** independently
4. ⟲ **Try simpler input** to isolate the problem

**Still stuck?**
- Check [GitHub Issues](https://github.com/your-username/swimming-schedule-converter/issues)
- Create new issue with error details and input sample