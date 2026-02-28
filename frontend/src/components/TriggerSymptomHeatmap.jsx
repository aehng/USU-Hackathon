import { useMemo } from "react";

/**
 * Builds a trigger × symptom heatmap from an array of { trigger, symptom, score }.
 * Rows = triggers, columns = symptoms. Score 0–1 maps to color intensity.
 */
export default function TriggerSymptomHeatmap({ data }) {
  const { triggers, symptoms, grid } = useMemo(() => {
    if (!data?.length) return { triggers: [], symptoms: [], grid: new Map() };

    const triggerSet = new Set();
    const symptomSet = new Set();
    const key = (t, s) => `${t}\0${s}`;
    const gridMap = new Map();

    for (const { trigger, symptom, score } of data) {
      triggerSet.add(trigger);
      symptomSet.add(symptom);
      gridMap.set(key(trigger, symptom), typeof score === "number" ? score : 0);
    }

    const triggers = Array.from(triggerSet).sort();
    const symptoms = Array.from(symptomSet).sort();
    return { triggers, symptoms, grid: gridMap };
  }, [data]);

  if (triggers.length === 0 || symptoms.length === 0) return null;

  const getCellColor = (score) => {
    if (score == null || Number.isNaN(score)) return "bg-slate-100 dark:bg-slate-700";
    const t = Math.max(0, Math.min(1, score));
    // Violet scale: light (low) -> dark (high)
    if (t < 0.25) return "bg-violet-100 dark:bg-violet-900/40";
    if (t < 0.5) return "bg-violet-200 dark:bg-violet-800/50";
    if (t < 0.75) return "bg-violet-400 dark:bg-violet-600";
    return "bg-violet-600 dark:bg-violet-500 text-white";
  };

  const key = (t, s) => `${t}\0${s}`;

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-0">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="border border-slate-200 bg-slate-50 px-2 py-1.5 text-left font-medium text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300">
                Trigger
              </th>
              {symptoms.map((s) => (
                <th
                  key={s}
                  className="border border-slate-200 bg-slate-50 px-2 py-1.5 font-medium text-slate-600 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
                >
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {triggers.map((t) => (
              <tr key={t}>
                <td className="whitespace-nowrap border border-slate-200 bg-slate-50 px-2 py-1.5 font-medium text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200">
                  {t}
                </td>
                {symptoms.map((s) => {
                  const score = grid.get(key(t, s));
                  const pct = score != null ? Math.round(score * 100) : null;
                  return (
                    <td
                      key={s}
                      className={`border border-slate-200 px-2 py-1.5 text-center dark:border-slate-600 ${getCellColor(score)}`}
                      title={pct != null ? `${t} → ${s}: ${pct}% correlation` : ""}
                    >
                      {pct != null ? `${pct}%` : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Higher % = stronger correlation between trigger and symptom.
        </p>
      </div>
    </div>
  );
}
