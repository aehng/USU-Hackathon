// API client for backend communication
// ⚠️⚠️⚠️ DO NOT CHANGE API_BASE_URL OR PORTS UNDER ANY CIRCUMSTANCE ⚠️⚠️⚠️
// Required for production routing - ask Eli before any changes

// ⚠️ DO NOT CHANGE - Production API endpoint
const DEFAULT_API_BASE_URL = 'https://api.flairup.dpdns.org';

function resolveApiBaseUrl() {
  const configuredBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim();
  
  // Always use configured URL if set
  if (configuredBaseUrl) {
    return configuredBaseUrl;
  }
  
  // Fallback to production default
  return DEFAULT_API_BASE_URL;
}

export const API_BASE_URL = resolveApiBaseUrl();
export const DEMO_USER_ID = '00000000-0000-0000-0000-000000000001';

async function fetchJson(url, options = {}) {
  let response;

  // Add 2-minute timeout for slow LLM processing
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes

  try {
    response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after 2 minutes. The LLM might be processing - please wait or try a smaller model.`);
    }
    throw new Error(`Network error reaching ${url}. Verify backend is running on ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch (e) {
      // If response isn't JSON, use default message
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// Quick log - single voice input, immediate extraction
export async function quickLog(transcript) {
  console.log('🚀 quickLog called with transcript:', transcript);
  console.log('📍 API_BASE_URL:', API_BASE_URL);
  const url = `${API_BASE_URL}/api/log/quick`;
  console.log('🌐 Making request to:', url);
  
  const response = await fetchJson(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
          user_id: DEMO_USER_ID,
          transcript: transcript
        })
  });
  
  console.log('✅ quickLog response:', response);
  return response;
}

// Guided log - start conversation with initial transcript
export async function guidedLogStart(transcript) {
  console.log('🚀 guidedLogStart called with transcript:', transcript);
  const url = `${API_BASE_URL}/api/guided-log/start`;
  console.log('🌐 Making request to:', url);
  
  const response = await fetchJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      transcript: transcript
    })
  });
  
  console.log('✅ guidedLogStart response:', response);
  return response;
}

// Guided log - respond to a follow-up question
export async function guidedLogRespond(sessionId, answer) {
  console.log('🚀 guidedLogRespond called:', { sessionId, answer });
  const url = `${API_BASE_URL}/api/guided-log/respond`;
  console.log('🌐 Making request to:', url);
  
  const response = await fetchJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      answer: answer
    })
  });
  
  console.log('✅ guidedLogRespond response:', response);
  return response;
}

// Guided log - finalize session and extract data via /generate endpoint
export async function guidedLogFinalize(sessionId) {
  console.log('🚀 guidedLogFinalize called with session:', sessionId);
  const url = `${API_BASE_URL}/api/guided-log/finalize`;
  console.log('🌐 Finalizing guided log at:', url);
  
  const response = await fetchJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_id: DEMO_USER_ID
    })
  });
  
  console.log('✅ guidedLogFinalize response:', response);
  return response.extracted_data;
}

// Guided log - save completed guided log to database
export async function guidedLogSave(extractedData) {
  console.log('🚀 guidedLogSave called:', extractedData);
  const url = `${API_BASE_URL}/api/log/quick`;
  console.log('🌐 Saving guided log data to:', url);
  
  // Reuse quick log endpoint to save the extracted data
  const response = await fetchJson(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      // Send as pre-extracted data
      ...extractedData
    })
  });
  
  console.log('✅ guidedLogSave response:', response);
  return response;
}

// Get dashboard insights
export async function getInsights() {
  return fetchJson(`${API_BASE_URL}/api/insights?user_id=${DEMO_USER_ID}`);
}

// Replace the existing getHistory placeholder with this:
export async function getHistory() {
  console.log('🚀 getHistory called');
  return fetchJson(`${API_BASE_URL}/api/history/${DEMO_USER_ID}`);
}

// Add this new function to handle edits
export async function updateEntry(entryId, updateData) {
  console.log('🚀 updateEntry called for:', entryId);
  const url = `${API_BASE_URL}/api/entries/${entryId}`;
  
  const response = await fetchJson(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updateData)
  });
  
  console.log('✅ updateEntry response:', response);
  return response;
}

// Transcribe audio using Faster-Whisper
export async function transcribeAudio(audioBlob) {
  console.log('🎤 transcribeAudio called with blob size:', audioBlob.size);
  
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  
  const url = `${API_BASE_URL}/api/transcribe`;
  console.log('🌐 Transcribing at:', url);
  
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    let errorDetail = `Transcription failed (${response.status})`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch (e) {
      // If response isn't JSON, use default message
    }
    throw new Error(errorDetail);
  }
  
  const result = await response.json();
  console.log('✅ Transcription result:', result);
  return result;
}
