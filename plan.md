# Modernization Plan v2 (Lean, Product-Focused)

> Date: 2026-02-27  
> Scope: staged execution in progress  
> Principle: keep what users care about stable; simplify internals without gold-plating.

## Execution Status (2026-02-27)

Overall status:
- Core product modernization complete (Stages B, C, D, E)
- App remains feature-equivalent for user workflows
- Remaining items are optional follow-ups, not blockers

Completed in this pass:
- Stage B (minimal settings surface): implemented
- Stage C (flow refactor): implemented
- Stage D (targeted cleanup): implemented
- Stage E (test modernization): implemented

Implemented changes:
- Added `src/settings.py` for major user/policy knobs only.
- Added `src/pipeline.py` for extract → rules orchestration.
- Moved AI edit service logic from UI into `EventExtractor.edit()`.
- Updated `app.py` to use service interfaces (`process_schedule`, `EventExtractor.edit`).
- Removed hardcoded year in extraction prompt (now dynamic current year).
- Centralized selected export/config/shared-calendar defaults in service modules.
- Added `default_event_title` persistence in `Config` and config files.
- Replaced print-based warnings with structured logging in service modules.
- Externalized app CSS into `static/style.css` and simplified `app.py` initialization.
- Migrated tests to `pytest` with shared fixtures and API markers.
- Updated `run_tests.ps1` to run non-API tests by default (`-Full` for all, `-ApiOnly` for API tests).

Validation strategy (quota-safe):
- Prioritize non-API tests first (`test_ics_encoding`, `test_ics_zip`, shared-calendar tests).
- Run API-calling tests only once at the end, spaced to avoid Gemini free-tier limits.

Deferred follow-ups (optional):
- Stage F (broader docs consolidation) can be done after pytest migration.

## 1) My Review of the Previous Plan

The prior plan is strong technically, but too broad for a “shrink and modernize” goal.

### What to keep
- Preserve current output as golden truth (especially extraction + ICS behavior).
- Move heavy logic out of `app.py`.
- Use staged migration with regression checks after each stage.
- Fix obvious drift risks (hardcoded year in prompt, duplicated defaults).

### What to scale back
- Do **not** centralize every hardcoded number/string.
- Do **not** force aggressive deletions (docs/modules) early.
- Do **not** optimize for LOC reduction as a primary KPI.

### Why
A professional “new house” refactor prioritizes:
1) stable external behavior,
2) clear system boundaries,
3) a small, explicit configuration surface,
4) gradual low-risk changes.

## 2) What We Should Centralize (and What We Shouldn’t)

### Centralize only major user-facing or policy knobs
These are the inputs users/admins reasonably care about and may want to change:

- `timezone`
- `default_event_title`
- default locations (weekday/weekend)
- built-in location catalog (name/address/default flags)
- AI model (`gemini_model`)
- host/port
- API retry policy (`max_attempts`, backoff factor)
- extraction policy knobs that affect output semantics:
  - minimum input length
  - inferred-text sentinel
  - current-year assumption strategy
- export policy knobs:
  - calendar display name
  - ICS method/timezone headers
  - default output filename

### Keep local implementation constants in-place
These do not need “global constants” unless reused across modules:
- CSS spacing/font sizes (`900px`, `1.8rem`, etc.)
- single-use formatting literals inside one function
- tiny UI display numbers (`text_area` heights) unless product wants them configurable

**Rule:** only elevate values that are either cross-module, behavior-critical, or user/policy-facing.

## 3) Golden Truth (Contract We Must Preserve)

### Extraction contract
- Combined underwater + dryland becomes one continuous session.
- Rest days (`休息`, `闭馆`) produce no events.
- Location defaults still apply when no explicit location is present.
- Event ordering and dedup behavior stays functionally equivalent.

### Export contract
- ICS must keep UTF-8 BOM, CRLF, `METHOD:PUBLISH`, timezone headers, and `DTSTAMP` behavior.
- ZIP export must preserve embedded ICS compatibility.

### Shared calendar contract
- Save/list/load/delete/stats semantics unchanged.
- Shared calendars remain usable without original source text.

### UI contract
- Keep current user flow intact:
  - Create New → Extract → Review/Edit → Export/Share
  - Use Shared → Load → Review/Edit → Export

## 4) Target Architecture (Minimal, Clean)

### Keep modules, improve boundaries
- Keep current module set (no big-bang restructure).
- Add only **two** new modules:
  - `src/settings.py` (or `src/constants.py`) for major knobs only.
  - `src/pipeline.py` for orchestrating extract → rules → post-process.

