export const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost') {
      return 'http://localhost:8000';
    } else {
      return '';
    }
  }
  return '';
};

export const API_URL = getApiUrl();