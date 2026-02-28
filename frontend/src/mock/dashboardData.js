/**
 * Mock dashboard data for VoiceHealth Tracker.
 * Demo data is derived from DEMO_LOG_ENTRIES (voice-health logs).
 */

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

const TIME_CONTEXT_TO_PERIOD = {
  Morning: "morning",
  "All day": "afternoon",
  Evening: "evening",
  Night: "night",
  Afternoon: "afternoon",
  "Post-gym": "afternoon",
  "Post-dinner": "evening",
  Now: "afternoon",
};

/** Raw demo log entries (voice health). */
export const DEMO_LOG_ENTRIES = [
  { date: "2026-01-30", symptoms: ["Hoarseness"], severity: 2, potential_triggers: ["Cold Weather"], mood: "Good", body_location: ["Throat"], time_context: "Morning", notes: "Slight raspiness after waking up." },
  { date: "2026-01-31", symptoms: ["Hoarseness", "Dryness"], severity: 3, potential_triggers: ["Coffee"], mood: "Fine", body_location: ["Throat"], time_context: "All day", notes: "Need to drink more water." },
  { date: "2026-02-01", symptoms: ["Sore Throat"], severity: 4, potential_triggers: ["Dust"], mood: "Tired", body_location: ["Throat"], time_context: "Evening", notes: "Felt a scratchy sensation during work." },
  { date: "2026-02-02", symptoms: ["Sore Throat", "Cough"], severity: 5, potential_triggers: ["Pollutants"], mood: "Anxious", body_location: ["Throat", "Chest"], time_context: "Night", notes: "Coughing started late." },
  { date: "2026-02-03", symptoms: ["Cough", "Breathiness"], severity: 6, potential_triggers: ["Exercise"], mood: "Frustrated", body_location: ["Chest"], time_context: "Post-gym", notes: "Struggled to finish my sentences." },
  { date: "2026-02-04", symptoms: ["Loss of Voice"], severity: 8, potential_triggers: ["Public Speaking"], mood: "Stressed", body_location: ["Larynx"], time_context: "Afternoon", notes: "Completely lost my voice during the meeting." },
  { date: "2026-02-05", symptoms: ["Pain", "Hoarseness"], severity: 9, potential_triggers: ["Lack of Rest"], mood: "Low", body_location: ["Throat"], time_context: "Morning", notes: "Extremely painful to swallow." },
  { date: "2026-02-06", symptoms: ["Pain", "Dryness"], severity: 7, potential_triggers: ["Dairy"], mood: "Better", body_location: ["Throat"], time_context: "All day", notes: "Resting my voice today." },
  { date: "2026-02-07", symptoms: ["Hoarseness"], severity: 5, potential_triggers: null, mood: "Optimistic", body_location: ["Throat"], time_context: "Afternoon", notes: "Voice is slowly returning." },
  { date: "2026-02-08", symptoms: ["Dryness"], severity: 3, potential_triggers: ["Air Conditioning"], mood: "Good", body_location: ["Throat"], time_context: "Night", notes: "Using a humidifier now." },
  { date: "2026-02-09", symptoms: ["Hoarseness"], severity: 4, potential_triggers: ["Stress"], mood: "Busy", body_location: ["Throat"], time_context: "Evening", notes: "Stress-induced tension in neck." },
  { date: "2026-02-10", symptoms: ["Sore Throat", "Pain"], severity: 6, potential_triggers: ["Spicy Food"], mood: "Irritated", body_location: ["Throat", "Esophagus"], time_context: "Post-dinner", notes: "Acid reflux making it worse." },
  { date: "2026-02-11", symptoms: ["Cough", "Hoarseness"], severity: 8, potential_triggers: ["Allergens"], mood: "Exhausted", body_location: ["Chest", "Throat"], time_context: "Morning", notes: "Heavy coughing fits." },
  { date: "2026-02-12", symptoms: ["Loss of Voice", "Pain"], severity: 10, potential_triggers: ["Shouting"], mood: "Upset", body_location: ["Larynx"], time_context: "Night", notes: "Total vocal failure after the game." },
  { date: "2026-02-13", symptoms: ["Pain"], severity: 7, potential_triggers: null, mood: "Quiet", body_location: ["Throat"], time_context: "All day", notes: "Complete vocal rest ordered." },
  { date: "2026-02-14", symptoms: ["Dryness"], severity: 5, potential_triggers: ["Alcohol"], mood: "Happy", body_location: ["Throat"], time_context: "Evening", notes: "Valentine's dinner, kept it quiet." },
  { date: "2026-02-15", symptoms: ["Hoarseness"], severity: 4, potential_triggers: null, mood: "Relaxed", body_location: ["Throat"], time_context: "Morning", notes: "Feeling much better today." },
  { date: "2026-02-16", symptoms: ["Hoarseness"], severity: 3, potential_triggers: ["Talking on phone"], mood: "Productive", body_location: ["Throat"], time_context: "Afternoon", notes: "Managed a 20-min call." },
  { date: "2026-02-17", symptoms: ["Dryness"], severity: 2, potential_triggers: ["Dehydration"], mood: "Focus", body_location: ["Throat"], time_context: "All day", notes: "Drinking 3L of water today." },
  { date: "2026-02-18", symptoms: null, severity: 1, potential_triggers: null, mood: "Great", body_location: null, time_context: "Morning", notes: "Almost back to normal." },
  { date: "2026-02-19", symptoms: ["Hoarseness"], severity: 2, potential_triggers: ["Singing"], mood: "Joyful", body_location: ["Throat"], time_context: "Evening", notes: "Sang a bit in the car, slight strain." },
  { date: "2026-02-20", symptoms: ["Sore Throat"], severity: 3, potential_triggers: ["Cold Air"], mood: "Fine", body_location: ["Throat"], time_context: "Morning", notes: "Walked to work in the cold." },
  { date: "2026-02-21", symptoms: ["Cough"], severity: 4, potential_triggers: ["Dust"], mood: "Annoyed", body_location: ["Chest"], time_context: "Afternoon", notes: "Cleaning the attic triggered a cough." },
  { date: "2026-02-22", symptoms: ["Hoarseness", "Pain"], severity: 5, potential_triggers: ["Passive Smoke"], mood: "Tired", body_location: ["Throat"], time_context: "Night", notes: "At a bar with smoke, throat hurt." },
  { date: "2026-02-23", symptoms: ["Hoarseness"], severity: 4, potential_triggers: null, mood: "Calm", body_location: ["Throat"], time_context: "Morning", notes: "Resting today." },
  { date: "2026-02-24", symptoms: ["Dryness"], severity: 2, potential_triggers: ["Coffee"], mood: "Good", body_location: ["Throat"], time_context: "Afternoon", notes: "Switched to herbal tea." },
  { date: "2026-02-25", symptoms: ["Breathiness"], severity: 3, potential_triggers: ["Anxiety"], mood: "Nervous", body_location: ["Chest"], time_context: "Evening", notes: "Presentation prep making me breathless." },
  { date: "2026-02-26", symptoms: ["Hoarseness"], severity: 2, potential_triggers: null, mood: "Confident", body_location: ["Throat"], time_context: "All day", notes: "Voice is stable." },
  { date: "2026-02-27", symptoms: null, severity: 0, potential_triggers: null, mood: "Excellent", body_location: null, time_context: "Morning", notes: "No symptoms at all!" },
  { date: "2026-02-28", symptoms: null, severity: 0, potential_triggers: null, mood: "Hype", body_location: null, time_context: "Now", notes: "Hackathon demo day! Voice is 100%." },
];

