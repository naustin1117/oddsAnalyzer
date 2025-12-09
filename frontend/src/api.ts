/**
 * API utility for making requests to the FastAPI backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Make a GET request to the API
 */
export async function apiGet<T>(endpoint: string, apiKey: string = 'dev-key-123'): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const headers: Record<string, string> = {
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
 */
export async function apiPost<T>(
  endpoint: string,
  data: unknown,
  apiKey: string = 'dev-key-123'
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const headers: Record<string, string> = {
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