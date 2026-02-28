# Guided Log Service

A conversational chatbot service that helps users log their symptoms through an interactive Q&A experience.

## Overview

The guided log service uses the local Lemonade LLM to have a natural conversation with users, asking follow-up questions to gather complete symptom information. It's designed to extract:
- Symptoms
- Severity (1-10 scale)
- Potential triggers
- Mood
- Body location
- Time context
- Additional notes

## Architecture

- **Separate Service**: Runs independently from `main.py` to avoid merge conflicts
- **Stateful Conversations**: Tracks multi-turn dialogues in memory
- **LLM-Driven**: Uses Lemonade models to intelligently ask follow-up questions
- **RESTful API**: Easy integration with frontend

## Running the Service

```bash
cd backend
python guided_log.py
```

Default port: **8001**

## API Endpoints

### 1. Start Guided Log
**POST** `/guided-log/start`

Start a new conversation session.

**Request:**
```json
{
  "transcript": "I've had a headache since this morning",
  "user_id": "optional-user-id"
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "question": "How would you rate your headache on a scale of 1 to 10?",
  "is_complete": false,
  "extracted_data": null
}
```

### 2. Respond to Question
**POST** `/guided-log/respond`

Submit an answer and get the next question.

**Request:**
```json
{
  "session_id": "uuid-from-start",
  "answer": "I'd say it's about a 7"
}
```

**Response (more questions):**
```json
{
  "session_id": "uuid-here",
  "question": "Do you remember doing anything specific before the headache started?",
  "is_complete": false,
  "extracted_data": null
}
```

**Response (complete):**
```json
{
  "session_id": "uuid-here",
  "question": null,
  "is_complete": true,
  "extracted_data": {
    "symptoms": ["headache"],
    "severity": 7,
    "potential_triggers": ["screen time", "dehydration"],
    "mood": "frustrated",
    "body_location": "head - temples",
    "time_context": "since morning",
    "notes": "Intensified around noon"
  }
}
```

### 3. Check Session Status
**GET** `/guided-log/status/{session_id}`

Check if a session exists (useful for debugging).

## How It Works

1. **User starts**: Frontend sends initial transcript to `/guided-log/start`
2. **LLM asks questions**: Backend uses Lemonade to generate contextual follow-up questions
3. **User responds**: Frontend sends answers to `/guided-log/respond`
4. **Repeat**: Continue until LLM has enough information (2-4 questions typically)
5. **Complete**: LLM responds with `COMPLETE:{json_data}`
6. **Save**: Frontend saves extracted data using existing `/api/log/quick` endpoint

## Frontend Integration

The `VoiceRecorder.jsx` component handles the conversation flow:

```javascript
// Start conversation
const response = await guidedLogStart(transcript);
setGuidedState(response);

// User answers question
const response = await guidedLogRespond(sessionId, answer);

// Check if complete
if (response.is_complete) {
  await guidedLogSave(response.extracted_data);
}
```

## Configuration

Environment variables (optional):

```bash
LEMONADE_BASE_URL=http://localhost:8080/v1
LLM_MODEL=Qwen3-1.7B-Hybrid
GUIDED_LOG_PORT=8001
```

## Session Management

- **In-Memory**: Sessions stored in Python dictionary (development)
- **Production**: Replace with Redis, Memcached, or database
- **Auto-cleanup**: Sessions removed after completion
- **Timeout**: Add TTL in production (e.g., 30 minutes)

## Benefits Over Quick Log

- **More complete data**: LLM asks for missing information
- **Better triggers**: Questions specifically target potential causes
- **User-friendly**: Natural conversation vs single prompt
- **Adaptive**: Questions based on previous answers

## Example Conversation

```
User: "I'm not feeling well"

Bot: "I'm sorry to hear that. Can you describe what symptoms you're experiencing?"

User: "I have a stomachache and feel nauseous"

Bot: "How severe is it on a scale from 1 to 10, where 10 is unbearable?"

User: "About a 6"

Bot: "Did you eat or drink anything unusual today?"

User: "I had dairy for lunch and I'm usually lactose intolerant"

Bot: [COMPLETE] -> Extracts: symptoms: ["stomachache", "nausea"], 
                            severity: 6, 
                            triggers: ["dairy", "lactose"]
```

## Troubleshooting

**Issue**: Session not found
- **Fix**: Session may have expired or been completed. Start new session.

**Issue**: LLM not asking good questions
- **Fix**: Adjust temperature (currently 0.7) or use larger model

**Issue**: Conversation too long
- **Fix**: Modify system prompt to ask fewer questions or be more direct

**Issue**: Can't parse extracted data
- **Fix**: LLM response format might vary. Add more robust JSON extraction.

## Future Improvements

- [ ] Add session persistence (Redis)
- [ ] Support voice input for answers
- [ ] Add session timeout/expiry
- [ ] Support multiple languages
- [ ] Add conversation branching based on symptoms
- [ ] Integrate medical knowledge base for better questions
