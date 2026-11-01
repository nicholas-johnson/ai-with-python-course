const API_BASE = '/api';

export type Recipe = {
	id: string;
	title: string;
	cuisine: string;
	difficulty: string;
	cook_time_minutes: number;
	servings: number;
	ingredients: string[];
	allergens: string[];
	description: string;
	cached: boolean;
};

export type SearchResult = {
	recipes: Recipe[];
	cached: boolean;
	query: string;
};

export type HealthStatus = {
	status: string;
	cache?: string;
};

export async function searchRecipes(
	query: string,
	dietaryFilter?: string,
): Promise<SearchResult> {
	const res = await fetch(`${API_BASE}/search`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ query, dietary_filter: dietaryFilter }),
	});
	if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
	return res.json();
}

export async function uploadPhoto(imageBase64: string): Promise<SearchResult> {
	const res = await fetch(`${API_BASE}/upload-photo`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ image: imageBase64 }),
	});
	if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
	return res.json();
}

export async function getRecipe(id: string): Promise<Recipe> {
	const res = await fetch(`${API_BASE}/recipe/${id}`);
	if (!res.ok) throw new Error(`Recipe not found: ${res.statusText}`);
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
