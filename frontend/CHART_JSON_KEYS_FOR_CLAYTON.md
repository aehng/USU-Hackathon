# Chart JSON Keys — For Clayton (GET /api/stats/{user_id})

Max’s dashboard charts expect these **exact** keys. Map your analysis output to these names.

---

## 1. Severity trend (LineChart)

**Top-level key:** `severity_trends`  
**Type:** array of objects

| Key        | Type   | Notes                          |
|-----------|--------|---------------------------------|
| `date`    | string | ISO date, e.g. `"2026-02-25"`  |
| `severity`| number | 1–10                            |

**Example:**
```json
"severity_trends": [
  { "date": "2026-02-21", "severity": 5 },
  { "date": "2026-02-22", "severity": 6 }
]
```

---

## 2. Top triggers (horizontal BarChart)

**Top-level key:** `trigger_correlations`  
**Type:** array of objects

| Key    | Type   | Notes              |
|--------|--------|--------------------|
| `name` | string | Trigger label      |
| `value`| number | Count / frequency  |

**Example:**
```json
"trigger_correlations": [
  { "name": "Caffeine", "value": 14 },
  { "name": "Poor sleep", "value": 12 }
]
```

---

## 3. Symptom breakdown (Donut/PieChart)

**Top-level key:** `symptom_frequency`  
**Type:** array of objects

| Key    | Type   | Notes              |
|--------|--------|--------------------|
| `name` | string | Symptom label      |
| `value`| number | Count / frequency  |

**Example:**
```json
"symptom_frequency": [
  { "name": "Headache", "value": 18 },
  { "name": "Fatigue", "value": 14 }
]
```

---

## 4. Symptom heatmap (day × time of day)

**Top-level key:** `symptom_temporal_heatmap`  
**Type:** array of objects. One entry per (symptom, day, time_of_day) with a frequency/count. Dashboard shows one symptom at a time via dropdown; X axis = day, Y axis = time of day.

| Key           | Type   | Notes                                      |
|---------------|--------|--------------------------------------------|
| `symptom`     | string | Symptom name (used in dropdown)            |
| `day`         | string | Day of week: Monday … Sunday               |
| `time_of_day` | string | One of: morning, afternoon, evening, night |
| `value`       | number | Frequency/count for that cell              |

**Example:**
```json
"symptom_temporal_heatmap": [
  { "symptom": "Headache", "day": "Monday", "time_of_day": "morning", "value": 2 },
  { "symptom": "Headache", "day": "Monday", "time_of_day": "afternoon", "value": 5 },
  { "symptom": "Fatigue", "day": "Monday", "time_of_day": "morning", "value": 8 }
]
```

---

## 5. Root-level keys on stats response

The dashboard also reads these on the stats payload:

| Key             | Type   | Used for                                  |
|-----------------|--------|-------------------------------------------|
| `total_entries` | number | “Not enough data” when &lt; 5             |
| `message`       | string | Optional “not enough data” message        |

---

## Summary — exact keys

- **severity_trends** → `[{ "date", "severity" }, ...]`
- **trigger_correlations** → `[{ "name", "value" }, ...]`
- **symptom_temporal_heatmap** → `[{ "symptom", "day", "time_of_day", "value" }, ...]` (day × time heatmap, symptom dropdown)
- **symptom_frequency** → `[{ "name", "value" }, ...]`

Spelling and key names must match exactly or the charts will be empty.
