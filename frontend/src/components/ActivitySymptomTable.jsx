const confidenceBadgeClasses = (confidence) => {
  if (confidence == null) return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200";
  if (confidence >= 0.8) {
    return "bg-emerald-50 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200";
  }
  if (confidence >= 0.6) {
    return "bg-amber-50 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200";
  }
  return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200";
};

const confidenceLabel = (confidence) => {
  if (confidence == null) return "Unknown";
  if (confidence >= 0.8) return "High";
  if (confidence >= 0.6) return "Medium";
  return "Low";
};

export default function ActivitySymptomTable({ data }) {
  if (!data?.length) return null;

  const sorted = [...data].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full align-middle">
        <table className="min-w-full border-collapse text-sm">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800">
              <th className="border border-slate-200 px-3 py-2 text-left font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300">
                Activity
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300">
                Symptom
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300">
                Confidence
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-medium text-slate-600 dark:border-slate-700 dark:text-slate-300">
                Samples
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => {
              const pct = row.confidence != null ? Math.round(row.confidence * 100) : null;
              const label = confidenceLabel(row.confidence);
              return (
                <tr key={`${row.activity}-${row.symptom}-${idx}`} className="odd:bg-white even:bg-slate-50/60 dark:odd:bg-slate-900 dark:even:bg-slate-900/60">
                  <td className="border border-slate-200 px-3 py-2 text-slate-800 dark:border-slate-700 dark:text-slate-100">
                    {row.activity}
                  </td>
                  <td className="border border-slate-200 px-3 py-2 text-slate-800 dark:border-slate-700 dark:text-slate-100">
                    {row.symptom}
                  </td>
                  <td className="border border-slate-200 px-3 py-2 dark:border-slate-700">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${confidenceBadgeClasses(
                        row.confidence,
                      )}`}
                    >
                      {pct != null ? `${pct}%` : "—"}
                      <span className="opacity-80">({label})</span>
                    </span>
                  </td>
                  <td className="border border-slate-200 px-3 py-2 text-slate-700 dark:border-slate-700 dark:text-slate-200">
                    {row.sample_size ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Confidence is based on how often the activity and symptom appear together in your history. Higher % = stronger
          evidence of a link.
        </p>
      </div>
    </div>
  );
}

