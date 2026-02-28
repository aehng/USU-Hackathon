export default function AdviceCard({ title, body, disclaimer }) {
  return (
    <section className="rounded-xl border border-orange-100 bg-gradient-to-br from-orange-50 via-white to-amber-50 p-4 shadow-md shadow-orange-50 hover:shadow-lg hover:-translate-y-0.5 transition-all">
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-orange-500 text-white shadow-md">
            <span className="text-lg" aria-hidden>
              💡
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-base font-bold text-slate-900">
              {title}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-800">
              {body}
            </p>
          </div>
        </div>
        {disclaimer && (
          <p className="text-xs leading-snug text-slate-600">
            {disclaimer}
          </p>
        )}
      </div>
    </section>
  );
}

