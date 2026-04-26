import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

/**
 * Submit network flow features for prediction.
 * POST /predict
 */
export async function submitPrediction(data) {
  const response = await client.post('/predict', data);
  return response.data;
}

/**
 * Check backend health.
 * GET /health
 */
export async function getHealth() {
  const response = await client.get('/health');
  return response.data;
}

/**
 * Send a test email to verify SMTP configuration.
 * POST /test-email
 */
export async function sendTestEmail() {
  const response = await client.post('/test-email');
  return response.data;
}

/**
 * Get email alerting configuration status.
 * GET /email-status
 */
export async function getEmailStatus() {
  const response = await client.get('/email-status');
  return response.data;
}

export default client;

