# 🎙️ Eli — Voice UI + Log Screen + Project Coordination

You own the voice logging screen (the hero feature of the whole app) and keep the team unblocked. You're also managing git merges to main and making sure nobody is stuck.

**Branch:** `eli/voice-ui`

---

## What You're Building
The log screen is the first thing a user sees and the feature that makes this app unique. It needs to feel effortless — press a button, speak naturally, done. You're also building the mode toggle between Quick Log and Guided mode.

---

## Phase 1 — Setup (Fri 5:00–6:00pm)
- [ ] Create the GitHub repo and add Noah, Clayton, and Max as collaborators
- [ ] Push the initial folder structure so everyone can clone
- [ ] Confirm everyone has cloned the repo and can SSH into the VM
- [ ] Update the VM IP in README.md once it's known
- [ ] Spin up Docker Compose on the VM and confirm all three services start
- [ ] Create your branch and start your frontend project

---

## Phase 2 — Voice Recorder Component (Fri 6:00–8:00pm)
- [ ] Build the core voice recorder component — a large mic button the user taps to record
- [ ] Wire up the Web Speech API (built into Chrome/Edge — no library needed)
- [ ] Show a live transcript as the user speaks
- [ ] Auto-submit the transcript when the user stops speaking
- [ ] Show a loading state while waiting for the backend to respond
- [ ] Display the extracted symptom tags the backend returns (e.g. "headache · severity 7/10")
- [ ] Test in **Chrome or Edge only** — Web Speech API does not work in Firefox

---

## Phase 3 — Log Screen + Modes (Fri 8:00–10:00pm)
- [ ] Build the full log page with a toggle at the top: **Quick Log** vs **Guided**
- [ ] **Quick log flow:** Record → transcript → extracted tags shown → user confirms → logged ✓
- [ ] **Guided flow:** Record → backend returns 2-3 follow-up questions → show each one at a time → user speaks/types answer → all submitted together → logged ✓
- [ ] Build a confirmation screen ("Logged! 🎉") showing a summary of what was captured
- [ ] Connect to the correct backend routes depending on mode
- [ ] Build a shared API client module that Max can import from too

> **Priority:** Nail quick log first. Guided is the polish layer.

---

## Phase 4 — Integration + Navigation (Fri 10pm–Sat 1am)
- [ ] Test the full voice → backend → DB → confirmation flow end to end
- [ ] Handle error states (backend down, speech not recognized, empty transcript)
- [ ] Build a nav bar: Log → Dashboard → History
- [ ] Test on a phone screen (~390px wide)
- [ ] Merge your branch into main, trigger a VM pull

---

## Phase 5 — Demo Prep (Sat 8:00–11:00am)
- [ ] Do 5 full run-throughs of the demo
- [ ] Confirm mic works on the device you'll demo on
- [ ] Write and practice your two demo voice entries — one quick, one guided
- [ ] Prepare a typed-input fallback in case the mic fails on stage
- [ ] Help Max polish the dashboard if you have time

---

## Tips
- Build the UI with hardcoded mock data first if the backend isn't ready — swap in real API calls once Noah's routes are up
- The mic button should be big, obvious, and satisfying to press — it's the centerpiece
- Keep the API client in one shared file so Max can reuse it
- Guided mode questions should appear one at a time, not all at once — keeps it conversational
