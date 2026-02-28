// API client for backend communication
// NOTE: Ask Eli before changing DEMO_USER_ID or API_BASE_URL (README keeper rule)

export const API_BASE_URL = 'https://flairup.dpdns.org';
export const DEMO_USER_ID = 'demo-user-001';

// Quick log - single voice input, immediate extraction
export async function quickLog(transcript) {
  const response = await fetch(`${API_BASE_URL}/api/log/quick`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      transcript: transcript
    })
  });

  if (!response.ok) {
    throw new Error(`Quick log failed: ${response.status}`);
  }

  return response.json();
}

// Guided log - start with voice input, get follow-up questions
export async function guidedLogStart(transcript) {
  const response = await fetch(`${API_BASE_URL}/api/log/guided/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      transcript: transcript
    })
  });

  if (!response.ok) {
    throw new Error(`Guided log start failed: ${response.status}`);
  }

  return response.json();
}

// Guided log - finalize with answers to follow-up questions
export async function guidedLogFinalize(extractedState, answers) {
  const response = await fetch(`${API_BASE_URL}/api/log/guided/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: DEMO_USER_ID,
      extracted_state: extractedState,
      answers: answers
    })
  });

  if (!response.ok) {
    throw new Error(`Guided log finalize failed: ${response.status}`);
  }

  return response.json();
}

// Get dashboard insights
export async function getInsights() {
  const response = await fetch(`${API_BASE_URL}/api/insights?user_id=${DEMO_USER_ID}`);

  if (!response.ok) {
    throw new Error(`Get insights failed: ${response.status}`);
  }

  return response.json();
}

// Get history
export async function getHistory() {
  const response = await fetch(`${API_BASE_URL}/api/history?user_id=${DEMO_USER_ID}`);

  if (!response.ok) {
    throw new Error(`Get history failed: ${response.status}`);
  }

  return response.json();
}
