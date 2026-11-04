const API_BASE = '/api';

export type Activity = {
	time: string;
	name: string;
	description: string;
	cost: number;
	duration_hours?: number;
	category?: string;
};

export type DayPlan = {
	day: number;
	date?: string;
	theme?: string;
	activities: Activity[];
};

export type WeatherInfo = {
	temperature?: number;
	condition?: string;
	humidity?: number;
	wind_speed?: number;
};

export type TripPlan = {
	destination: string;
	duration_days: number;
	interests: string[];
	budget: string;
	itinerary: DayPlan[];
	total_cost: number;
	currency?: string;
	weather?: WeatherInfo;
	tips?: string[];
};

export type Destination = {
	id: string;
	city: string;
	country: string;
	description: string;
	best_seasons?: string[];
	budget_range?: string;
	highlights?: string[];
};

export type SearchResult = {
	destinations: Destination[];
	query: string;
};

export async function planTrip(
	destination: string,
	duration_days: number,
	interests: string[],
	budget: string,
): Promise<TripPlan> {
	const res = await fetch(`${API_BASE}/plan`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ destination, duration_days, interests, budget }),
	});
	if (!res.ok) throw new Error(`Planning failed: ${res.statusText}`);
	return res.json();
}

export async function searchDestinations(query: string): Promise<SearchResult> {
	const res = await fetch(`${API_BASE}/search`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ query }),
	});
	if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
	return res.json();
}

export async function getDestination(id: string): Promise<Destination> {
	const res = await fetch(`${API_BASE}/destination/${id}`);
	if (!res.ok) throw new Error(`Destination not found: ${res.statusText}`);
	return res.json();
}

export async function getWeather(city: string): Promise<WeatherInfo> {
	const res = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(city)}`);
	if (!res.ok) throw new Error(`Weather fetch failed: ${res.statusText}`);
	return res.json();
}

export async function checkHealth(): Promise<boolean> {
	try {
		const res = await fetch(`${API_BASE}/health`);
		return res.ok;
	} catch {
		return false;
	}
}
