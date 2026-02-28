import { useMemo, useState } from "react";

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const TIME_ORDER = ["morning", "afternoon", "evening", "night"];

/**
 * Heatmap: X = days, Y = time of day. Dropdown selects which symptom to show.
 * Data: array of { symptom, day, time_of_day, value }.
 */
export default function TriggerSymptomHeatmap({ data }) {
  const { symptoms, gridBySymptom } = useMemo(() => {
    if (!data?.length) return { symptoms: [], gridBySymptom: new Map() };

    const symptomSet = new Set();
    const key = (symptom, day, time) => `${symptom}\0${day}\0${time}`;
    const gridMap = new Map();

    for (const { symptom, day, time_of_day, value } of data) {
      symptomSet.add(symptom);
      gridMap.set(key(symptom, day, time_of_day), typeof value === "number" ? value : 0);
    }

    const symptoms = Array.from(symptomSet).sort();
    return { symptoms, gridBySymptom: gridMap };
  }, [data]);

  const [selectedSymptom, setSelectedSymptom] = useState(symptoms[0] ?? "");

  const getCellValue = (day, time) => {
    if (!selectedSymptom) return null;
    return gridBySymptom.get(`${selectedSymptom}\0${day}\0${time}`) ?? null;
  };

  const getCellColor = (value) => {
    if (value == null || Number.isNaN(value)) return "bg-slate-100";
    if (value === 0) return "bg-slate-100";
    if (value <= 2) return "bg-violet-100";
    if (value <= 4) return "bg-violet-200";
    if (value <= 6) return "bg-violet-400";
    return "bg-violet-600 text-white";
  };

  if (symptoms.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="heatmap-symptom" className="text-sm font-semibold text-slate-800">
          Symptom:
        </label>
        <select
          id="heatmap-symptom"
          value={selectedSymptom}
          onChange={(e) => setSelectedSymptom(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-800 shadow-sm focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
        >
          {symptoms.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-block min-w-0">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="border border-slate-200 bg-slate-100 px-2 py-1.5 text-left font-semibold text-slate-800">
                  Time
                </th>
                {DAY_ORDER.map((day) => (
                  <th
                    key={day}
                    className="border border-slate-200 bg-slate-100 px-2 py-1.5 font-semibold text-slate-800"
                  >
                    {day.slice(0, 3)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TIME_ORDER.map((time) => (
                <tr key={time}>
                  <td className="whitespace-nowrap border border-slate-200 bg-slate-100 px-2 py-1.5 font-semibold capitalize text-slate-800">
                    {time}
                  </td>
                  {DAY_ORDER.map((day) => {
                    const value = getCellValue(day, time);
                    return (
                      <td
                        key={day}
                        className={`min-w-[2.5rem] border border-slate-200 px-2 py-1.5 text-center ${getCellColor(value)}`}
                        title={
                          value != null
                            ? `${selectedSymptom}: ${day} ${time}, count ${value}`
                            : ""
                        }
                      >
                        {value != null ? value : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-xs font-medium text-slate-600">
        Frequency of &quot;{selectedSymptom}&quot; by day and time of day. Darker = more often logged.
      </p>
    </div>
  );
}
