# 🎙️ Eli — Voice UI + Log Screen + Project Coordination

Eli owned the voice logging screen — the hero feature of the whole app — and kept the team unblocked throughout the hackathon. He also managed git merges to main and made sure nobody was stuck.

**Branch:** `eli/voice-ui`

---

## What Was Built

The log screen is the first thing a user sees and the feature that makes this app unique. Recording, transcription, and submission all happen seamlessly — the user presses a button, speaks naturally, and the app takes care of the rest.

### Voice Recorder
- Built the `VoiceRecorder` component supporting both **Quick Log** and **Guided Log** modes
- Uses the **MediaRecorder API** to capture raw audio in-browser, then sends it to the backend's `/api/transcribe` endpoint (Faster-Whisper) for reliable cross-browser transcription
- Shows a live recording timer and stops on user demand — no auto-submit
- Handles errors gracefully: shows "Try Again" and "Type Instead" fallback options
- Guides users through conversational follow-up questions in Guided mode

### App Structure
- Built the full single-page app with tab navigation: **Main**, **Guided log**, **Quick log**, **History**
- Created `frontend/src/context/RefreshContext.jsx` — a global refresh signal so logging an entry immediately updates the Dashboard without a manual reload
- Wrapped the app in `RefreshProvider` in `App.jsx`
- Created a shared API client module (`frontend/src/api/client.js`) used by all components

### Coordination
- Created the GitHub repo, set up the initial folder structure, added collaborators
- Managed branch merges to `main` and VM pulls throughout the hackathon
- Designated as README keeper — all config constant changes go through Eli

---

## Key Files
- `frontend/src/components/VoiceRecorder.jsx` — core voice/text logging component
- `frontend/src/context/RefreshContext.jsx` — global dashboard refresh signal
- `frontend/src/api/client.js` — shared API client (all backend calls)
- `frontend/src/App.jsx` — app root with `RefreshProvider`
