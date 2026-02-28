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
  // Heatmap: trigger × symptom correlation (score 0–1)
  trigger_symptom_correlations: [
    { trigger: "Caffeine", symptom: "Headache", score: 0.72 },
    { trigger: "Caffeine", symptom: "Fatigue", score: 0.35 },
    { trigger: "Poor sleep", symptom: "Headache", score: 0.41 },
    { trigger: "Poor sleep", symptom: "Fatigue", score: 0.82 },
    { trigger: "Poor sleep", symptom: "Stomach ache", score: 0.28 },
    { trigger: "Stress", symptom: "Headache", score: 0.58 },
    { trigger: "Stress", symptom: "Fatigue", score: 0.44 },
    { trigger: "Stress", symptom: "Stomach ache", score: 0.67 },
    { trigger: "Alcohol", symptom: "Headache", score: 0.85 },
    { trigger: "Alcohol", symptom: "Fatigue", score: 0.52 },
    { trigger: "Skipped meals", symptom: "Headache", score: 0.31 },
    { trigger: "Skipped meals", symptom: "Stomach ache", score: 0.61 },
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
  trigger_symptom_correlations: [],
};
