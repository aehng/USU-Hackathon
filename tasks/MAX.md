# 📈 Max — Dashboard + Charts + C-Based JSON Filter

You own everything the user sees after they log an entry, PLUS a critical piece of the backend: the JSON filter. The dashboard is where the "magic" becomes visible, and your filter ensures the magic doesn't break. 

**Branch:** `max/dashboard`

---

## Phase 1 — Setup (~4:00pm Start)
- [ ] Clone repo, create your branch
- [ ] Pull Eli's initial frontend scaffold once he pushes it.
- [ ] Install dependencies and confirm the app runs locally (`npm run dev`).
- [ ] Install Recharts (`npm install recharts`) — this is your charting library. Recharts is basically a translator: you give it an array of data, and it draws the picture.
- [ ] **Look at the Recharts docs (recharts.org) and note the exact field names your charts expect.**
  - Example: A LineChart usually wants data formatted like a list of objects: `[{name: "Monday", uv: 4000}, {name: "Tuesday", uv: 3000}]`.
  - Bookmark these shapes! You'll hand them to Clayton at the 7:00pm checkpoint so he can make sure the database spits out data that perfectly matches what your charts need.

---

## Phase 2 — Mock Data Layer (Fri 4:30–6:00pm)

**Build with fake data first. Do not wait on the backend.**

- [ ] Create `frontend/src/mock/dashboardData.js` with realistic fake data matching the shapes you found in the Recharts docs.
- [ ] Mock data should include:
  - 3 insight cards (title, body text, icon emoji)
  - 1 prediction card (title, body, risk level: low/medium/high)
  - 7 days of severity trend data points
  - Top 5 most common triggers with counts
  - Symptom frequency breakdown
- [ ] Make your mock data tell a compelling story — caffeine causing migraines, poor sleep causing fatigue. The judges will read these!

---

## Phase 3 — Dashboard Layout (Fri 6:00–7:00pm)
- [ ] Build `Dashboard.jsx` — the main insights page.
- [ ] Layout structure (top to bottom):
  - **Prediction card** — the one "heads up" warning, most prominent element.
  - **Insight cards** — 3 cards showing discovered patterns.
  - **Severity trend chart** — line chart, last 7 days.
  - **Top triggers bar chart** — horizontal bars, most common triggers.
  - **Symptom breakdown** — donut or pie chart of most logged symptoms.
- [ ] Build a shared nav bar component that appears on all three pages: Log | Dashboard | History.

---

## 🛑 7:00pm Checkpoint: The JSON Lock
Meet with Noah and Clayton. You must agree on exactly what the data looks like.
1. Show Clayton the Recharts shapes you need.
2. Agree on the exact fields the LLM will output (e.g., `symptoms`, `severity`, `potential_triggers`).
3. **Once this is locked in, you move to Phase 4.**

---

## Phase 4 — The C-Based JSON Filter (Fri 7:00pm–9:00pm)
**What is this?** The LLM is going to spit out a text string that is *supposed* to be formatted as JSON. Your C program acts like a bouncer at a club. It takes the string, checks if it has the required fields (like `severity`), and says "Valid" or "Invalid" before letting it into the database.

**Beginner Tips for C:**
- **Do not write a parser from scratch.** Use a lightweight, free library called `cJSON`. It allows you to easily pull variables out of a JSON string in C without pulling your hair out.
- [ ] Download `cJSON.h` and `cJSON.c` from GitHub and put them in your project folder.
- [ ] Write a C function that takes a string input.
- [ ] Use `cJSON_Parse()` to read the string.
- [ ] Check if the required fields exist (e.g., `cJSON_GetObjectItemCaseSensitive(json, "severity")`).
- [ ] If all required fields are there, return `true` (or 1). If something is missing or broken, return `false` (or 0).
- [ ] Compile it and test it by passing it a perfect JSON string, and then test it by passing it a broken/incomplete string.

⭐ **Stretch Goal (If you have time!): Auto-Fixing the JSON**
Instead of just rejecting bad JSON, see if your C code can *repair* basic mistakes made by the LLM before passing it to the database!
- [ ] **Word Swapping:** If the LLM spits out the key `"symptom"` instead of `"symptoms"`, or `"level"` instead of `"severity"`, have your C code detect the typo, grab the data, and map it to the correct word in a new JSON object.
- [ ] **Reorganizing:** Grab all the valid data points from the messy LLM output and construct a brand new, perfectly formatted JSON string where the fields are in the exact standardized order Clayton expects.

---

## Phase 5 — Insight + Prediction Cards & Charts (Fri 9:00pm–11:00pm)

Jump back into React/Frontend. All charts use Recharts. Each one should have proper labels, a tooltip on hover, and look clean at phone width.

- [ ] **Insight & Prediction Cards:**
  - Build `InsightCard` component — icon, title, body text.
  - Build `PredictionCard` component — visually distinct with a risk indicator (🟢 Low, 🟡 Medium, 🔴 High).
- [ ] **Severity Trend — Line Chart:** X axis: dates. Y axis: severity (1–10).
- [ ] **Top Triggers — Bar Chart (horizontal):** Y axis: trigger names. X axis: frequency.
- [ ] **Symptom Frequency — Donut Chart:** Breakdown of most commonly logged symptoms.

---

## Phase 6 — History Page (Fri 11:00pm–Sat 1:00am)
- [ ] Build `HistoryPage.jsx` — scrollable list of past entries.
- [ ] Each entry row shows:
  - Date and time
  - Symptom tags (colored by severity — red = high, yellow = medium, green = low)
  - Severity badge (e.g. "7/10")
- [ ] Add a filter dropdown: filter by symptom type.

---

## Phase 7 — Wire Up Real API + Global Refresh (Sat 8:00–10:00am)
Once Noah and Clayton's backend is stable, swap your fake mock data for the real API calls.

- [ ] Replace mock insights with data from `GET /api/insights/{user_id}`.
- [ ] Replace mock chart data with data from `GET /api/stats/{user_id}`.
- [ ] **Handle the "not enough data" message gracefully:**
  - If the API says there isn't enough data yet, don't show blank broken charts! Show a friendly message: *"Not enough data yet. Log more entries to see patterns."*
- [ ] Add loading spinners while data is fetching so the user knows it's thinking.

---

## Phase 8 — Performance Testing + Polish (Sat 10:00–11:00am)
- [ ] Test on a real phone in Chrome — not just a desktop browser with a narrowed window. Mobile scrolling behaves differently!
- [ ] Pick one consistent accent color for the whole app and use it everywhere.
- [ ] Make sure all charts have axis labels and tooltips.
- [ ] Do a final manual test: Log an entry from the Log screen, make sure it passes your C filter, and confirm it shows up in the Dashboard.

---

## 💡 Tips
- **Mock data first, always.** The dashboard should look complete on your laptop by 7:00 PM even if the backend isn't ready.
- **Recharts relies on exact spelling.** If a chart is blank, 90% of the time it's because the array objects don't have the exact field names (keys) the chart is expecting. Double-check your spelling!
- **Don't panic about C.** C is notorious for throwing scary memory errors. Take it slow, use `printf` to print variables to your console so you can see what the program is doing step-by-step, and rely on the `cJSON` library to do the heavy lifting.