function getDayOfWeek(dateStr) {
  const d = new Date(dateStr + "T12:00:00");
  return DAYS[d.getDay()];
}

function getTimeOfDay(entry) {
  return TIME_CONTEXT_TO_PERIOD[entry.time_context] || "afternoon";
}

function deriveStatsFromDemoEntries(entries) {
  const severity_trends = entries
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((e) => ({ date: e.date, severity: e.severity }));

  const triggerCounts = {};
  const symptomCounts = {};
  const heatmapKey = (symptom, day, time) => `${symptom}|${day}|${time}`;
  const heatmap = {};
  const triggerSymptomPairs = {};

  entries.forEach((e) => {
    (e.potential_triggers || []).forEach((t) => {
      triggerCounts[t] = (triggerCounts[t] || 0) + 1;
      (e.symptoms || []).forEach((s) => {
        const key = `${t}|${s}`;
        triggerSymptomPairs[key] = (triggerSymptomPairs[key] || 0) + 1;
      });
    });
    (e.symptoms || []).forEach((s) => {
      symptomCounts[s] = (symptomCounts[s] || 0) + 1;
      const day = getDayOfWeek(e.date);
      const time = getTimeOfDay(e);
      const k = heatmapKey(s, day, time);
      heatmap[k] = (heatmap[k] || 0) + 1;
    });
  });

  const trigger_correlations = Object.entries(triggerCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const symptom_frequency = Object.entries(symptomCounts)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const symptom_temporal_heatmap = [];
  for (const [key, value] of Object.entries(heatmap)) {
    const [symptom, day, time_of_day] = key.split("|");
    symptom_temporal_heatmap.push({ symptom, day, time_of_day, value });
  }

  const activity_symptom_correlations = [];
  for (const [key, count] of Object.entries(triggerSymptomPairs)) {
    const [activity, symptom] = key.split("|");
    const triggerTotal = triggerCounts[activity] || 1;
    activity_symptom_correlations.push({
      activity,
      symptom,
      confidence: Math.min(1, Math.round((count / triggerTotal) * 100) / 100),
      sample_size: count,
    });
  }
  activity_symptom_correlations.sort((a, b) => b.confidence - a.confidence);

  return {
    total_entries: entries.length,
    date_range_days: entries.length,
    message: null,
    severity_trends,
    trigger_correlations,
    symptom_frequency,
    symptom_temporal_heatmap,
    activity_symptom_correlations,
  };
}

export const MOCK_STATS = deriveStatsFromDemoEntries(DEMO_LOG_ENTRIES);

export const MOCK_INSIGHTS = {
  insights: [
    {
      id: "1",
      title: "Coffee & dryness",
      body: "Dryness and hoarseness show up often when you log Coffee as a trigger. Switching to herbal tea or more water on voice-heavy days may help.",
      icon: "☕",
    },
    {
      id: "2",
      title: "Cold air and throat",
      body: "Cold Weather and Cold Air correlate with Sore Throat and Hoarseness in your logs. Consider a scarf or avoiding long cold exposure.",
      icon: "🧣",
    },
    {
      id: "3",
      title: "Stress and voice strain",
      body: "Stress and Public Speaking appear before higher severity and Loss of Voice in your history. Pacing and rest after big talks may reduce flare-ups.",
      icon: "🎤",
    },
  ],
  prediction: {
    title: "You're in a good place",
    body: "Your last few entries show low severity and stable voice. Keep up hydration and vocal rest when you feel the first signs of strain.",
    riskLevel: "low",
  },
  advice: {
    title: "What your pattern suggests",
    body:
      "Your logs point to dryness and hoarseness often linked to coffee, cold air, and stress. " +
      "Staying hydrated, using a humidifier, and resting your voice after long talking or singing may help keep symptoms from spiking.",
    disclaimer:
      "This is not a medical diagnosis. If symptoms worsen, change, or worry you, talk to a licensed clinician.",
  },
  message: null,
};

/** "Not enough data" response shape for testing empty state */
export const NOT_ENOUGH_DATA_INSIGHTS = {
  insights: [],
  prediction: null,
  advice: null,
  message: "Not enough data yet. Keep logging to unlock insights!",
};

export const NOT_ENOUGH_DATA_STATS = {
  total_entries: 2,
  message: "Minimum 5 entries needed for analysis.",
  trigger_correlations: [],
  severity_trends: [],
  symptom_frequency: [],
  symptom_temporal_heatmap: [],
  activity_symptom_correlations: [],
};
