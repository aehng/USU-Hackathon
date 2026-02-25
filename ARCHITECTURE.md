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
    POST /api/log/quick
    (or guided start/finalize)
          |
[FastAPI Backend — Noah]
          |
    ┌─────┴──────┐
    |            |
    |       OpenAI API
    |       GPT-4o extraction
    |       Returns structured JSON
    |            |
    └─────┬──────┘
          |
    Write entry to DB
          |
[PostgreSQL Database — Clayton]
          |
    Clayton's analysis engine
    reads historical entries,
    computes correlations
          |
    GET /api/insights
          |
[FastAPI Backend — Noah]
          |
    Correlation stats → LLM insight prompt
    GPT-4o generates plain-English findings
          |
[React Dashboard — Max]
    Shows insight cards, charts,
    prediction, history
```

---

## How the Two Logging Modes Work

### Quick Log
```
User speaks → transcript → POST /api/log/quick → extraction → DB write → return tags → done
```
One round trip. Fast. No follow-up.

### Guided Log
```
User speaks
  → POST /api/log/guided/start
  → extraction + follow-up question generation
  → frontend shows question 1
  → user answers (voice or typed)
  → repeat for each question
  → POST /api/log/guided/finalize
    (original transcript + all Q&A pairs combined)
  → re-run extraction on combined text
  → DB write → done
```

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

Clayton's code reads historical entries and finds patterns.

**Trigger Correlation:**
- "Every time caffeine appears in an entry, does a headache appear within 24 hours?"
- Expressed as conditional probability: P(headache | caffeine logged yesterday)
- Compared against baseline: P(headache | no caffeine yesterday)
- If meaningfully higher → strong correlation

**Temporal Pattern:**
- Group entries by day of week + time of day
- Do symptoms cluster? Monday mornings = fatigue? Weekend evenings = headaches?

**Severity Trend:**
- Last 14 data points for a symptom
- Linear regression slope → improving, worsening, or stable

Clayton's `compute_all_stats()` bundles all of this into one JSON object that gets passed to Noah's insight prompt.

---

## How Insights Are Generated (Noah + Clayton)

```
Clayton's stats JSON
        ↓
Noah's LLM insight prompt
        ↓
GPT-4o converts statistics into
plain-English insight cards

Example:
stats: headache occurs after caffeine with 0.72 correlation, n=14
insight: "Your migraines are 72% more likely the day after logging caffeine — that's based on 14 instances in your history."
```

---

## The Demo User

Everyone uses the same hardcoded demo user ID for development:
`00000000-0000-0000-0000-000000000001`

Clayton inserts this user in `init.sql` so the DB always has it on startup. No auth needed during the hackathon.

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

### 7pm Friday — Noah + Clayton sync
- Agree on exact JSON shape extraction returns
- Agree on exact JSON shape `compute_all_stats()` returns
- Write both shapes in README

### 9pm Friday — First end-to-end test
- Eli speaks into mic → entry appears in DB
- Confirm this works before building anything else

### 11pm Friday — Full pipeline test
- Seeded data in DB → insights endpoint → insight cards visible on dashboard
