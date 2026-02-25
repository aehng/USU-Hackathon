# 🏗️ Architecture Reference

How the pieces fit together. Read this if you're confused about how your work connects to someone else's.

---

## System Diagram

```
[User's Phone — Chrome Browser]
          |
    Speaks into mic
          |
    Web Speech API
    (runs in browser, free, no API needed)
          |
    Raw transcript text
          |
[React Frontend — Eli + Max]
          |
    POST /api/log/quick (or guided)
          |
[FastAPI Backend — Noah]
    ┌─────────────────┬──────────────────┐
    ↓                 ↓                  ↓
  Extract          Write entry        (ASYNC background task)
  to JSON          to DB                ↓
  return           immediately      Clayton computes stats
  immediately         |              ├→ analysis engine runs
                      |              ├→ LLM generates insights
                      |              └→ cache saved to DB
                      |                  (no blocking)
    ──────────────────┘
          |
[PostgreSQL Database — Clayton]
          |
    Entries stored
    Insights cached
          |
[React Frontend — GET /api/insights]
    Instant return from cache
    (no LLM call, no analysis lag)
          |
[Dashboard — Max]
    Shows insight cards, charts,
    prediction, history (fast load)
```

---

## How the Two Logging Modes Work

### Quick Log
```
User speaks
  → transcript
  → POST /api/log/quick
  → (sync) extract + DB write + return tags
  → (async background) compute stats → generate insights → cache
  → done
```
Fast. Single trip. Insights generated in background, cached for instant dashboard load.

### Guided Log
**Key innovation: Frontend holds extraction state. LLM only runs incremental update, not full re-extraction.**
```
User speaks
  → transcript
  → POST /api/log/guided/start
  → (sync) extract once + generate follow-up questions
  → return extracted JSON state + questions
  → frontend holds extracted state (prevents re-extraction)
  → show question 1
  → user answers (voice or typed)
  → repeat for each question
  → POST /api/log/guided/finalize
       (extracted JSON state + new Q&A answers)
  → (sync) LLM update prompt (fills blanks, doesn't re-extract)
       + DB write + return result
  → (async background) compute stats → generate insights → cache
  → done
```
Saves ~50% of LLM calls vs. full re-extraction.

---

## How LLM Extraction Works (Noah)

The voice transcript goes in. Structured JSON comes out.

**Input:** `"My head has been pounding since lunch, maybe a 7 out of 10, I had coffee this morning"`

**Output:**
```
symptoms: ["headache"]
severity: 7
potential_triggers: ["caffeine"]
mood: null
body_location: ["head"]
time_context: "afternoon"
notes: "started since lunch"
```

Noah uses `response_format: json_object` to guarantee valid JSON every time.

---

## How the Analysis Engine Works (Clayton)

Clayton's code reads historical entries and finds patterns. **All functions handle the edge case of < 5 entries gracefully.**

**Trigger Correlation:**
- "Every time caffeine appears in an entry, does a headache appear within 24 hours?"
- Expressed as conditional probability: P(headache | caffeine logged yesterday)
- Compared against baseline: P(headache | no caffeine yesterday)
- If meaningfully higher → strong correlation
- Only report correlations with at least 5 data points

**Temporal Pattern:**
- Group entries by day of week + time of day
- Do symptoms cluster? Monday mornings = fatigue? Weekend evenings = headaches?
- Requires minimum sample size

**Severity Trend:**
- Last 14 data points for a symptom
- Linear regression slope → improving, worsening, or stable
- Requires minimum samples to avoid false signals

**Edge Case:** If total entries < 5, return empty results or null. The backend wraps this in a circuit-breaker.

Clayton's `compute_all_stats()` bundles all of this into one JSON object (with field names that match Max's Recharts expectations, agreed at 7pm). This gets passed to Noah's insight generation prompt for LLM processing.

---

## How Insights Are Generated (Noah + Clayton) — Asynchronous

**When:** After every successful log (quick or guided finalize)
**How:** Background async task (does not block the log response)

```
1. Entry written to DB
   ↓
2. Spawn background task:
   Clayton's compute_all_stats(user_id)
        ↓
   Returns stats JSON:
   {
     "trigger_correlations": [...],
     "temporal_patterns": [...],
     "severity_trends": [...],
     "total_entries": N,
     "date_range_days": D
   }
        ↓
   If total_entries >= 5:
     Pass stats to Noah's LLM insight prompt
        ↓
     GPT-4o converts statistics into
     plain-English insight cards (3 insights + 1 prediction)
        ↓
     Save result to insights_cache table
   Else:
     Cache the "not enough data" message
        ↓
3. Next dashboard load: GET /api/insights
   Returns cached result instantly (no LLM, no analysis lag)

Example insight:
stats: headache occurs after caffeine with 0.72 correlation, n=14
insight: "Your migraines are 72% more likely the day after logging caffeine — that's based on 14 instances in your history."
```

---

## The Demo User

Everyone uses the same hardcoded demo user ID for development:
`00000000-0000-0000-0000-000000000001`

Clayton inserts this user in `init.sql` so the DB always has it on startup. No auth needed during the hackathon.

---

## Edge Case Handling: Insufficient Data

**Problem:** Testing with brand new user IDs (0 entries) or small samples can cause crashes or hallucinations.

**Solution:** Circuit-breaker logic in both endpoints.

If a user has fewer than 5 entries:

**`GET /api/insights/{user_id}` returns:**
```json
{
  "insights": [],
  "prediction": null,
  "message": "Not enough data yet. Keep logging to unlock insights!"
}
```

**`GET /api/stats/{user_id}` returns:**
```json
{
  "total_entries": 2,
  "message": "Minimum 5 entries needed for analysis.",
  "trigger_correlations": [],
  "temporal_patterns": [],
  "severity_trends": []
}
```

**Frontend handles this gracefully:**
- Dashboard shows the "not enough data" message prominently
- Charts are hidden or show empty states
- Encourages the user to log more entries
- No errors, no hallucinated false correlations

This is critical for demo robustness — if judges test with fresh user IDs, the app remains stable.

---

## Data Flow Summary

```
Voice → transcript → extraction → entry in DB
                                      ↓
                               analysis engine
                                      ↓
                               stats JSON
                                      ↓
                               LLM insight prompt
                                      ↓
                               insight cards + prediction
                                      ↓
                               dashboard
```

---

## Integration Checkpoints

### 7pm Friday — 3-way Noah + Clayton + Max sync
**All three people must be present.**

1. **Noah** finalizes extraction JSON shape
   - Drives Clayton's schema (what gets stored)
   - Drives insight LLM prompt input
   - Lock this in

2. **Clayton** finalizes `compute_all_stats()` output
   - **Must include field names that match Max's chart expectations**
   - Example: If Max's bar chart expects `{name: string, value: number}`, Clayton maps trigger output to that format
   - Otherwise charts break when plugged in
   - Lock this in

3. **Max** dictates his Recharts field expectations
   - Show Clayton the exact field names each chart needs
   - Severity trend: does it need `{date, severity}` or `{name, uv}`?
   - Triggers bar: does it need `{trigger, count}` or custom?
   - Lock this in

**Write all three agreed shapes in README before moving on. Do not change afterward.**

### 9pm Friday — First end-to-end test
- Eli speaks into mic → entry appears in DB
- Insights computation begins (async, in background)
- Confirm the log works before building anything else

### 11pm Friday — Full pipeline test
- Seeded data in DB → insights endpoint returns cached insights → insight cards visible on dashboard
- Async insight computation verified working
- Charts consume real `/api/stats` data and display correctly
