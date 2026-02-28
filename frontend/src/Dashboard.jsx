import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import InsightCard from "./components/InsightCard.jsx";
import PredictionCard from "./components/PredictionCard.jsx";
import { API_BASE_URL } from "./api/client.js";
import {
  MOCK_INSIGHTS,
  MOCK_STATS,
  NOT_ENOUGH_DATA_INSIGHTS,
  NOT_ENOUGH_DATA_STATS,
} from "./mock/dashboardData.js";

const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

const CHART_COLORS = [
  "#0ea5e9", // sky-500
  "#8b5cf6", // violet-500
  "#ec4899", // pink-500
  "#f59e0b", // amber-500
  "#10b981", // emerald-500
];

export default function Dashboard() {
  const [insights, setInsights] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [useMock, setUseMock] = useState(false); // Toggle to false when API is ready

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      if (useMock) {
        // Simulate network delay
        await new Promise((r) => setTimeout(r, 400));
        setInsights(MOCK_INSIGHTS);
        setStats(MOCK_STATS);
      } else {
        try {
          const base = API_BASE_URL;
          const [insightsRes, statsRes] = await Promise.all([
            fetch(`${base}/api/insights/${DEMO_USER_ID}`),
            fetch(`${base}/api/stats/${DEMO_USER_ID}`),
          ]);
          const insightsData = await insightsRes.json();
          const statsData = await statsRes.json();
          setInsights(insightsData);
          setStats(statsData);
        } catch (err) {
          console.error(err);
          setInsights(NOT_ENOUGH_DATA_INSIGHTS);
          setStats(NOT_ENOUGH_DATA_STATS);
        }
      }
      setLoading(false);
    }
    fetchData();
  }, [useMock]);

  const notEnoughData =
    insights?.message ||
    stats?.message ||
    (stats && stats.total_entries != null && stats.total_entries < 5);
  const hasInsights = insights?.insights?.length > 0;
  const hasPrediction = insights?.prediction && !notEnoughData;
  const hasSeverityData = stats?.severity_trends?.length > 0;
  const hasTriggerData = stats?.trigger_correlations?.length > 0;
  const hasSymptomData = stats?.symptom_frequency?.length > 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Loading your insights…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-700 dark:bg-slate-900/95">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            VoiceHealth Tracker
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Your health insights at a glance
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 space-y-6">
        {notEnoughData && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
            <p className="font-medium">
              {insights?.message || stats?.message || "Not enough data yet."}
            </p>
            <p className="mt-1 text-sm opacity-90">
              Log more entries to see patterns and predictions.
            </p>
          </div>
        )}

        {hasPrediction && (
          <section aria-labelledby="prediction-heading">
            <h2 id="prediction-heading" className="sr-only">
              Prediction
            </h2>
            <PredictionCard
              title={insights.prediction.title}
              body={insights.prediction.body}
              riskLevel={insights.prediction.riskLevel}
            />
          </section>
        )}

        {hasInsights && (
          <section aria-labelledby="insights-heading">
            <h2 id="insights-heading" className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-200">
              Discovered patterns
            </h2>
            <ul className="space-y-3">
              {insights.insights.map((item) => (
                <li key={item.id}>
                  <InsightCard
                    title={item.title}
                    body={item.body}
                    icon={item.icon}
                  />
                </li>
              ))}
            </ul>
          </section>
        )}

        {hasSeverityData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <h2 className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-200">
              Severity trend (last 7 days)
            </h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.severity_trends} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-600" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(v) => v.slice(5)}
                    stroke="currentColor"
                    className="text-slate-500"
                  />
                  <YAxis
                    domain={[0, 10]}
                    tick={{ fontSize: 12 }}
                    stroke="currentColor"
                    className="text-slate-500"
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "8px",
                      border: "1px solid var(--tw-border-color)",
                    }}
                    formatter={(value) => [`${value}/10`, "Severity"]}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Line
                    type="monotone"
                    dataKey="severity"
                    stroke="#0ea5e9"
                    strokeWidth={2}
                    dot={{ fill: "#0ea5e9", r: 4 }}
                    name="Severity"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {hasTriggerData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <h2 className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-200">
              Top triggers
            </h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stats.trigger_correlations}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-600" />
                  <XAxis type="number" tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate-500" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={90}
                    tick={{ fontSize: 12 }}
                    stroke="currentColor"
                    className="text-slate-500"
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "8px",
                      border: "1px solid var(--tw-border-color)",
                    }}
                  />
                  <Bar dataKey="value" fill="#8b5cf6" name="Count" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {hasSymptomData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
            <h2 className="mb-3 text-lg font-semibold text-slate-800 dark:text-slate-200">
              Symptom breakdown
            </h2>
            <div className="mx-auto h-64 w-full max-w-xs">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.symptom_frequency}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {stats.symptom_frequency.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: "8px",
                      border: "1px solid var(--tw-border-color)",
                    }}
                    formatter={(value, name) => [value, name]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </section>
        )}

        {!hasInsights && !hasPrediction && !hasSeverityData && !hasTriggerData && !hasSymptomData && !notEnoughData && (
          <p className="text-center text-slate-500 dark:text-slate-400">
            No dashboard data available.
          </p>
        )}
      </main>
    </div>
  );
}
