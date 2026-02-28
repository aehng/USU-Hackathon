import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import InsightCard from "./components/InsightCard.jsx";
import PredictionCard from "./components/PredictionCard.jsx";
import AdviceCard from "./components/AdviceCard.jsx";
import TriggerSymptomHeatmap from "./components/TriggerSymptomHeatmap.jsx";
import ActivitySymptomTable from "./components/ActivitySymptomTable.jsx";
import VoiceRecorder from "./components/VoiceRecorder.jsx";
import { API_BASE_URL, DEMO_USER_ID } from "./api/client.js";
import {
  MOCK_INSIGHTS,
  MOCK_STATS,
  NOT_ENOUGH_DATA_INSIGHTS,
  NOT_ENOUGH_DATA_STATS,
} from "./mock/dashboardData.js";

export default function Dashboard() {
  const [insights, setInsights] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [useMock, setUseMock] = useState(false); // Toggle to false when API is ready
  const [activeTab, setActiveTab] = useState("main"); // 'main' | 'guided' | 'quick'

  const buildBaseCandidates = () => {
    const candidates = [API_BASE_URL];
    try {
      const parsed = new URL(API_BASE_URL);
      if (parsed.port === "8001") {
        candidates.push(`${parsed.protocol}//${parsed.hostname}:8002`);
      }
    } catch {
      return candidates;
    }
    return [...new Set(candidates)];
  };

  const fetchJsonWithPortFallback = async (path) => {
    const bases = buildBaseCandidates();
    let lastError = null;

    for (const base of bases) {
      try {
        const res = await fetch(`${base}${path}`);
        if (!res.ok) {
          throw new Error(`Request failed (${res.status})`);
        }
        return await res.json();
      } catch (error) {
        lastError = error;
      }
    }

    throw lastError || new Error("Failed to fetch dashboard data");
  };

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
          const [insightsRes, statsRes] = await Promise.all([
            fetchJsonWithPortFallback(`/api/insights/${DEMO_USER_ID}`),
            fetchJsonWithPortFallback(`/api/stats/${DEMO_USER_ID}`),
          ]);
          setInsights(insightsRes);
          setStats(statsRes);
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
  const hasAdvice = insights?.advice && !notEnoughData;
  const hasSeverityData = stats?.severity_trends?.length > 0;
  const hasTriggerData = stats?.trigger_correlations?.length > 0;
  const hasHeatmapData = stats?.symptom_temporal_heatmap?.length > 0;
  const hasActivityCorrelationData = stats?.activity_symptom_correlations?.length > 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
          <p className="text-sm font-medium text-slate-800">
            Loading your insights…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-2xl border border-orange-200 bg-[#e4e4e4] shadow-md">
              <img
                src="/Screenshot 2026-02-28 011120.png"
                alt="FlairUp logo"
                className="h-9 w-9 object-contain"
              />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold tracking-tight text-slate-900">
                  FlairUp
                </span>
                <span className="text-xs font-extrabold uppercase tracking-wide text-orange-600">
                  VoiceHealth
                </span>
              </div>
              <p className="text-xs font-medium text-slate-600">
                Heart-first insights from your daily logs
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="font-medium text-slate-600">Data source</span>
            <div className="inline-flex rounded-full border border-slate-300 bg-slate-100 p-0.5 shadow-sm">
              <button
                type="button"
                onClick={() => setUseMock(true)}
                className={`px-2 py-1 rounded-full font-medium transition ${
                  useMock
                    ? "bg-orange-500 text-white shadow-sm"
                    : "bg-transparent text-slate-700"
                }`}
              >
                Demo
              </button>
              <button
                type="button"
                onClick={() => setUseMock(false)}
                className={`px-2 py-1 rounded-full font-medium transition ${
                  !useMock
                    ? "bg-orange-500 text-white shadow-sm"
                    : "bg-transparent text-slate-700"
                }`}
              >
                API
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-6 space-y-6">
        <div className="mb-4 flex justify-center">
          <nav className="inline-flex rounded-full border border-slate-200 bg-white p-1 text-xs font-medium shadow-sm">
            <button
              type="button"
              onClick={() => setActiveTab("main")}
              className={`px-3 py-1.5 rounded-full transition ${
                activeTab === "main" ? "bg-slate-900 text-white shadow-sm" : "text-slate-700"
              }`}
            >
              Main
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("guided")}
              className={`px-3 py-1.5 rounded-full transition ${
                activeTab === "guided" ? "bg-orange-500 text-white shadow-sm" : "text-slate-700"
              }`}
            >
              Guided log
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("quick")}
              className={`px-3 py-1.5 rounded-full transition ${
                activeTab === "quick" ? "bg-orange-100 text-orange-700 shadow-sm" : "text-slate-700"
              }`}
            >
              Quick log
            </button>
          </nav>
        </div>

        {activeTab === "main" && notEnoughData && (
          <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900 shadow-md">
            <p className="font-semibold">
              {insights?.message || stats?.message || "Not enough data yet."}
            </p>
            <p className="mt-1 text-sm font-medium text-amber-800">
              Log more entries to see patterns and predictions.
            </p>
          </div>
        )}

        {activeTab === "main" && hasPrediction && (
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

        {activeTab === "main" && hasAdvice && (
          <section aria-labelledby="advice-heading">
            <h2 id="advice-heading" className="mb-3 text-lg font-bold text-slate-900">
              LLM guidance
            </h2>
            <AdviceCard
              title={insights.advice.title}
              body={insights.advice.body}
              disclaimer={insights.advice.disclaimer}
            />
          </section>
        )}

        {activeTab === "main" && hasInsights && (
          <section aria-labelledby="insights-heading">
            <h2 id="insights-heading" className="mb-3 text-lg font-bold text-slate-900">
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

        {activeTab === "main" && hasSeverityData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
            <h2 className="mb-3 text-lg font-bold text-slate-900">
              Severity trend (last 7 days)
            </h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.severity_trends} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
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

        {activeTab === "main" && hasTriggerData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
            <h2 className="mb-3 text-lg font-bold text-slate-900">
              Top triggers
            </h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stats.trigger_correlations}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200" />
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

        {activeTab === "main" && hasHeatmapData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
            <h2 className="mb-3 text-lg font-bold text-slate-900">
              When do symptoms show up?
            </h2>
            <TriggerSymptomHeatmap data={stats.symptom_temporal_heatmap} />
          </section>
        )}

        {activeTab === "main" && hasActivityCorrelationData && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
            <h2 className="mb-3 text-lg font-bold text-slate-900">
              Activity ↔ symptom correlation
            </h2>
            <ActivitySymptomTable data={stats.activity_symptom_correlations} />
          </section>
        )}

        {activeTab === "guided" && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50">
            <h2 className="mb-2 text-lg font-bold text-slate-900">Guided log</h2>
            <p className="mb-4 text-sm text-slate-600">
              Start with a short description and we&apos;ll walk you through a few smart follow-up questions.
            </p>
            <VoiceRecorder mode="guided" />
          </section>
        )}

        {activeTab === "quick" && (
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50">
            <h2 className="mb-2 text-lg font-bold text-slate-900">Quick log</h2>
            <p className="mb-4 text-sm text-slate-600">
              Fire-and-forget: one fast voice or typed log when you&apos;re in a hurry.
            </p>
            <VoiceRecorder mode="quick" />
          </section>
        )}

        {activeTab === "main" &&
          !hasInsights &&
          !hasPrediction &&
          !hasAdvice &&
          !hasSeverityData &&
          !hasTriggerData &&
          !hasHeatmapData &&
          !hasActivityCorrelationData &&
          !notEnoughData && (
            <p className="text-center font-medium text-slate-700">
              No dashboard data available.
            </p>
          )}
      </main>
    </div>
  );
}
