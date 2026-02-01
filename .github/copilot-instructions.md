# GitHub Copilot Instructions - Swimming Schedule Converter

## Project Overview
AI-powered swimming schedule converter using Google Gemini 2.5 Flash to extract structured calendar events from unstructured Chinese/English text.

---

## Core Engineering Principles

### 0. API Rate Limiting - Critical for Free Tier
**⚠️ Using Gemini 2.5 Flash FREE TIER - Strict rate limits apply!**

**Rate Limit Strategy:**
- **RPM (Requests Per Minute):** 15 requests/minute for free tier
- **Avoid rapid successive API calls** - space out test runs
- **Cache is your friend** - reuses results without API calls
- **Wait 5+ seconds between test runs** to avoid quota errors

**During Development:**
```powershell
# ❌ DON'T run full suite repeatedly
.\run_tests.ps1  # (makes 6+ API calls)
# ... make change ...
.\run_tests.ps1  # (another 6+ calls) - TOO FAST!

# ✅ DO run targeted tests
python tests/test_api.py           # 1 call - verify API key
python tests/test_cache.py         # 2-3 calls - test caching
python tests/test_combined_sessions.py  # 1 call - session logic
# ... wait 10 seconds ...
# ... make change ...
python tests/test_extraction.py    # 1 call - verify extraction
```

**API Call Budget:**
- `test_api.py` - **1 API call** (quick validation)
- `test_extraction.py` - **1 API call** (may use cache on reruns)
- `test_combined_sessions.py` - **1 API call** (may use cache)
- `test_cache.py` - **2-3 API calls** (tests cache miss/hit)
- `test_e2e.py` - **1 API call** (comprehensive validation)
- **Total:** ~6-7 calls per full suite run

**Rate Limit Safety:**
- Full suite takes ~15-20 seconds (built-in delays)
- **Wait 30+ seconds between full suite runs**
- If you get quota errors, wait 1 minute before retrying
- Cache reduces API calls on subsequent runs with same input

### 1. Testing Strategy - Optimized for Development
**Smart testing saves API quota and development time.**

**Three-Tier Testing Approach:**

#### Tier 1: Quick Validation (No/Minimal API calls)
**Use during active development - run frequently**
```powershell
# API key check only (1 call, <2 seconds)
python tests/test_api.py

# Code syntax/import checks (0 calls)
python -m py_compile src/*.py
```
**When to use:** After small code changes, syntax fixes, refactoring

#### Tier 2: Targeted Testing (1-2 API calls)
**Use when working on specific features**
```powershell
# Working on extraction logic?
python tests/test_extraction.py        # 1 call (uses cache after first run)

# Working on session combining?
python tests/test_combined_sessions.py # 1 call

# Working on cache?
python tests/test_cache.py             # 2-3 calls (intentional)

# Working on ICS export?
python tests/test_ics_encoding.py      # 0 calls (file validation only)
python tests/test_ics_zip.py           # 0 calls (file validation only)
```
**When to use:** Testing the module you're actively modifying

#### Tier 3: Full Suite (6-7 API calls)
**Use ONLY before committing or when finishing work**
```powershell
# Complete validation - run ONCE at the end
.\run_tests.ps1

# Or manually:
python tests/test_api.py
python tests/test_extraction.py
python tests/test_combined_sessions.py
python tests/test_cache.py
python tests/test_ics_encoding.py
python tests/test_e2e.py
```
**When to use:** Before `git commit`, before `git push`, end of work session

**Development Workflow with Optimized Testing:**
```powershell
# 1. Start: Verify baseline
python tests/test_api.py          # 1 call - API working?

# 2. Code: Make targeted changes
# ... edit extractor.py ...

# 3. Test: Run relevant test only
python tests/test_extraction.py   # 1 call - does my change work?

# 4. Iterate: Fix issues
# ... fix bug ...
# WAIT 10 seconds (rate limit safety)
python tests/test_extraction.py   # May use cache - fast!

# 5. Finish: Full validation before commit
# WAIT 30 seconds
.\run_tests.ps1                   # 6-7 calls - everything works?

# 6. Commit if all pass
git add .
git commit -m "feat: improved extraction"
```