### Boundary cleanup
- `app.py`: UI and session orchestration only.
- `extractor.py`: AI interactions (extract + AI edit).
- `rules_engine.py`: deterministic business rules only.
- `calendar_exporter.py`: deterministic export only.

### Keep risk low
- Avoid deleting Google/Outlook export in first pass unless product confirms they are permanently out-of-scope.
- Avoid mass docs deletion in same phase as code refactor.

## 5) Staged Plan (Revised)

## Stage A — Baseline Lock (Golden Outputs First)

**Goal:** freeze behavior before structural changes.

Tasks:
1. Run current test suite and capture baseline output artifacts.
2. Add fixture snapshots for key ICS output (headers/encoding structure).
3. Record exact extraction expectations from existing tests as acceptance checklist.

Exit criteria:
- Existing tests pass unchanged.
- Baseline artifacts/checklist available for regression comparison.

Risk: Low

---

## Stage B — Introduce Minimal Settings Surface

**Goal:** centralize only major knobs.

Tasks:
1. Create `src/settings.py` with major user/policy knobs listed in section 2.
2. Replace duplicated defaults in `models.py` and `extractor.py` with settings imports.
3. Keep local-only constants local (do not over-extract).
4. Replace hardcoded year assumption with dynamic current-year strategy.

Exit criteria:
- No behavior change in tests.
- Duplicated business defaults removed.
- Major knobs readable in one file.

Risk: Low

---

## Stage C — Flow Refactor (Main Shrink Win)

**Goal:** simplify flow and function surface without changing UX.

Tasks:
1. Add `src/pipeline.py` (`process_schedule`) to own extract/rules sequencing.
2. Move AI edit logic from `app.py` into extractor service API.
3. Keep prompt behavior equivalent; preserve output schema.
4. Update `app.py` to call service interfaces only.

Exit criteria:
- `app.py` significantly slimmer and mostly declarative.
- Same end-to-end behavior and test results.

Risk: Medium (AI-edit path movement)

---

## Stage D — Targeted Cleanup (Not Big Rewrite)

**Goal:** remove high-noise/low-value complexity only.

Tasks:
1. Convert `print` warnings to structured logging.
2. Remove obvious dead/orphan code only after caller verification.
3. Keep non-critical refactors (e.g., `__all__`, stylistic rewrites) out unless directly valuable.
4. Optional: move large inline CSS out of `app.py` if it improves readability without style drift.

Exit criteria:
- Cleaner internals, same output.
- No accidental feature removal.

Risk: Low

---

## Stage E — Test Modernization (Pragmatic)

**Goal:** improve developer confidence while respecting API limits.

Tasks:
1. Introduce pytest gradually (start with non-API tests first).
2. Add markers (`api`, `slow`) for rate-limit-safe workflows.
3. Preserve existing test semantics; do not rewrite assertions aggressively.
4. Keep a one-command smoke path for contributors.

Exit criteria:
- Local developer loop supports quick non-API checks.
- API tests remain available but intentionally throttled.

Risk: Medium

---

## Stage F — Documentation Refresh (Selective)

**Goal:** remove confusion, not documentation volume for its own sake.

Tasks:
1. Consolidate overlapping setup instructions.
2. Fix broken references and stale file structure sections.
3. Document the new “settings surface” clearly so users know what inputs matter.
4. Keep specialized docs when they provide real user value.

Exit criteria:
- No broken links.
- Clear single source for setup + core workflow + configurable knobs.

Risk: Low

## 6) Migration Guardrails

- One stage = one PR if possible.
- No stage should mix major behavior changes with large doc moves.
- After each stage: run targeted tests first, then full suite with API-rate-limit spacing.
- If any stage changes extraction semantics, stop and reconcile against golden baseline before continuing.

## 7) Professional Design Principles for This Project

This is the “new house feeling” guideline:

1. **Small public surface:** UI calls a few stable service methods.
2. **Explicit contracts:** extraction output shape and ICS format are treated as contracts.
3. **Configuration with intent:** only expose knobs users/admins actually care about.
4. **Incremental modernization:** prefer safe, reversible moves over sweeping rewrites.
5. **Readable defaults:** one obvious place to understand system behavior.
6. **Operational empathy:** tests and workflows respect Gemini free-tier limits.

## 8) Suggested First Execution Order

If we start implementation next, do this order:
1. Stage A (baseline lock)
2. Stage B (minimal settings)
3. Stage C (flow refactor)
4. Stage D (targeted cleanup)
5. Stage E (pytest migration)
6. Stage F (docs refresh)

This gives the biggest clarity gain early, with lower regression risk.

---

End of revised plan.
