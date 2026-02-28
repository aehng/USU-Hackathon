export default function InsightCard({ title, body, icon }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="flex gap-3">
        <span className="text-2xl" aria-hidden>
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-slate-900 md:text-base md:font-bold">
            {title}
          </h3>
          <p className="mt-1 text-sm leading-relaxed text-slate-800">
            {body}
          </p>
        </div>
      </div>
    </article>
  );
}
