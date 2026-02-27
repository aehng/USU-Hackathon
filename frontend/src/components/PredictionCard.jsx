const riskStyles = {
  low: "border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-600",
  medium:
    "border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-600",
  high: "border-rose-500 bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200 dark:border-rose-600",
};

const riskLabels = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

export default function PredictionCard({ title, body, riskLevel = "medium" }) {
  const style = riskStyles[riskLevel] ?? riskStyles.medium;
  const label = riskLabels[riskLevel] ?? riskLevel;

  return (
    <section
      className={`rounded-xl border-2 p-4 shadow-sm ${style}`}
      aria-label="Prediction"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="font-bold text-lg">{title}</h2>
          <p className="mt-2 text-sm leading-relaxed opacity-90">{body}</p>
        </div>
        <span
          className="shrink-0 rounded-full px-2.5 py-1 text-xs font-medium uppercase"
          aria-label={`Risk level: ${label}`}
        >
          {label}
        </span>
      </div>
    </section>
  );
}
