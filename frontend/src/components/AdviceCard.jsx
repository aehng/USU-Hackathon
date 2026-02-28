export default function AdviceCard({ title, body, disclaimer }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-200">
            <span className="text-lg" aria-hidden>
              💡
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
              {title}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-700 dark:text-slate-200">
              {body}
            </p>
          </div>
        </div>
        {disclaimer && (
          <p className="text-xs leading-snug text-slate-500 dark:text-slate-400">
            {disclaimer}
          </p>
        )}
      </div>
    </section>
  );
}

