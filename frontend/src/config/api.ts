// API configuration supporting dynamic base URL for local development and deployed environments (Vercel)
export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
).replace(/\/+$/, '');