**Test Files Reference:**
- `tests/test_api.py` - **1 call** - API key validation (always run first)
- `tests/test_extraction.py` - **1 call** - Event extraction with real data
- `tests/test_combined_sessions.py` - **1 call** - Session combining logic
- `tests/test_cache.py` - **2-3 calls** - Cache hit/miss behavior
- `tests/test_ics_encoding.py` - **0 calls** - ICS file format validation
- `tests/test_ics_zip.py` - **0 calls** - ZIP packaging validation
- `tests/test_e2e.py` - **1 call** - End-to-end comprehensive test

**Golden Rules:**
- ✅ **DO:** Run single targeted tests during development
- ✅ **DO:** Wait 10+ seconds between API-calling test runs
- ✅ **DO:** Run full suite ONCE at the end before committing
- ❌ **DON'T:** Run `run_tests.ps1` repeatedly during development
- ❌ **DON'T:** Make rapid API calls (triggers rate limits)
- ❌ **DON'T:** Commit without running full suite at least once

**Test Requirements:**
- All tests must pass before committing
- New features require new tests
- Bug fixes require regression tests
- Test coverage for critical paths (extraction, export, validation)

### 2. Virtual Environment - Always
**NEVER install packages globally. ALWAYS use venv.**

```powershell
# Activate venv before any pip command
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Adding new dependency
pip install package-name
pip freeze > requirements.txt
```

### 3. Security - API Keys and Secrets
**NEVER commit secrets or show them in UI.**

**🔴 CRITICAL - NEVER EVER:**
- ❌ Put real API keys in documentation files
- ❌ Put real API keys in example files
- ❌ Put real API keys in code comments
- ❌ Put real API keys in README/guides
- ❌ Display API keys in UI (not even masked/truncated)
- ❌ Log API keys to console/files

**✅ ALWAYS:**
- ✅ Use placeholders in docs: "your-api-key-here" or "AIzaSyXXXX..."
- ✅ API keys ONLY in `.env` file (gitignored)
- ✅ Use environment variables only
- ✅ Verify `.env` is in `.gitignore`
- ✅ Template files use fake/example keys only

- API keys MUST be in `.env` file (gitignored)
- NEVER display API keys in UI (not even masked/truncated)
- Use environment variables only
- `.env` is plain text (standard practice for local dev)
- Protected by: File permissions + gitignore + localhost binding
- `.env.example` for templates (no real keys)
- Streamlit secrets for cloud deployment

**File checks before commit:**
```bash
# .env must be in .gitignore
# No API keys in code files
# No secrets in config.json
```

**Network Security:**
- App binds to `127.0.0.1` (localhost only)
- NOT accessible from network/internet
- See SECURITY.md for details

### 4. Code Architecture - Separation of Concerns

**Module Responsibilities:**
- `models.py` - Data structures only (dataclasses, enums)
- `extractor.py` - AI service layer (Gemini API)
- `rules_engine.py` - Business logic (pure functions)
- `calendar_exporter.py` - Export layer (file generation)
- `config_manager.py` - Configuration persistence
- `app.py` - UI layer only (Streamlit)

**Rules:**
- UI never talks directly to AI
- Business logic independent of UI
- Data models have no business logic
- Services are stateless where possible

### 5. Error Handling - Defensive Programming

**Always validate:**
- User input (empty, malformed, non-calendar text)
- AI responses (valid JSON, expected schema)
- File operations (permissions, existence)
- API responses (rate limits, errors)

**Example:**
```python
try:
    events = extractor.extract(text)
    if not events or len(events) == 0:
        raise ValueError("No events extracted - input may not be a calendar")
except ValueError as e:
    st.error(f"Invalid input: {e}")
except Exception as e:
    st.error(f"Extraction failed: {e}")
```

### 6. Data Validation - Type Safety

**Always use type hints:**
```python
def process_events(events: List[Event], config: Config) -> List[Event]:
    """Process events with configuration"""
    # Implementation
```

**Validate data models:**
- Required fields must exist
- Dates must be valid datetimes
- Enums must match defined values
- Locations must be in knowledge base

---

## Development Workflow

### Lessons Learned - Mandatory Documentation
**After EVERY task (fix, feature, refactor, docs, debugging session), record a lesson learned.**

**Purpose:**
- Build institutional knowledge over time
- Prevent repeating mistakes
- Share insights across development sessions
- Create a searchable history of "why we do X this way"

