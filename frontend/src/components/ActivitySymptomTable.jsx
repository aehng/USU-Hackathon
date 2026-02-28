const confidenceBadgeClasses = (confidence) => {
  if (confidence == null) return "bg-slate-100 text-slate-700";
  if (confidence >= 0.8) return "bg-emerald-50 text-emerald-800";
  if (confidence >= 0.6) return "bg-amber-50 text-amber-800";
  return "bg-slate-100 text-slate-700";
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
            <tr className="bg-slate-100">
              <th className="border border-slate-200 px-3 py-2 text-left font-semibold text-slate-800">
                Activity
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-semibold text-slate-800">
                Symptom
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-semibold text-slate-800">
                Confidence
              </th>
              <th className="border border-slate-200 px-3 py-2 text-left font-semibold text-slate-800">
                Samples
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => {
              const pct = row.confidence != null ? Math.round(row.confidence * 100) : null;
              const label = confidenceLabel(row.confidence);
              return (
                <tr key={`${row.activity}-${row.symptom}-${idx}`} className="odd:bg-white even:bg-slate-50/60">
                  <td className="border border-slate-200 px-3 py-2 text-slate-800">
                    {row.activity}
                  </td>
                  <td className="border border-slate-200 px-3 py-2 text-slate-800">
                    {row.symptom}
                  </td>
                  <td className="border border-slate-200 px-3 py-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${confidenceBadgeClasses(
                        row.confidence,
                      )}`}
                    >
                      {pct != null ? `${pct}%` : "—"}
                      <span className="opacity-80">({label})</span>
                    </span>
                  </td>
                  <td className="border border-slate-200 px-3 py-2 text-slate-700">
                    {row.sample_size ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="mt-2 text-xs font-medium text-slate-600">
          Confidence is based on how often the activity and symptom appear together in your history. Higher % = stronger
          evidence of a link.
        </p>
      </div>
    </div>
  );
}

