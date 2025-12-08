/**
 * API utility for making requests to the FastAPI backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Make a GET request to the API
 * @param {string} endpoint - The API endpoint (e.g., '/health', '/predictions')
 * @param {string} apiKey - Optional API key for authenticated endpoints
 * @returns {Promise} - The API response data
 */
export async function apiGet(endpoint, apiKey = 'dev-key-123') {
  const url = `${API_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
  };

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const response = await fetch(url, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Make a POST request to the API
 * @param {string} endpoint - The API endpoint
 * @param {object} data - The request body
 * @param {string} apiKey - Optional API key for authenticated endpoints
 * @returns {Promise} - The API response data
 */
export async function apiPost(endpoint, data, apiKey = 'dev-key-123') {
  const url = `${API_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
  };

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}