**When to Add an Entry:**
✅ After fixing a bug (what was the root cause?)
✅ After implementing a feature (what worked well? what was tricky?)
✅ After hitting a roadblock (what did you learn?)
✅ After discovering a better approach (what changed?)
✅ After API/library quirks (what behavior was unexpected?)
✅ After performance optimization (what was the insight?)
✅ After user feedback (what did we miss?)
✅ Even if nothing went wrong (proactive learnings count!)

**Rules:**
- Add ONE bullet per task in this file under the **Lessons Learned Log** section below
- Keep each entry 1-2 lines: _What went wrong/insight_ + _the prevention/improvement rule_
- If there was no issue, write a proactive rule (e.g., "Verify ICS encoding before iOS tests")
- Never include secrets, API keys, or user data
- Reference the affected area when relevant (module/test/feature)
- Use past tense for the lesson, imperative for prevention
- Be specific - "AI returned invalid JSON" not "something broke"

**Format:**
```
YYYY-MM-DD - [area] Lesson learned: <specific issue/insight>. Prevention: <actionable rule>.
```

**Examples:**
```
2026-02-01 - [api] Lesson learned: Free tier Gemini has 15 RPM limit, full test suite hit quota. Prevention: Space out test runs by 30+ seconds, use targeted tests during development.
2026-02-01 - [cache] Lesson learned: Cache wasn't being used for identical inputs. Prevention: Always verify cache hit rate after implementing caching features.
2026-02-01 - [ios] Lesson learned: iOS Calendar requires UTF-8 BOM and CRLF for file imports. Prevention: Test .ics files on actual iOS device before marking feature complete.
```

### Standard Workflow
```powershell
# 1. Pull latest
git pull

# 2. Activate venv
.\venv\Scripts\Activate.ps1

# 3. Run tests (baseline)
.\run_tests.ps1

# 4. Make changes
# ... code changes ...

# 5. Run tests (verify)
.\run_tests.ps1

# 6. If tests pass, commit
git add .
git commit -m "feat: descriptive message"
git push
```

### Quick Development Loop
```powershell
# Run tests + start app
.\dev.ps1
```

### Before Committing
- [ ] All tests pass
- [ ] No secrets in code
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Requirements.txt updated if needed

---

## Lessons Learned Log
**📚 Living history of project insights - update after every task!**

### Testing & Performance
- 2026-02-01 - [api] Lesson learned: Free tier Gemini has 15 RPM limit, running full test suite repeatedly hits quota errors. Prevention: Wait 30+ seconds between full suite runs, use targeted single tests during development.
- 2026-01-31 - [process] Lesson learned: Full test suites are slow mid-iteration. Prevention: Run only impacted tests during work, then run the full suite at the end.
- 2026-01-31 - [process] Lesson learned: Manual runs can leak sensitive output. Prevention: Avoid printing or sharing secret values in logs or UI.

### iOS Compatibility
- 2026-01-31 - [export] Lesson learned: iOS sharing can fail on strict ICS validation. Prevention: Always include METHOD and X-WR-TIMEZONE headers in ICS output.
- 2026-01-31 - [ios] Lesson learned: iOS Safari may not offer direct downloads for .ics files. Prevention: Offer a ZIP download option for saving via Files.

### Documentation & Code Quality
- 2026-02-01 - [docs] Lesson learned: Testing strategy wasn't optimized for API rate limits in free tier. Prevention: Document API call budget per test and recommended development workflow.
- 2026-01-31 - [docs] Lesson learned: Enforce the lessons-learned log update on every task. Prevention: Always add a log entry immediately after completing any change.
- 2026-01-31 - [docs] Lesson learned: Duplicate sections confuse readers. Prevention: Consolidate repeated content during documentation updates.
- 2026-01-31 - [cleanup] Lesson learned: Stale debug docs/tests create confusion. Prevention: Remove or archive obsolete troubleshooting assets after fixes land.

