# 📈 Max — Dashboard + Charts + History Page

You own everything the user sees after they log an entry. The dashboard is where the "magic" becomes visible — this is what judges will look at and go "wow." Make it impressive.

**Branch:** `max/dashboard`

---

## Phase 1 — Setup (Fri 5:00–6:00pm)
- [ ] Clone repo, create your branch
- [ ] Pull Eli's initial frontend scaffold once he pushes it (should be up by 5:30pm)
- [ ] Install dependencies and confirm the app runs locally
- [ ] Install Recharts (`npm install recharts`) — this is your charting library
- [ ] Open the Recharts docs (recharts.org) and bookmark them — you'll reference them all night

---

## Phase 2 — Mock Data Layer (Fri 5:30–6:30pm)

**Build with fake data first. Do not wait on the backend.**

- [ ] Create `frontend/src/mock/dashboardData.js` with realistic fake data matching the shapes the API will eventually return
- [ ] Mock data should include:
  - 3 insight cards (title, body text, icon emoji)
  - 1 prediction card (title, body, risk level: low/medium/high)
  - 7 days of severity trend data points
  - Top 5 most common triggers with counts
  - Symptom frequency breakdown
- [ ] Make your mock data tell a compelling story — caffeine causing migraines, poor sleep causing fatigue, stress peaking on Mondays. The judges will read these.

---

## Phase 3 — Dashboard Layout (Fri 6:00–8:00pm)
- [ ] Build `Dashboard.jsx` — the main insights page
- [ ] Layout structure (top to bottom):
  - **Prediction card** — the one "heads up" warning, most prominent element
  - **Insight cards** — 3 cards showing discovered patterns
  - **Severity trend chart** — line chart, last 7 days
  - **Top triggers bar chart** — horizontal bars, most common triggers
  - **Symptom breakdown** — donut or pie chart of most logged symptoms
- [ ] Build a shared nav bar component that appears on all three pages: Log | Dashboard | History

---

## Phase 4 — Insight + Prediction Cards (Fri 7:00–8:30pm)
- [ ] Build `InsightCard` component — icon, title, body text, clean card styling
- [ ] Build `PredictionCard` component — same structure but visually distinct, with a risk indicator
  - 🟢 Low risk — green accent
  - 🟡 Medium risk — yellow/amber accent
  - 🔴 High risk — red accent
- [ ] The prediction card should feel like a warning or notification — make it stand out from the insight cards

---

## Phase 5 — Charts (Fri 8:30–11:00pm)

All charts use Recharts. Each one should have proper labels, a tooltip on hover, and look clean at phone width.

- [ ] **Severity Trend — Line Chart**
  - X axis: dates (last 7 days)
  - Y axis: severity (1–10)
  - Show for the user's most common symptom
  - Add a reference line at severity 5 as a midpoint marker

- [ ] **Top Triggers — Bar Chart (horizontal)**
  - Y axis: trigger names
  - X axis: how often each was logged
  - Sort by frequency descending

- [ ] **Symptom Frequency — Donut Chart**
  - Breakdown of most commonly logged symptoms
  - Show percentage labels

- [ ] **Trigger Heatmap** *(stretch goal — skip if short on time)*
  - Grid: symptoms on one axis, days of week on the other
  - Color intensity shows correlation strength

---

## Phase 6 — History Page (Fri 10:00pm–Sat 1:00am)
- [ ] Build `HistoryPage.jsx` — scrollable list of past entries
- [ ] Each entry row shows:
  - Date and time
  - Symptom tags (colored by severity — red = high, yellow = medium, green = low)
  - Severity badge (e.g. "7/10")
  - Trigger tags if any were logged
- [ ] Add a filter dropdown: filter by symptom type
- [ ] Most recent entries at the top

---

## Phase 7 — Wire Up Real API (Sat 8:00–10:00am)
Once Noah and Clayton's backend is stable, swap mock data for real API calls.

- [ ] Replace mock insights with data from `GET /api/insights/{user_id}`
- [ ] Replace mock chart data with data from `GET /api/stats/{user_id}`
- [ ] Wire history page to `GET /api/entries/{user_id}`
- [ ] Use the `DEMO_USER_ID` constant from `api/client.js` — don't hardcode UUIDs
- [ ] Add loading spinners while data is fetching
- [ ] Add empty state messages ("No entries yet — go log something!")

---

## Phase 8 — Polish (Sat 10:00–11:00am)
- [ ] Test on a real phone in Chrome — not just a desktop browser with narrow window
- [ ] Pick one consistent accent color for the whole app and use it everywhere
- [ ] Make sure all charts have axis labels and tooltips
- [ ] Make sure the prediction card is the first thing your eye goes to on the dashboard
- [ ] Remove any placeholder text or test labels that are still visible

---

## 💡 Tips
- **Mock data first, always.** The dashboard should look complete on your laptop by midnight even if the backend isn't ready.
- Recharts components are data-driven — if a chart looks wrong, 90% of the time it's because the array objects don't have the exact field names the chart's `dataKey` prop expects. Double check those.
- The insight cards and prediction card are the most visually impactful thing for judges. Prioritize those over the charts if time gets short.
- Keep phone screen width in mind constantly — the nav bar, cards, and charts all need to fit in ~390px without scrolling weirdly.
