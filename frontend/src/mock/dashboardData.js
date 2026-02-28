/**
 * Mock dashboard data for VoiceHealth Tracker.
 * Shapes match Recharts expectations and API contract.
 */

export const MOCK_INSIGHTS = {
  insights: [
    {
      id: "1",
      title: "Caffeine & headaches",
      body: "Your migraines are 72% more likely the day after logging caffeine — based on 14 instances in your history.",
      icon: "☕",
    },
    {
      id: "2",
      title: "Sleep and fatigue",
      body: "Poor sleep logged the night before correlates with next-morning fatigue in about 80% of entries.",
      icon: "😴",
    },
    {
      id: "3",
      title: "Stress and stomach",
      body: "Stress appears before stomach discomfort same-day in roughly 65% of your logs.",
      icon: "😤",
    },
  ],
  prediction: {
    title: "Heads up",
    body: "Based on your recent logs (caffeine yesterday, low sleep), you may be at higher risk for a headache today.",
    riskLevel: "medium", // "low" | "medium" | "high"
  },
  message: null,
};

export const MOCK_STATS = {
  total_entries: 42,
  date_range_days: 30,
  message: null,
  // Severity trend — LineChart: { date, severity }
  severity_trends: [
    { date: "2026-02-21", severity: 5 },
    { date: "2026-02-22", severity: 6 },
    { date: "2026-02-23", severity: 4 },
    { date: "2026-02-24", severity: 7 },
    { date: "2026-02-25", severity: 6 },
    { date: "2026-02-26", severity: 5 },
    { date: "2026-02-27", severity: 6 },
  ],
  // Top triggers — BarChart: { name, value } (horizontal: Y=name, X=value)
  trigger_correlations: [
    { name: "Caffeine", value: 14 },
    { name: "Poor sleep", value: 12 },
    { name: "Stress", value: 10 },
    { name: "Alcohol", value: 8 },
    { name: "Skipped meals", value: 5 },
  ],
  // Symptom breakdown — Pie/Donut: { name, value }
  symptom_frequency: [
    { name: "Headache", value: 18 },
    { name: "Fatigue", value: 14 },
    { name: "Stomach ache", value: 9 },
    { name: "Joint pain", value: 6 },
    { name: "Other", value: 4 },
  ],
  // Heatmap: day (x) × time of day (y), filter by symptom. One row per (symptom, day, time_of_day).
  symptom_temporal_heatmap: [
    { symptom: "Headache", day: "Monday", time_of_day: "morning", value: 2 },
    { symptom: "Headache", day: "Monday", time_of_day: "afternoon", value: 5 },
    { symptom: "Headache", day: "Monday", time_of_day: "evening", value: 3 },
    { symptom: "Headache", day: "Tuesday", time_of_day: "morning", value: 4 },
    { symptom: "Headache", day: "Tuesday", time_of_day: "afternoon", value: 2 },
    { symptom: "Headache", day: "Wednesday", time_of_day: "morning", value: 6 },
    { symptom: "Headache", day: "Wednesday", time_of_day: "evening", value: 4 },
    { symptom: "Headache", day: "Thursday", time_of_day: "afternoon", value: 5 },
    { symptom: "Headache", day: "Friday", time_of_day: "evening", value: 7 },
    { symptom: "Headache", day: "Saturday", time_of_day: "morning", value: 3 },
    { symptom: "Headache", day: "Sunday", time_of_day: "afternoon", value: 2 },
    { symptom: "Fatigue", day: "Monday", time_of_day: "morning", value: 8 },
    { symptom: "Fatigue", day: "Monday", time_of_day: "afternoon", value: 4 },
    { symptom: "Fatigue", day: "Tuesday", time_of_day: "morning", value: 6 },
    { symptom: "Fatigue", day: "Wednesday", time_of_day: "morning", value: 7 },
    { symptom: "Fatigue", day: "Thursday", time_of_day: "morning", value: 5 },
    { symptom: "Fatigue", day: "Friday", time_of_day: "evening", value: 3 },
    { symptom: "Stomach ache", day: "Monday", time_of_day: "afternoon", value: 4 },
    { symptom: "Stomach ache", day: "Tuesday", time_of_day: "evening", value: 3 },
    { symptom: "Stomach ache", day: "Wednesday", time_of_day: "afternoon", value: 5 },
    { symptom: "Stomach ache", day: "Thursday", time_of_day: "morning", value: 2 },
    { symptom: "Joint pain", day: "Monday", time_of_day: "evening", value: 2 },
    { symptom: "Joint pain", day: "Saturday", time_of_day: "afternoon", value: 3 },
  ],
};

/** "Not enough data" response shape for testing empty state */
export const NOT_ENOUGH_DATA_INSIGHTS = {
  insights: [],
  prediction: null,
  message: "Not enough data yet. Keep logging to unlock insights!",
};

export const NOT_ENOUGH_DATA_STATS = {
  total_entries: 2,
  message: "Minimum 5 entries needed for analysis.",
  trigger_correlations: [],
  severity_trends: [],
  symptom_frequency: [],
  symptom_temporal_heatmap: [],
};
