/**
 * API utility for making requests to the FastAPI backend
 */

import { supabase } from './lib/supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get the current user's JWT token if authenticated
 */
async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ?? null
}

/**
 * Make a GET request to the API
 */
export async function apiGet<T>(endpoint: string, apiKey: string = 'dev-key-123'): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add legacy API key for backward compatibility
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  // Add Supabase JWT if user is authenticated (for future use)
  const token = await getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
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

  // Add legacy API key for backward compatibility
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  // Add Supabase JWT if user is authenticated (for future use)
  const token = await getAuthToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
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