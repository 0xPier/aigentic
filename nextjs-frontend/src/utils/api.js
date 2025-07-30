const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

// Simple error logger that could be extended to send to logging service
const logError = (context, error) => {
  // In production, this could send to a logging service like Sentry
  if (process.env.NODE_ENV === 'development') {
    console.error(`[API Error] ${context}:`, error);
  }
  // Could add error reporting service here
};

export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}/api${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const config = {
    ...defaultOptions,
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      const errorMessage = errorData?.detail || `Failed to fetch: ${response.status} ${response.statusText}`;
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    logError(`API call failed for ${url}`, error);
    throw error;
  }
}; 