### UI/UX Design
- 2026-02-01 - [ui] Lesson learned: Wide layout (layout="wide") looks sparse on large monitors and cramped on mobile. Prevention: Use layout="centered" with max-width CSS for consistent readability.
- 2026-02-01 - [ui] Lesson learned: Multi-step export (select format → click export → download) adds friction. Prevention: Show all download options immediately after clicking Export, let user choose by clicking download button.
- 2026-02-01 - [ui] Lesson learned: 3-column layouts don't work well on mobile or tablet. Prevention: Use single-column or max 2-column layout with stacked sections for mobile.
- 2026-02-01 - [ui] Lesson learned: Sidebar settings should be minimal and collapsed by default. Prevention: Move rarely-used settings to sidebar expanders, keep main UI clean.
- 2026-02-01 - [ui] Lesson learned: Event list needs to be scannable at a glance. Prevention: Show key info (date, time, location) on single line, notes as caption below.

---

## Code Quality Standards

### 1. Naming Conventions
- Classes: `PascalCase` (Event, ConfigManager)
- Functions: `snake_case` (extract_events, apply_rules)
- Constants: `UPPER_SNAKE_CASE` (GEMINI_API_KEY, DEFAULT_TIMEZONE)
- Private: `_leading_underscore` (_build_prompt, _validate)

### 2. Documentation
**Every module must have:**
```python
"""
Module description

Key responsibilities:
- Responsibility 1
- Responsibility 2
"""
```

**Every public function must have:**
```python
def extract_events(text: str, config: Config) -> List[Event]:
    """
    Extract events from unstructured text
    
    Args:
        text: Raw schedule text (Chinese/English)
        config: Application configuration
        
    Returns:
        List of extracted events
        
    Raises:
        ValueError: If text is empty or invalid
        Exception: If AI extraction fails
    """
```

### 3. Function Length
- Maximum 50 lines per function
- If longer, extract helper functions
- Single responsibility principle

### 4. Imports
```python
# Standard library
import os
from datetime import datetime
from typing import List, Dict

# Third party
import streamlit as st
import pandas as pd

# Local
from models import Event, Config
from extractor import EventExtractor
```

---

## Business Rules - Swimming Schedule Specific

### 1. Training Session Rules
**CRITICAL: Underwater + Dryland = Single Continuous Session**

```
Input: "6~7:30pm 下水、7:30~8pm 陆上拉伸"
Output: Single event 6:00 PM - 8:00 PM (NOT two separate events)
```

**Rule: Never split sessions**
- If text mentions both underwater (下水) and dryland (陆上), create ONE event
- Start time = beginning of underwater
- End time = end of dryland
- Summary should indicate "Swim Practice" (not split into parts)

### 2. Location Rules
- Explicit mentions override defaults (e.g., "@ Regis")
- Weekday (Mon-Fri) → Regis (if no explicit location)
- Weekend (Sat-Sun) → Brandeis (if no explicit location)
- Special cases: Check for location changes mid-schedule

### 3. Event Validation
- Start time must be before end time
- Duration should be reasonable (0.5 - 4 hours typical)
- Past events generate warnings (not errors)
- Ambiguous events flagged for user review

---

## AI Prompt Engineering

### System Prompt Guidelines
1. **Provide clear context** - List all known locations
2. **Specify output format** - JSON schema
3. **Define rules explicitly** - Location defaults, session combining
4. **Handle ambiguity** - Ask AI to flag uncertain extractions
5. **Examples** - Show expected input/output patterns

### Response Validation
```python
# Always validate AI responses
response = model.generate_content(prompt)
try:
    data = json.loads(response.text)
    if "events" not in data:
        raise ValueError("Invalid response - no events array")
    if len(data["events"]) == 0:
        raise ValueError("No events extracted - check input")
except json.JSONDecodeError:
    raise ValueError("AI returned invalid JSON")
```

---

## Streamlit Best Practices

### 1. Session State
```python
# Initialize once
if 'config' not in st.session_state:
    st.session_state.config = load_config()

# Never mutate directly, always reassign
st.session_state.events = new_events
```

### 2. Performance
- Use `@st.cache_data` for expensive operations
- Avoid reloading config on every render
- Lazy load AI model

### 3. UI/UX
- Mobile-first design (centered layout)
- Clear error messages
- Loading indicators for long operations
- Confirmation for destructive actions

---

## Git Practices

### Commit Messages
```
feat: add event validation
fix: correct timezone handling
docs: update API key setup
test: add end-to-end test
refactor: extract prompt builder
chore: update dependencies
```

