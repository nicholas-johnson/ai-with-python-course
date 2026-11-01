export interface Movie {
  id: string;
  title: string;
  year: number;
  rating: number;
  genres: string[];
  director: string;
  cast: string[];
  explanation: string;
  mood_tags: string[];
}

export interface RecommendResponse {
  movies: Movie[];
  query: string;
}

export interface DataQueryResponse {
  question: string;
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  summary: string;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

export function recommendMovies(query: string): Promise<RecommendResponse> {
  return request('/api/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
}

export function queryData(question: string): Promise<DataQueryResponse> {
  return request('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}

export function getMovie(id: string): Promise<Movie> {
  return request(`/api/movie/${encodeURIComponent(id)}`);
}

export function getSchema(): Promise<{ tables: Record<string, string[]> }> {
  return request('/api/schema');
}

export function checkHealth(): Promise<{ status: string }> {
  return request('/api/health');
}
