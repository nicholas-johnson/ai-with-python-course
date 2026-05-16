<script lang="ts">
	import { searchRecipes, uploadPhoto, checkHealth, type Recipe, type SearchResult } from '$lib/api';
	import RecipeCard from '$lib/components/RecipeCard.svelte';
	import { Search, Loader2, Wifi, WifiOff, ImagePlus, ChefHat, X, Sparkles } from 'lucide-svelte';

	const DIETARY_FILTERS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free'] as const;

	let query = $state('');
	let loading = $state(false);
	let connected = $state(false);
	let recipes: Recipe[] = $state([]);
	let resultsCached = $state(false);
	let hasSearched = $state(false);
	let errorMessage = $state('');
	let selectedFilters: string[] = $state([]);
	let fileInput: HTMLInputElement;

	$effect(() => {
		checkHealth().then((ok) => (connected = ok));
		const interval = setInterval(() => checkHealth().then((ok) => (connected = ok)), 5000);
		return () => clearInterval(interval);
	});

	function toggleFilter(filter: string) {
		if (selectedFilters.includes(filter)) {
			selectedFilters = selectedFilters.filter((f) => f !== filter);
		} else {
			selectedFilters = [...selectedFilters, filter];
		}
	}

	async function handleSearch() {
		const text = query.trim();
		if (!text || loading) return;

		loading = true;
		errorMessage = '';
		try {
			const dietaryFilter = selectedFilters.length > 0 ? selectedFilters.join(', ') : undefined;
			const result: SearchResult = await searchRecipes(text, dietaryFilter);
			recipes = result.recipes ?? [];
			resultsCached = result.cached ?? false;
			hasSearched = true;
		} catch (err) {
			errorMessage = `Search failed: ${err}`;
			recipes = [];
		}
		loading = false;
	}

	async function handlePhotoUpload(e: Event) {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		loading = true;
		errorMessage = '';
		try {
			const base64 = await fileToBase64(file);
			const result: SearchResult = await uploadPhoto(base64);
			recipes = result.recipes ?? [];
			resultsCached = result.cached ?? false;
			hasSearched = true;
			if (result.query) query = result.query;
		} catch (err) {
			errorMessage = `Upload failed: ${err}`;
			recipes = [];
		}
		loading = false;
		target.value = '';
	}

	function fileToBase64(file: File): Promise<string> {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => {
				const result = reader.result as string;
				resolve(result.split(',')[1]);
			};
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			handleSearch();
		}
	}

	function clearSearch() {
		query = '';
		recipes = [];
		hasSearched = false;
		errorMessage = '';
		selectedFilters = [];
	}
</script>

<div class="flex flex-col min-h-screen">
	<!-- Header -->
	<header class="border-b bg-card">
		<div class="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="flex items-center justify-center h-10 w-10 rounded-lg bg-primary text-primary-foreground">
					<ChefHat class="h-5 w-5" />
				</div>
				<div>
					<h1 class="text-xl font-bold tracking-tight">Recipe Finder</h1>
					<p class="text-xs text-muted-foreground">AI-powered recipe search</p>
				</div>
			</div>
			<div class="flex items-center gap-2 text-sm">
				{#if connected}
					<Wifi class="h-4 w-4 text-green-500" />
					<span class="text-muted-foreground">Connected</span>
				{:else}
					<WifiOff class="h-4 w-4 text-red-500" />
					<span class="text-red-500">Disconnected</span>
				{/if}
			</div>
		</div>
	</header>

	<!-- Search Section -->
	<div class="bg-card border-b">
		<div class="max-w-5xl mx-auto px-6 py-6">
			<div class="flex items-center gap-2">
				<div class="flex-1 relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<input
						type="text"
						bind:value={query}
						onkeydown={handleKeydown}
						placeholder="Type ingredients or describe what you want to cook..."
						class="w-full rounded-lg border bg-background pl-10 pr-10 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
					/>
					{#if query}
						<button
							onclick={clearSearch}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
						>
							<X class="h-4 w-4" />
						</button>
					{/if}
				</div>

				<input
					bind:this={fileInput}
					type="file"
					accept="image/*"
					onchange={handlePhotoUpload}
					class="hidden"
				/>
				<button
					onclick={() => fileInput.click()}
					disabled={loading}
					class="flex items-center gap-2 rounded-lg border bg-background px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors disabled:opacity-50"
					title="Upload a photo of ingredients"
				>
					<ImagePlus class="h-4 w-4" />
					<span class="hidden sm:inline">Photo</span>
				</button>

				<button
					onclick={handleSearch}
					disabled={loading || !query.trim()}
					class="flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-5 py-2.5 text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
				>
					{#if loading}
						<Loader2 class="h-4 w-4 animate-spin" />
					{:else}
						<Search class="h-4 w-4" />
					{/if}
					Search
				</button>
			</div>

			<!-- Dietary Filters -->
			<div class="flex items-center gap-2 mt-3">
				<span class="text-xs text-muted-foreground font-medium">Dietary:</span>
				{#each DIETARY_FILTERS as filter}
					<button
						onclick={() => toggleFilter(filter)}
						class="rounded-full px-3 py-1 text-xs font-medium transition-colors {selectedFilters.includes(filter) ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'}"
					>
						{filter}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- Results -->
	<main class="flex-1">
		<div class="max-w-5xl mx-auto px-6 py-6">
			{#if errorMessage}
				<div class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
					{errorMessage}
				</div>
			{:else if loading}
				<div class="flex flex-col items-center justify-center py-20 text-muted-foreground">
					<Loader2 class="h-8 w-8 animate-spin mb-3" />
					<p class="text-sm font-medium">Finding recipes...</p>
				</div>
			{:else if hasSearched && recipes.length === 0}
				<div class="flex flex-col items-center justify-center py-20 text-muted-foreground">
					<ChefHat class="h-12 w-12 mb-3 opacity-30" />
					<p class="font-medium">No recipes found</p>
					<p class="text-sm mt-1">Try different ingredients or a broader search</p>
				</div>
			{:else if hasSearched}
				<div class="flex items-center justify-between mb-4">
					<p class="text-sm text-muted-foreground">
						Found <span class="font-medium text-foreground">{recipes.length}</span> recipe{recipes.length !== 1 ? 's' : ''}
					</p>
					{#if resultsCached}
						<span class="inline-flex items-center gap-1 rounded-full bg-accent/20 px-2.5 py-0.5 text-xs font-medium text-accent">
							<Sparkles class="h-3 w-3" />
							Results from cache
						</span>
					{/if}
				</div>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each recipes as recipe}
						<RecipeCard {recipe} cached={resultsCached} />
					{/each}
				</div>
			{:else}
				<div class="flex flex-col items-center justify-center py-20 text-muted-foreground">
					<ChefHat class="h-16 w-16 mb-4 opacity-20" />
					<p class="text-lg font-medium">What would you like to cook?</p>
					<p class="text-sm mt-1 max-w-md text-center">
						Search by ingredients, cuisine, or describe a dish. You can also upload a photo of what's in your fridge.
					</p>
					<div class="flex flex-wrap justify-center gap-2 mt-6">
						{#each ['chicken pasta', 'vegan stir fry', 'quick breakfast', 'Italian dinner'] as suggestion}
							<button
								onclick={() => { query = suggestion; handleSearch(); }}
								class="rounded-full border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/30 transition-colors"
							>
								{suggestion}
							</button>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</main>

	<!-- Footer -->
	<footer class="border-t py-4">
		<div class="max-w-5xl mx-auto px-6 text-center text-xs text-muted-foreground">
			AI Python Course — Module 12: Productionisation
		</div>
	</footer>
</div>