### Branch Strategy
- `main` - production ready
- `develop` - integration branch
- `feature/*` - new features
- `fix/*` - bug fixes

### Before Push
```powershell
# Run full test suite
.\run_tests.ps1

# Check for secrets
git diff | grep -i "api_key\|secret\|password"
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass
- [ ] No console.log or debug prints
- [ ] API key in secrets (not .env for cloud)
- [ ] requirements.txt up to date
- [ ] README.md reflects current state
- [ ] DEPLOYMENT.md has platform instructions

### Post-Deployment
- [ ] Smoke test on production URL
- [ ] Verify API key loaded correctly
- [ ] Test with sample schedule
- [ ] Check error handling works

---

## Common Pitfalls - Avoid These

### ❌ Don't Do This
```python
# Installing packages globally
pip install package  # NO!

# Showing API keys
st.write(f"API Key: {api_key}")  # NO!

# Skipping tests
# "It's just a small change, I don't need to test"  # NO!

# Mutating dataclasses
event.start_time = new_time  # NO! Create new instance

# Catching all exceptions silently
try:
    dangerous_operation()
except:
    pass  # NO! Always log errors
```

### ✅ Do This Instead
```python
# Use venv
.\venv\Scripts\Activate.ps1
pip install package

# Hide API keys
api_key = os.getenv("GEMINI_API_KEY")  # Never display

# Always test
.\run_tests.ps1

# Create new instances
event = Event(start_time=new_time, ...)

# Handle errors properly
try:
    dangerous_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

---

## File Structure Reference

```
calendar_import/
├── .github/
│   └── copilot-instructions.md  ← You are here
├── .streamlit/
│   ├── config.toml              ← UI config (dark theme)
│   └── secrets.toml.example     ← Secrets template
├── docs/                        ← Documentation folder
│   ├── README.md                ← Documentation index
│   ├── QUICKSTART.md            ← Desktop launcher guide
│   ├── LINUX_DEPLOYMENT.md      ← Linux deployment
│   ├── SECURITY.md              ← API key & network security
│   ├── TROUBLESHOOTING.md       ← Common issues
│   └── DEPLOYMENT.md            ← Cloud deployment
├── src/
│   ├── models.py                ← Data models + Config with model/host settings
│   ├── extractor.py             ← AI service (uses config.gemini_model)
│   ├── rules_engine.py          ← Business logic
│   ├── calendar_exporter.py     ← Export service
│   └── config_manager.py        ← Config persistence
├── tests/
│   ├── __init__.py              ← Package marker
│   ├── test_api.py              ← API validation
│   ├── test_extraction.py       ← Extraction tests
│   └── test_e2e.py              ← End-to-end tests
├── app.py                       ← Streamlit UI
├── .env                         ← API key (NEVER COMMIT) - plain text, gitignored
├── .env.example                 ← Template
├── .gitignore                   ← Must include .env
├── config.json                  ← App config (model, host, port, locations)
├── requirements.txt             ← Dependencies
├── dev.ps1                      ← Dev workflow script (network accessible)
├── run_tests.ps1                ← Test runner
├── restart_app.ps1              ← App restart (network accessible)
├── setup_firewall.ps1           ← Windows firewall setup
└── README.md                    ← Main documentation (root level only)

Desktop:
└── Start Swimming Calendar.bat  ← Desktop launcher (network accessible)
```

---

## Key Reminders

1. **Tests are mandatory** - No exceptions
2. **Venv always** - Global installs break reproducibility
3. **Secrets stay secret** - Never in code, never in UI
4. **Type hints everywhere** - Makes code self-documenting
5. **Business rules matter** - Don't split training sessions
6. **Validate everything** - User input, AI responses, file operations
7. **Document changes** - Update README, docstrings, comments

---

## Quick Reference Commands

```powershell
# Development
.\venv\Scripts\Activate.ps1      # Activate venv
.\dev.ps1                        # Test + run app
.\run_tests.ps1                  # Run all tests
.\restart_app.ps1                # Restart Streamlit

# Testing
python tests/test_api.py         # Test API key
python tests/test_extraction.py  # Test extraction
python tests/test_e2e.py         # End-to-end test

# Deployment
streamlit run app.py             # Run locally
docker build -t swim-cal .       # Docker build
```

---

**Remember: Quality over speed. Working code beats fast code.**
