// API client for backend communication
// NOTE: Ask Eli before changing DEMO_USER_ID or API_BASE_URL (README keeper rule)

const DEFAULT_API_BASE_URL = 'https://api.flairup.dpdns.org';
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
export const DEMO_USER_ID = 'demo-user-001';

async function fetchJson(url, options = {}) {
  let response;

  try {
    response = await fetch(url, options);
  } catch (error) {
    throw new Error(`Network error reaching ${url}. Verify backend is running on ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${url}`);
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

// Guided log - start with voice input, get follow-up questions
export async function guidedLogStart(transcript) {
  return fetchJson(`${API_BASE_URL}/api/log/guided/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      transcript: transcript
    })
  });
}

// Guided log - finalize with answers to follow-up questions
export async function guidedLogFinalize(extractedState, answers) {
  return fetchJson(`${API_BASE_URL}/api/log/guided/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      extracted_state: extractedState,
      answers: answers
    })
  });
}

// Get dashboard insights
export async function getInsights() {
  return fetchJson(`${API_BASE_URL}/api/insights?user_id=${DEMO_USER_ID}`);
}

// Get history
export async function getHistory() {
  return fetchJson(`${API_BASE_URL}/api/history?user_id=${DEMO_USER_ID}`);
}
