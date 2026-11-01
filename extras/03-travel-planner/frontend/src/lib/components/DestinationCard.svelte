<script lang="ts">
	import { MapPin, DollarSign, Sun } from 'lucide-svelte';
	import type { Destination } from '$lib/api';

	let { destination, onselect }: { destination: Destination; onselect?: (d: Destination) => void } =
		$props();
</script>

<button
	class="w-full cursor-pointer rounded-lg border bg-card p-5 text-left shadow-sm transition-all hover:border-primary/40 hover:shadow-md"
	onclick={() => onselect?.(destination)}
>
	<div class="mb-2 flex items-start justify-between">
		<div>
			<h3 class="flex items-center gap-1.5 text-lg font-semibold text-foreground">
				<MapPin class="h-4 w-4 text-primary" />
				{destination.city}
			</h3>
			<p class="text-sm text-muted-foreground">{destination.country}</p>
		</div>
		{#if destination.budget_range}
			<span class="flex items-center gap-1 rounded-full bg-accent/15 px-2.5 py-1 text-xs font-medium text-accent">
				<DollarSign class="h-3 w-3" />
				{destination.budget_range}
			</span>
		{/if}
	</div>

	<p class="mb-3 text-sm text-muted-foreground">{destination.description}</p>

	{#if destination.best_seasons?.length}
		<div class="flex flex-wrap gap-1.5">
			{#each destination.best_seasons as season}
				<span class="flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
					<Sun class="h-3 w-3" />
					{season}
				</span>
			{/each}
		</div>
	{/if}
</button>
