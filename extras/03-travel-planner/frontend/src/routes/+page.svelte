<script lang="ts">
	import { Compass, MapPin, Calendar, DollarSign, Sun, Search, Loader2 } from 'lucide-svelte';
	import {
		planTrip,
		searchDestinations,
		getWeather,
		type TripPlan,
		type Destination,
		type WeatherInfo,
	} from '$lib/api';
	import DayCard from '$lib/components/DayCard.svelte';
	import DestinationCard from '$lib/components/DestinationCard.svelte';

	const ALL_INTERESTS = ['Culture', 'Food', 'Nature', 'Adventure', 'Nightlife', 'Shopping', 'History'];
	const BUDGETS = ['Budget', 'Mid-range', 'Luxury'] as const;
	const DURATIONS = Array.from({ length: 14 }, (_, i) => i + 1);

	let activeTab: 'plan' | 'search' = $state('plan');

	// Plan form state
	let destination = $state('');
	let durationDays = $state(5);
	let selectedInterests: string[] = $state([]);
	let budget: string = $state('Mid-range');
	let planning = $state(false);
	let tripPlan: TripPlan | null = $state(null);
	let weather: WeatherInfo | null = $state(null);
	let planError = $state('');

	// Search state
	let searchQuery = $state('');
	let searching = $state(false);
	let destinations: Destination[] = $state([]);
	let searchError = $state('');

	let totalCost = $derived(
		tripPlan?.itinerary?.reduce(
			(sum, day) => sum + day.activities.reduce((s, a) => s + (a.cost || 0), 0),
			0,
		) ?? tripPlan?.total_cost ?? 0,
	);

	function toggleInterest(interest: string) {
		if (selectedInterests.includes(interest)) {
			selectedInterests = selectedInterests.filter((i) => i !== interest);
		} else {
			selectedInterests = [...selectedInterests, interest];
		}
	}

	async function handlePlan() {
		if (!destination.trim()) return;
		planning = true;
		planError = '';
		tripPlan = null;
		weather = null;

		try {
			const [plan, wx] = await Promise.allSettled([
				planTrip(destination, durationDays, selectedInterests, budget),
				getWeather(destination),
			]);
			if (plan.status === 'fulfilled') tripPlan = plan.value;
			else throw plan.reason;
			if (wx.status === 'fulfilled') weather = wx.value;
		} catch (e: any) {
			planError = e.message || 'Failed to plan trip';
		} finally {
			planning = false;
		}
	}

	async function handleSearch() {
		if (!searchQuery.trim()) return;
		searching = true;
		searchError = '';
		destinations = [];

		try {
			const result = await searchDestinations(searchQuery);
			destinations = result.destinations;
		} catch (e: any) {
			searchError = e.message || 'Search failed';
		} finally {
			searching = false;
		}
	}

	function selectDestination(d: Destination) {
		destination = d.city;
		activeTab = 'plan';
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-8">
	<!-- Header -->
	<header class="mb-8 text-center">
		<div class="mb-3 flex items-center justify-center gap-3">
			<div class="rounded-xl bg-primary/10 p-2.5">
				<Compass class="h-8 w-8 text-primary" />
			</div>
			<h1 class="text-4xl font-bold tracking-tight text-foreground">Travel Planner</h1>
		</div>
		<p class="text-muted-foreground">Plan your perfect trip with AI-powered itineraries</p>
	</header>

	<!-- Tabs -->
	<div class="mb-6 flex gap-1 rounded-lg bg-muted p-1">
		<button
			class="flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all {activeTab === 'plan' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => (activeTab = 'plan')}
		>
			<Calendar class="h-4 w-4" />
			Plan a Trip
		</button>
		<button
			class="flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2.5 text-sm font-medium transition-all {activeTab === 'search' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => (activeTab = 'search')}
		>
			<Search class="h-4 w-4" />
			Search Destinations
		</button>
	</div>

	{#if activeTab === 'plan'}
		<!-- Planning Form -->
		<form
			class="mb-8 space-y-5 rounded-lg border bg-card p-6 shadow-sm"
			onsubmit={(e) => { e.preventDefault(); handlePlan(); }}
		>
			<!-- Destination -->
			<div>
				<label for="destination" class="mb-1.5 block text-sm font-medium text-foreground">
					<MapPin class="mr-1 inline h-4 w-4 text-primary" />
					Destination
				</label>
				<input
					id="destination"
					type="text"
					bind:value={destination}
					placeholder="e.g. Tokyo, Paris, Barcelona..."
					class="w-full rounded-md border bg-background px-4 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
				/>
			</div>

			<!-- Duration -->
			<div>
				<label for="duration" class="mb-1.5 block text-sm font-medium text-foreground">
					<Calendar class="mr-1 inline h-4 w-4 text-primary" />
					Duration
				</label>
				<select
					id="duration"
					bind:value={durationDays}
					class="w-full rounded-md border bg-background px-4 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
				>
					{#each DURATIONS as d}
						<option value={d}>{d} {d === 1 ? 'day' : 'days'}</option>
					{/each}
				</select>
			</div>

			<!-- Interests -->
			<div>
				<span class="mb-2 block text-sm font-medium text-foreground">Interests</span>
				<div class="flex flex-wrap gap-2">
					{#each ALL_INTERESTS as interest}
						<button
							type="button"
							class="rounded-full border px-3.5 py-1.5 text-sm font-medium transition-all {selectedInterests.includes(interest) ? 'border-primary bg-primary/10 text-primary' : 'border-border bg-background text-muted-foreground hover:border-primary/40'}"
							onclick={() => toggleInterest(interest)}
						>
							{interest}
						</button>
					{/each}
				</div>
			</div>

			<!-- Budget -->
			<div>
				<span class="mb-2 block text-sm font-medium text-foreground">
					<DollarSign class="mr-1 inline h-4 w-4 text-primary" />
					Budget Level
				</span>
				<div class="flex gap-3">
					{#each BUDGETS as level}
						<label
							class="flex flex-1 cursor-pointer items-center justify-center rounded-md border px-4 py-2.5 text-sm font-medium transition-all {budget === level ? 'border-primary bg-primary/10 text-primary' : 'border-border bg-background text-muted-foreground hover:border-primary/40'}"
						>
							<input
								type="radio"
								name="budget"
								value={level}
								bind:group={budget}
								class="sr-only"
							/>
							{level}
						</label>
					{/each}
				</div>
			</div>

			<!-- Submit -->
			<button
				type="submit"
				disabled={planning || !destination.trim()}
				class="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{#if planning}
					<Loader2 class="h-4 w-4 animate-spin" />
					Planning your trip...
				{:else}
					<Compass class="h-4 w-4" />
					Plan My Trip
				{/if}
			</button>
		</form>

		<!-- Error -->
		{#if planError}
			<div class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
				{planError}
			</div>
		{/if}

		<!-- Results -->
		{#if tripPlan}
			<div class="space-y-6">
				<!-- Trip header -->
				<div class="rounded-lg border bg-card p-5 shadow-sm">
					<div class="flex flex-wrap items-center gap-4">
						<div class="flex-1">
							<h2 class="flex items-center gap-2 text-2xl font-bold text-foreground">
								<MapPin class="h-5 w-5 text-primary" />
								{tripPlan.destination}
							</h2>
							<p class="mt-1 text-sm text-muted-foreground">
								{tripPlan.duration_days} days · {tripPlan.budget} · {tripPlan.interests?.join(', ') || 'All interests'}
							</p>
						</div>
						{#if weather}
							<div class="flex items-center gap-2 rounded-lg bg-accent/10 px-4 py-2">
								<Sun class="h-5 w-5 text-accent" />
								<div class="text-sm">
									{#if weather.temperature != null}
										<span class="font-semibold">{weather.temperature}°</span>
									{/if}
									{#if weather.condition}
										<span class="text-muted-foreground"> · {weather.condition}</span>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- Day-by-day itinerary -->
				{#if tripPlan.itinerary?.length}
					<div class="space-y-4">
						{#each tripPlan.itinerary as day}
							<DayCard {day} />
						{/each}
					</div>
				{/if}

				<!-- Tips -->
				{#if tripPlan.tips?.length}
					<div class="rounded-lg border bg-card p-5 shadow-sm">
						<h3 class="mb-3 font-semibold text-foreground">Travel Tips</h3>
						<ul class="space-y-1.5 text-sm text-muted-foreground">
							{#each tripPlan.tips as tip}
								<li class="flex gap-2">
									<span class="text-primary">•</span>
									{tip}
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Budget summary -->
				<div class="rounded-lg border bg-primary/5 p-5">
					<div class="flex items-center justify-between">
						<span class="flex items-center gap-2 text-lg font-semibold text-foreground">
							<DollarSign class="h-5 w-5 text-primary" />
							Estimated Total
						</span>
						<span class="text-2xl font-bold text-primary">
							${totalCost.toFixed(0)}
							{#if tripPlan.currency && tripPlan.currency !== 'USD'}
								<span class="text-sm font-normal text-muted-foreground">{tripPlan.currency}</span>
							{/if}
						</span>
					</div>
					<div class="mt-3 h-2.5 overflow-hidden rounded-full bg-muted">
						<div
							class="h-full rounded-full bg-primary transition-all"
							style="width: {Math.min((totalCost / (durationDays * (budget === 'Budget' ? 100 : budget === 'Mid-range' ? 250 : 500))) * 100, 100)}%"
						></div>
					</div>
					<p class="mt-1.5 text-xs text-muted-foreground">
						~${(totalCost / durationDays).toFixed(0)} per day
					</p>
				</div>
			</div>
		{/if}

	{:else}
		<!-- Search Tab -->
		<form
			class="mb-6 flex gap-3"
			onsubmit={(e) => { e.preventDefault(); handleSearch(); }}
		>
			<div class="relative flex-1">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search destinations... e.g. 'beaches in Southeast Asia'"
					class="w-full rounded-md border bg-card py-2.5 pl-10 pr-4 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20"
				/>
			</div>
			<button
				type="submit"
				disabled={searching || !searchQuery.trim()}
				class="flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{#if searching}
					<Loader2 class="h-4 w-4 animate-spin" />
				{:else}
					<Search class="h-4 w-4" />
				{/if}
				Search
			</button>
		</form>

		{#if searchError}
			<div class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
				{searchError}
			</div>
		{/if}

		{#if destinations.length}
			<div class="grid gap-4 sm:grid-cols-2">
				{#each destinations as dest}
					<DestinationCard destination={dest} onselect={selectDestination} />
				{/each}
			</div>
		{:else if !searching && searchQuery}
			<div class="py-12 text-center text-muted-foreground">
				<Compass class="mx-auto mb-3 h-10 w-10 opacity-40" />
				<p>No destinations found. Try a different search.</p>
			</div>
		{:else if !searching}
			<div class="py-12 text-center text-muted-foreground">
				<MapPin class="mx-auto mb-3 h-10 w-10 opacity-40" />
				<p>Search for destinations to explore</p>
			</div>
		{/if}
	{/if}
</div>
